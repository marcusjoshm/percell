# Hexagonal Architecture Implementation Plan

## Overview

This document outlines the plan to refactor the Percell project to implement clean hexagonal architecture, addressing the issues identified in `REFACTORING_SUGGESTIONS_2025-08-29.md`.

## Current State Analysis

### Issues Identified

1. **Module Dependencies are Inverted**: `percell.modules` directly imports from `percell.core`
2. **Core Layer is Doing Too Much**: Infrastructure concerns mixed with application logic
3. **Direct Infrastructure Access**: Components bypass ports to access infrastructure
4. **CLI Mixed with Core Logic**: Business logic embedded in CLI layer
5. **Missing Clear Boundaries**: No clear separation between layers

### Current Architecture

```
percell/
├── core/           # Mixed concerns (infrastructure + application)
├── modules/        # Direct dependencies on core
├── domain/         # Minimal domain layer
├── infrastructure/ # Underdeveloped
├── services/       # Underdeveloped
└── cli/           # Mixed with business logic
```

## Target Architecture

```
percell/
├── domain/
│   ├── models/          # Business entities and value objects
│   ├── ports/           # All interfaces (contracts)
│   ├── exceptions/      # Domain exceptions
│   └── services/        # Domain services
├── application/
│   ├── services/        # Use case implementations (refactored from modules)
│   ├── workflows/       # Pipeline orchestration
│   └── commands/        # Command/Query handlers
├── infrastructure/
│   ├── adapters/        # Port implementations
│   ├── progress/        # Progress reporting
│   ├── logging/         # Logging implementation
│   ├── configuration/   # Config management
│   └── imagej/          # ImageJ integration
├── adapters/
│   ├── cli/            # Thin CLI adapters
│   └── web/            # Future web adapters
└── main/
    └── composition_root.py  # Dependency injection
```

## Implementation Phases

### Phase 1: Foundation (✅ COMPLETED)

**Status**: ✅ **COMPLETED**

- [x] Created comprehensive domain ports (`percell/domain/ports.py`)
- [x] Created domain exceptions (`percell/domain/exceptions.py`)
- [x] Created application layer structure
- [x] Created infrastructure adapters structure
- [x] Created composition root (`percell/main/composition_root.py`)
- [x] Created example refactored service (`CreateCellMasksService`)
- [x] Created example CLI adapter (`CreateCellMasksCLI`)

**Key Achievements**:
- Established clean domain boundaries with comprehensive ports
- Implemented dependency injection pattern
- Created example of proper hexagonal architecture implementation

### Phase 2: Infrastructure Layer (🔄 IN PROGRESS)

**Status**: 🔄 **IN PROGRESS**

#### 2.1 Move Infrastructure Concerns from Core

- [ ] Move `core/progress.py` → `infrastructure/progress/`
- [ ] Move `core/logger.py` → `infrastructure/logging/`
- [ ] Move `core/config.py` → `infrastructure/configuration/`
- [ ] Move `core/paths.py` → `infrastructure/filesystem/`

#### 2.2 Create Infrastructure Adapters

- [x] `SubprocessAdapter` (✅ COMPLETED)
- [x] `FileSystemAdapter` (✅ COMPLETED)
- [ ] `ConfigurationAdapter`
- [ ] `LoggingAdapter`
- [ ] `ImageJAdapter`
- [ ] `StageRegistryAdapter`

#### 2.3 Update Progress Reporter

- [ ] Refactor `infrastructure/progress_reporter.py` to implement `ProgressReporter` port
- [ ] Remove direct dependencies on `alive-progress`
- [ ] Create progress port interface

### Phase 3: Application Layer (📋 PLANNED)

**Status**: 📋 **PLANNED**

#### 3.1 Refactor Modules to Application Services

Priority order based on usage and complexity:

1. **High Priority**:
   - [ ] `create_cell_masks.py` → `CreateCellMasksService` (✅ COMPLETED)
   - [ ] `extract_cells.py` → `ExtractCellsService`
   - [ ] `analyze_cell_masks.py` → `AnalyzeCellMasksService`
   - [ ] `measure_roi_area.py` → `MeasureROIAreaService`

2. **Medium Priority**:
   - [ ] `group_cells.py` → `GroupCellsService`
   - [ ] `combine_masks.py` → `CombineMasksService`
   - [ ] `cleanup_directories.py` → `CleanupDirectoriesService`
   - [ ] `resize_rois.py` → `ResizeROIsService`

3. **Low Priority**:
   - [ ] `bin_images.py` → `BinImagesService`
   - [ ] `directory_setup.py` → `DirectorySetupService`
   - [ ] `set_directories.py` → `SetDirectoriesService`

#### 3.2 Create Application Workflows

- [ ] `PipelineWorkflow` - Main pipeline orchestration
- [ ] `AdvancedWorkflow` - Advanced analysis workflow
- [ ] `ValidationWorkflow` - Input validation workflow

#### 3.3 Create Command/Query Handlers

- [ ] `CreateCellMasksCommand`
- [ ] `ExtractCellsCommand`
- [ ] `AnalyzeCellMasksCommand`
- [ ] `GetAnalysisResultsQuery`

### Phase 4: Adapter Layer (📋 PLANNED)

**Status**: 📋 **PLANNED**

#### 4.1 Refactor CLI

- [x] `CreateCellMasksCLI` (✅ COMPLETED)
- [ ] `ExtractCellsCLI`
- [ ] `AnalyzeCellMasksCLI`
- [ ] `PipelineCLI` - Main CLI orchestrator
- [ ] Remove business logic from existing CLI

#### 4.2 Create Web Adapters (Future)

- [ ] REST API adapters
- [ ] Web UI adapters
- [ ] GraphQL adapters

### Phase 5: Cleanup and Migration (📋 PLANNED)

**Status**: 📋 **PLANNED**

#### 5.1 Remove Core Package Dependencies

- [ ] Update all imports throughout codebase
- [ ] Remove `from percell.core` imports
- [ ] Ensure clean dependency flow: Adapters → Application → Domain

#### 5.2 Update Tests

- [ ] Refactor tests to use composition root
- [ ] Create unit tests for application services
- [ ] Create integration tests for adapters
- [ ] Update existing tests to use new architecture

#### 5.3 Documentation

- [ ] Update API documentation
- [ ] Create architecture documentation
- [ ] Update user guides
- [ ] Create developer guides

## Implementation Guidelines

### Dependency Rules

1. **Domain Layer**: No dependencies on other layers
2. **Application Layer**: Only depends on domain layer
3. **Infrastructure Layer**: Implements domain ports
4. **Adapter Layer**: Depends on application layer through composition root

### Service Creation Pattern

```python
class ExampleService:
    def __init__(
        self,
        subprocess_port: SubprocessPort,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort
    ):
        self.subprocess_port = subprocess_port
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.logger = logging_port.get_logger("ExampleService")
    
    def execute_use_case(self, **kwargs) -> bool:
        # Use case implementation
        pass
```

### CLI Adapter Pattern

```python
class ExampleCLI:
    def __init__(self):
        self.composition_root = get_composition_root()
        self.service = self.composition_root.get_service('example_service')
    
    def run(self, args) -> int:
        # Validate input
        # Delegate to service
        # Handle errors
        pass
```

## Migration Strategy

### Incremental Migration

1. **Parallel Implementation**: New services alongside existing modules
2. **Feature Flags**: Use configuration to switch between old/new implementations
3. **Gradual Replacement**: Replace modules one by one
4. **Backward Compatibility**: Maintain existing APIs during transition

### Testing Strategy

1. **Unit Tests**: Test application services in isolation
2. **Integration Tests**: Test adapters with real infrastructure
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Ensure no performance regression

## Success Metrics

### Architecture Quality

- [ ] Zero circular dependencies
- [ ] Clean dependency flow (inward only)
- [ ] Domain layer has no external dependencies
- [ ] All business logic in application layer

### Code Quality

- [ ] Reduced coupling between components
- [ ] Improved testability
- [ ] Clear separation of concerns
- [ ] Consistent error handling

### Maintainability

- [ ] Easier to add new features
- [ ] Easier to modify existing features
- [ ] Easier to test components
- [ ] Clearer code organization

## Risk Mitigation

### Technical Risks

1. **Breaking Changes**: Use feature flags and gradual migration
2. **Performance Impact**: Monitor and optimize as needed
3. **Complexity Increase**: Keep implementations simple and focused

### Project Risks

1. **Timeline**: Phase implementation allows for incremental delivery
2. **Resources**: Focus on high-impact changes first
3. **Knowledge Transfer**: Document patterns and examples

## Next Steps

### Immediate Actions (Next 2 weeks)

1. **Complete Phase 2**: Finish infrastructure layer refactoring
2. **Create More Services**: Implement 2-3 more application services
3. **Update Tests**: Create tests for new architecture
4. **Documentation**: Update architecture documentation

### Medium Term (Next 2 months)

1. **Complete Phase 3**: Finish application layer refactoring
2. **Complete Phase 4**: Finish adapter layer refactoring
3. **Migration**: Replace old modules with new services
4. **Performance Testing**: Ensure no regression

### Long Term (Next 6 months)

1. **Complete Phase 5**: Full cleanup and optimization
2. **Advanced Features**: Add new capabilities using clean architecture
3. **Web Interface**: Implement web adapters
4. **Community**: Share architecture patterns and lessons learned

## Conclusion

This refactoring plan provides a clear path to implementing clean hexagonal architecture while maintaining system functionality and improving maintainability. The incremental approach minimizes risk while delivering value at each phase.

The foundation work completed in Phase 1 demonstrates the viability of the approach and provides a template for the remaining work.
