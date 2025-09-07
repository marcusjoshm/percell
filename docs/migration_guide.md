## Optimal File-by-File Replacement Strategy

### 1. **Create a Migration Order Based on Dependencies**

Start with the least dependent files and work your way up:

```python
# migration_order.md
## Phase 1: Pure Utilities (No dependencies)
1. core/utils.py → Split into domain services
2. core/paths.py → domain/services/file_naming_service.py

## Phase 2: Domain Logic (Minimal dependencies)
3. modules/measure_roi_area.py → domain/services/analysis_aggregation_service.py
4. modules/resize_rois.py → domain/services/segmentation_strategy_service.py
5. modules/group_cells.py → domain/services/intensity_analysis_service.py

## Phase 3: Integration Logic (External dependencies)
6. modules/bin_images.py → adapters/pil_image_processing_adapter.py
7. modules/create_cell_masks.py → adapters/imagej_macro_adapter.py
8. modules/extract_cells.py → adapters/cellpose_subprocess_adapter.py

## Phase 4: Orchestration (Depends on everything)
9. modules/stage_classes.py → application/step_execution_coordinator.py
10. core/pipeline.py → application/workflow_coordinator.py
11. core/cli.py → ports/driving/user_interface_port.py
```

### 2. **Create a Test Harness for Each File**

Before migrating each file, create a test that captures its current behavior:

```python
# tests/migration/test_[filename]_migration.py
import pytest
from pathlib import Path
import importlib
import sys

class TestMigration:
    @pytest.fixture
    def old_module(self):
        """Load the old module."""
        # Temporarily add old module to path
        sys.path.insert(0, 'percell/modules')
        old = importlib.import_module('bin_images')
        sys.path.pop(0)
        return old
    
    @pytest.fixture
    def new_module(self):
        """Load the new implementation."""
        from percell.adapters import PILImageProcessingAdapter
        from percell.domain.services import SegmentationStrategyService
        return PILImageProcessingAdapter(), SegmentationStrategyService()
    
    def test_binning_functionality_preserved(self, old_module, new_module):
        """Ensure new implementation matches old behavior."""
        test_image = create_test_image()
        
        # Old way
        old_result = old_module.bin_image(test_image, factor=2)
        
        # New way
        adapter, service = new_module
        strategy = service.calculate_binning_strategy(test_image, factor=2)
        new_result = adapter.apply_binning(test_image, strategy)
        
        assert_images_equal(old_result, new_result)
```

### 3. **Prompt Template for Cursor AI Agent**

Create specific prompts for each file migration:

```markdown
# Cursor AI Migration Prompt Template

## Task: Migrate [modules/bin_images.py]

### Current File Location:
`percell/modules/bin_images.py`

### Migration Targets:
- Business logic → `domain/services/segmentation_strategy_service.py`
- Image I/O → `adapters/pil_image_processing_adapter.py`
- File operations → `adapters/local_filesystem_adapter.py`

### Architecture Rules:
1. Domain services CANNOT import from adapters or infrastructure
2. Domain services should only use domain models from `domain/models.py`
3. Adapters implement ports from `ports/driven/`
4. No framework-specific code in domain layer
5. Keep ImageJ/Cellpose subprocess calls in adapters only

### Specific Instructions:
1. Extract the binning algorithm calculation to SegmentationStrategyService
2. Move PIL Image operations to PILImageProcessingAdapter
3. Create a temporary wrapper in the old location that calls new services
4. Ensure all existing function signatures remain unchanged
5. Add type hints to all new methods
6. Write docstrings explaining what was migrated from where

### Testing Requirements:
After migration, these tests must pass:
- `pytest tests/migration/test_bin_images_migration.py`
- `pytest tests/integration/test_binning_workflow.py`

### Do NOT:
- Delete the old file yet (we'll do that after verification)
- Change any public API signatures
- Mix concerns between services
```

### 4. **Incremental Migration Script**

Create a script to manage the migration process:

```python
# tools/migrate_file.py
#!/usr/bin/env python3
"""
Manage file-by-file migration with testing.
Usage: python tools/migrate_file.py modules/bin_images.py
"""

import subprocess
import sys
import shutil
from pathlib import Path
from datetime import datetime

class FileMigrator:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.backup_dir = Path('.migration_backups')
        self.backup_dir.mkdir(exist_ok=True)
        
    def backup_current_state(self):
        """Backup current working state before migration."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{self.file_path.stem}_{timestamp}.py"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy(self.file_path, backup_path)
        print(f"✓ Backed up to {backup_path}")
        return backup_path
        
    def run_tests(self):
        """Run tests to verify migration."""
        test_file = f"tests/migration/test_{self.file_path.stem}_migration.py"
        
        # Run specific migration test
        result = subprocess.run(
            f"pytest {test_file} -v",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"✗ Tests failed for {self.file_path.name}")
            print(result.stdout)
            return False
            
        print(f"✓ Migration tests passed")
        
        # Run full test suite
        result = subprocess.run(
            "pytest tests/ -x",  # Stop on first failure
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"✗ Full test suite failed")
            print(result.stdout)
            return False
            
        print(f"✓ Full test suite passed")
        return True
        
    def create_migration_wrapper(self):
        """Create temporary wrapper in old location."""
        wrapper_content = f'''"""
Temporary wrapper for {self.file_path.name}
This file maintains backward compatibility during migration.
TODO: Remove after full migration is complete.
"""

# Import from new locations
from percell.domain.services import (
    SegmentationStrategyService,
    FileNamingService
)
from percell.adapters import PILImageProcessingAdapter

# Initialize services (consider dependency injection later)
_segmentation_service = SegmentationStrategyService()
_image_adapter = PILImageProcessingAdapter()
_naming_service = FileNamingService()

# Preserve old function signatures
def bin_images(*args, **kwargs):
    """Wrapper for backward compatibility."""
    # Delegate to new architecture
    return _image_adapter.bin_images(*args, **kwargs)

# Add other wrapped functions as needed
'''
        
        # Write wrapper
        wrapper_path = self.file_path.with_suffix('.wrapper.py')
        wrapper_path.write_text(wrapper_content)
        print(f"✓ Created wrapper at {wrapper_path}")
        
    def migrate(self):
        """Execute the migration process."""
        print(f"\n{'='*50}")
        print(f"Migrating: {self.file_path}")
        print(f"{'='*50}\n")
        
        # Step 1: Backup
        backup_path = self.backup_current_state()
        
        # Step 2: Run pre-migration tests
        print("\nRunning pre-migration tests...")
        if not self.run_tests():
            print("⚠ Pre-migration tests failed - review before proceeding")
            
        # Step 3: AI migration happens here
        print("\n>>> Run Cursor AI migration now <<<")
        print(f">>> Use prompt from: prompts/{self.file_path.stem}_prompt.md <<<")
        input("\nPress Enter after Cursor completes the migration...")
        
        # Step 4: Run post-migration tests
        print("\nRunning post-migration tests...")
        if not self.run_tests():
            print(f"\n✗ Migration failed - restoring from {backup_path}")
            shutil.copy(backup_path, self.file_path)
            return False
            
        # Step 5: Create wrapper for compatibility
        self.create_migration_wrapper()
        
        print(f"\n✓ Successfully migrated {self.file_path.name}")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/migrate_file.py <file_path>")
        sys.exit(1)
        
    migrator = FileMigrator(sys.argv[1])
    success = migrator.migrate()
    sys.exit(0 if success else 1)
```

### 5. **Git Workflow for Each File**

```bash
# For each file migration:

# 1. Create feature branch
git checkout -b migrate/bin_images

# 2. Run migration script
python tools/migrate_file.py modules/bin_images.py

# 3. Let Cursor AI do the migration
# ... Cursor works here ...

# 4. Verify tests pass (handled by script)

# 5. Commit with clear message
git add -A
git commit -m "refactor: Migrate bin_images.py to hexagonal architecture

- Moved binning logic to SegmentationStrategyService
- Moved image I/O to PILImageProcessingAdapter  
- Created backward compatibility wrapper
- All tests passing"

# 6. Push and create PR
git push origin migrate/bin_images

# 7. After review, merge and move to next file
```

### 6. **Validation Checklist for Cursor**

Give Cursor this checklist for each file:

```markdown
## Migration Validation Checklist

Before considering migration complete:

- [ ] All business logic moved to appropriate domain service
- [ ] All I/O operations moved to appropriate adapter
- [ ] All external tool calls moved to adapters
- [ ] Type hints added to all new methods
- [ ] Docstrings indicate source of migrated code
- [ ] No circular dependencies introduced
- [ ] Domain layer has no framework dependencies
- [ ] Original tests still pass
- [ ] New unit tests created for services
- [ ] Backward compatibility wrapper created
- [ ] No code duplication between old and new
```

### 7. **Testing Strategy During Migration**

```python
# Create a test that verifies both old and new work
# tests/migration/compatibility_test.py

def test_parallel_execution():
    """Ensure old and new implementations work in parallel."""
    
    # Old way
    from percell.modules import bin_images as old_way
    
    # New way  
    from percell.domain.services import SegmentationStrategyService
    from percell.adapters import PILImageProcessingAdapter
    
    # Both should work
    test_data = create_test_data()
    
    old_result = old_way.process(test_data)
    
    service = SegmentationStrategyService()
    adapter = PILImageProcessingAdapter()
    new_result = adapter.process(test_data, service.calculate_strategy(test_data))
    
    assert results_equivalent(old_result, new_result)
```

## Benefits of This Approach

1. **Clear rollback points** - Each backup allows easy reversion
2. **Continuous validation** - Tests run after each file
3. **AI-friendly** - Clear, focused tasks for Cursor
4. **Maintains working code** - App never breaks during migration
5. **Traceable progress** - Git history shows exact migration path

## Suggested Migration Schedule

```markdown
## Week 1: Utilities and Pure Functions
- Monday: core/utils.py
- Tuesday: core/paths.py  
- Wednesday: modules/measure_roi_area.py
- Thursday: modules/resize_rois.py
- Friday: Test and stabilize

## Week 2: Domain Services
- Monday: modules/group_cells.py
- Tuesday: modules/bin_images.py
- Wednesday: modules/create_cell_masks.py
- Thursday: modules/extract_cells.py
- Friday: Integration testing

## Week 3: Orchestration Layer
- Monday-Tuesday: modules/stage_classes.py
- Wednesday-Thursday: core/pipeline.py
- Friday: core/cli.py

## Week 4: Cleanup
- Remove backward compatibility wrappers
- Delete old files
- Update documentation
- Final testing
```

This approach gives you a systematic, testable, and reversible migration path that works perfectly with AI assistance. Each file becomes a clear, bounded task that Cursor can handle effectively.