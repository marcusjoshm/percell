# Cursor Agent Prompt for Percell Refactoring

## Context and Objective

You are tasked with refactoring the Percell microscopy pipeline project from a monolithic architecture to a clean Ports and Adapters (Hexagonal) architecture. You have been provided with two comprehensive documents:

1. **inventory_report.md** - A complete analysis of the current codebase
2. **refactoring_guide.md** - Detailed instructions for the refactoring
3. **layer_assignments.md** - Specific assignments of components to architectural layers

Your goal is to systematically refactor the codebase following these documents while maintaining backward compatibility and committing changes incrementally.

## Instructions for Cursor Agent

### Initial Setup

1. **Create a new git branch for the refactoring:**
```bash
git checkout -b refactor/ports-and-adapters
git commit --allow-empty -m "refactor: initialize ports and adapters architecture migration"
```

2. **Read and analyze the provided documents:**
- First, read `inventory_report.md` to understand the current codebase structure
- Then read `refactoring_guide.md` for the refactoring strategy
- Finally, read `layer_assignments.md` for specific component placements

### Phase 1: Foundation (Commits 1-5)

**Commit 1: Create domain structure**
```bash
# Create the new directory structure
mkdir -p percell/domain/{entities,value_objects,services}
mkdir -p percell/application/{use_cases,commands}
mkdir -p percell/ports/{inbound,outbound}
mkdir -p percell/adapters/{inbound,outbound}
mkdir -p percell/infrastructure/{config,bootstrap,utils}

# Create __init__.py files for all new directories
# Commit with message: "refactor: create ports and adapters directory structure"
```

**Commit 2: Extract value objects**
- Create value objects in `percell/domain/value_objects/` based on layer_assignments.md Section 1
- Start with `experiment.py`, `processing.py`, and `imaging.py`
- Include proper type hints and make them immutable using `@dataclass(frozen=True)`
- Write unit tests in `tests/domain/value_objects/`
- Commit: `"refactor: add domain value objects for experiment and processing"`

**Commit 3: Define port interfaces**
- Create port interfaces in `percell/ports/outbound/` from layer_assignments.md Section 3
- Start with critical ports: `ImageReaderPort`, `ImageWriterPort`, `MacroRunnerPort`
- Use ABC (Abstract Base Class) for all ports
- Include comprehensive docstrings
- Commit: `"refactor: define core port interfaces"`

**Commit 4: Extract first domain service**
- Extract `ROITrackingService` from `track_rois.py` as specified in layer_assignments.md
- Move ONLY pure logic (no I/O) to `percell/domain/services/roi_tracking_service.py`
- Write comprehensive unit tests with no external dependencies
- Commit: `"refactor: extract ROI tracking domain service"`

**Commit 5: Extract cell grouping service**
- Extract pure logic from `group_cells.py` to `percell/domain/services/cell_grouping_service.py`
- Include `compute_auc()`, clustering logic, aggregation rules
- Write unit tests using numpy arrays (no file I/O)
- Commit: `"refactor: extract cell grouping domain service"`

### Phase 2: Adapters (Commits 6-10)

**Commit 6: Implement image adapters**
- Create `TifffileImageAdapter` in `percell/adapters/outbound/tifffile_image_adapter.py`
- Implement both `ImageReaderPort` and `ImageWriterPort`
- Write integration tests that use temporary files
- Commit: `"refactor: implement tifffile image adapter"`

**Commit 7: Implement macro runner adapter**
- Create `ImageJMacroAdapter` in `percell/adapters/outbound/imagej_macro_adapter.py`
- Wrap existing subprocess and macro logic
- Mock subprocess calls in unit tests
- Commit: `"refactor: implement ImageJ macro adapter"`

**Commit 8: Implement metadata adapter**
- Create `PandasMetadataAdapter` for CSV operations
- Extract from `analyze_cell_masks.py` and `include_group_metadata.py`
- Write tests with fixture data
- Commit: `"refactor: implement pandas metadata adapter"`

**Commit 9: Implement filesystem adapter**
- Create `PathlibFilesystemAdapter` for all Path/glob operations
- Include methods for directory creation, file listing, deletion
- Write tests using temp directories
- Commit: `"refactor: implement filesystem adapter"`

**Commit 10: Create adapter factory**
- Create adapter factory in `percell/adapters/factory.py`
- Allow configuration-based adapter selection
- Commit: `"refactor: add adapter factory for dependency injection"`

### Phase 3: Application Services (Commits 11-15)

**Commit 11: Create first use case**
- Create `GroupCellsUseCase` in `percell/application/use_cases/group_cells.py`
- Inject domain service and port dependencies
- Orchestrate the workflow using injected dependencies
- Write tests with mocked dependencies
- Commit: `"refactor: implement group cells use case"`

**Commit 12: Create ROI tracking use case**
- Create `TrackROIsUseCase` using the domain service and ports
- Remove all direct file I/O from the use case
- Test with mocks
- Commit: `"refactor: implement track ROIs use case"`

**Commit 13: Create segmentation use case**
- Extract orchestration logic from `SegmentationStage`
- Create clean use case with injected dependencies
- Commit: `"refactor: implement segmentation use case"`

**Commit 14: Refactor stage classes**
- Modify `stage_classes.py` to use new use cases
- Keep backward compatibility with thin adapters
- Commit: `"refactor: update stage classes to use application services"`

**Commit 15: Create command objects**
- Extract command patterns from current argument handling
- Create command objects for each use case
- Commit: `"refactor: add command objects for use cases"`

### Phase 4: Dependency Injection (Commits 16-18)

**Commit 16: Setup DI container**
- Create `Container` in `percell/infrastructure/bootstrap/container.py`
- Wire all services, adapters, and use cases
- Use dependency-injector or similar library
- Commit: `"refactor: add dependency injection container"`

**Commit 17: Integrate container with main**
- Update `main.py` to use the container
- Maintain backward compatibility
- Commit: `"refactor: integrate DI container with main application"`

**Commit 18: Add configuration management**
- Move configuration to infrastructure layer
- Create configuration port and adapter
- Commit: `"refactor: migrate configuration to infrastructure layer"`

### Phase 5: Testing and Migration (Commits 19-25)

**Commit 19: Add comprehensive domain tests**
- Test all domain services with pure unit tests
- Achieve 100% coverage of domain logic
- Commit: `"test: add comprehensive domain service tests"`

**Commit 20: Add use case tests**
- Test all use cases with mocked dependencies
- Verify orchestration logic
- Commit: `"test: add application use case tests"`

**Commit 21: Add integration tests**
- Create end-to-end tests for critical workflows
- Use test fixtures and temporary files
- Commit: `"test: add integration tests for main workflows"`

**Commit 22: Create migration shims**
- Add backward compatibility layers
- Ensure old CLI commands still work
- Commit: `"refactor: add backward compatibility shims"`

**Commit 23: Update documentation**
- Update README with new architecture
- Add architecture diagrams
- Document how to extend the system
- Commit: `"docs: update documentation for new architecture"`

**Commit 24: Performance optimization**
- Profile the refactored code
- Optimize any performance regressions
- Commit: `"perf: optimize refactored components"`

**Commit 25: Final cleanup**
- Remove deprecated code paths (if safe)
- Clean up imports and dependencies
- Commit: `"refactor: final cleanup and deprecation removal"`

## Working Principles

### For Each Refactoring Session:

1. **Read the specification first** - Before changing any code, read the relevant section from the provided documents
2. **Write tests before refactoring** - Create tests for the new structure before moving code
3. **Maintain backward compatibility** - Never break existing functionality
4. **Commit frequently** - Make atomic commits with clear messages
5. **Run tests after each commit** - Ensure `pytest` passes before committing

### Code Quality Guidelines:

1. **Type hints everywhere** - Add comprehensive type hints to all new code
2. **Docstrings for public APIs** - Document all public methods and classes
3. **No business logic in adapters** - Adapters only translate between ports and external systems
4. **No I/O in domain** - Domain layer must be pure with no external dependencies
5. **Dependency injection** - All dependencies should be injected, not instantiated

### Testing Strategy:

```python
# Domain tests - pure, no mocks needed
def test_compute_auc():
    service = CellGroupingService()
    result = service.compute_auc(np.array([1, 2, 3, 2, 1]))
    assert result == 9.0

# Use case tests - mock all dependencies
def test_group_cells_use_case():
    mock_service = Mock()
    mock_reader = Mock()
    use_case = GroupCellsUseCase(mock_service, mock_reader)
    # Test orchestration logic

# Integration tests - use real adapters with temp files
def test_group_cells_end_to_end(tmp_path):
    container = Container()
    use_case = container.group_cells_use_case()
    # Test with real files in tmp_path
```

### Git Commit Message Format:

```
<type>: <subject>

<body>

<footer>
```

Types:
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `docs:` - Documentation changes
- `perf:` - Performance improvements
- `fix:` - Bug fixes during refactoring

### Progress Tracking:

After each commit, update a `REFACTORING_PROGRESS.md` file with:
- [x] Completed tasks
- [ ] Remaining tasks
- Current phase status
- Any blockers or decisions needed

## Critical Success Criteria:

1. **All existing tests must pass** - Never break existing functionality
2. **Domain layer has zero external dependencies** - Pure business logic only
3. **Each commit is atomic and complete** - Code should work after every commit
4. **New architecture is properly tested** - Minimum 80% test coverage
5. **Performance is maintained or improved** - No significant performance degradation

## Start Instructions:

1. First, confirm you've read all three documents (inventory_report.md, refactoring_guide.md, layer_assignments.md)
2. Create the git branch as specified
3. Start with Phase 1, Commit 1
4. After each commit, run tests and confirm everything works
5. Ask for clarification if any specification is unclear
6. Provide a brief status update after every 5 commits

Begin the refactoring process now, starting with creating the new directory structure and committing it as specified in Phase 1, Commit 1.