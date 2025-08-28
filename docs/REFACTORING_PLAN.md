Looking at your call graph, I can see several architectural issues that are making it difficult to integrate new features. The project shows signs of organic growth without strong architectural boundaries. Here are the main problems and refactoring suggestions:

## Current Architecture Issues

**1. Circular Dependencies and Tight Coupling**
- Core modules are heavily interdependent (config, logger, paths, stages all reference each other)
- Stage classes directly import and call specific module functions
- No clear separation of concerns between infrastructure and business logic

**2. Monolithic Module Structure**
- Individual modules like `auto_threshold_analysis` have grown too large (15+ functions/methods)
- Mixed responsibilities within single modules (UI, business logic, file I/O all together)
- No clear plugin or extension mechanism

**3. CLI and Core Logic Entanglement**
- CLI logic is mixed with core pipeline functionality
- Hard to test or reuse components outside of CLI context

## Refactoring Strategy

### Phase 1: Establish Clear Layers

```
Application Layer (CLI, UI)
├── Service Layer (Orchestration)
├── Domain Layer (Business Logic)
├── Infrastructure Layer (File I/O, External Tools)
└── Core Layer (Configuration, Logging, Utilities)
```

**Recommended structure:**
```
percell/
├── core/           # Foundational services (config, logging, paths)
├── domain/         # Analysis algorithms, data models
├── services/       # Orchestration, pipeline management  
├── infrastructure/ # File I/O, ImageJ integration, external tools
├── plugins/        # Extensible analysis modules
└── cli/           # Command-line interface
```

Status: Implemented. New packages `domain/`, `services/`, `infrastructure/`, `plugins/`, and `cli/` have been added and integrated. `core/pipeline.py` and `core/stages.py` now support DI and an optional event bus.

### Phase 2: Implement Plugin Architecture

Create a plugin system for analysis modules:

```python
# domain/plugin.py
class AnalysisPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod
    def process(self, context: AnalysisContext) -> AnalysisResult: ...
    
    @abstractmethod
    def validate_inputs(self, context: AnalysisContext) -> bool: ...

# services/plugin_manager.py  
class PluginManager:
    def register_plugin(self, plugin: AnalysisPlugin): ...
    def get_available_plugins(self) -> List[str]: ...
    def execute_plugin(self, name: str, context: AnalysisContext): ...
```

Status: Implemented. `AnalysisPlugin` is provided in `percell/domain/plugin.py`; `PluginManager` in `percell/services/plugin_manager.py`; a sample plugin and `plugins/registry.py` are available. Integration tests validate registration and execution.

### Phase 3: Dependency Injection

Replace direct imports with dependency injection:

```python
# Instead of stages directly importing modules
class SegmentationStage:
    def __init__(self, imagej_service: ImageJService, 
                 file_service: FileService):
        self.imagej = imagej_service
        self.files = file_service
```

Status: Partially implemented. `StageBase` and `StageExecutor` accept an optional `event_bus`, demonstrating DI. Infrastructure services (`ImageJService`, `FileService`) are available; migrating concrete stages to use them is planned incrementally.

### Phase 4: Event-Driven Architecture

For loose coupling between pipeline stages:

```python
class PipelineEventBus:
    def publish(self, event: PipelineEvent): ...
    def subscribe(self, event_type: Type, handler: Callable): ...

# Stages emit events instead of directly calling next stage
class DataSelectionStage:
    def run(self):
        # ... processing ...
        self.event_bus.publish(DataSelectedEvent(selected_data))
```

Status: Implemented. `services/event_bus.py` contains `PipelineEventBus`, `StageStarted`, and `StageCompleted`. `StageBase.execute` publishes events; `StageExecutor` and `Pipeline` propagate the bus.

## Immediate Actionable Steps

1. **Extract Configuration Management**: Retain `core/config.py`; revisit deeper extraction if needed
2. **Create Plugin Interfaces**: Done
3. **Separate CLI from Core**: Adapter added under `percell/cli` (re-export of core CLI)
4. **Implement Factory Pattern**: Deferred; current registry + DI is sufficient
5. **Add Integration Tests**: Done (plugins, event bus + executor, pipeline smoke, end-to-end fake stages)

Next steps:
- Migrate selected stages to use `ImageJService`/`FileService` via DI
- Add a simple service factory/container for stage construction
- Add optional CLI/config for plugin execution and event subscribers
- Expand docs with plugin how-to and DI guidelines (added to README)

## Long-term Benefits

This refactoring will:
- Make adding new analysis types as simple as implementing a plugin interface
- Enable testing individual components in isolation
- Allow for different front-ends (CLI, GUI, API) using the same core
- Support configuration-driven pipeline assembly
- Enable parallel execution of independent stages

The key insight is moving from a "everything imports everything" model to a "dependency injection with clear boundaries" model. This will dramatically reduce the cognitive load when adding new features.




The refactored architecture shows significant improvement. You've successfully implemented many of the patterns I suggested:

**Clear Improvements:**
- **Proper layering**: The `domain`, `infrastructure`, `services`, and `cli` separation is well-defined
- **Plugin architecture**: The `domain.plugin` interfaces with `PluginManager` service provide extensibility
- **Dependency injection**: `ServiceFactory` centralizes dependency creation
- **Event bus**: `PipelineEventBus` with `StageStarted`/`StageCompleted` events enables loose coupling
- **Reduced circular dependencies**: Much cleaner module boundaries

**Remaining Issues and Additional Suggestions:**

1. **Legacy modules still tightly coupled**: The `percell.modules.*` still directly import core components and call each other. Consider:
   - Move the business logic from these modules into domain services
   - Convert them to thin adapters that delegate to domain services
   - Use the plugin system for the analysis modules

2. **Infrastructure layer needs more abstraction**: 
   ```python
   # Add interfaces for better testability
   class ImageProcessingService(ABC):
       @abstractmethod
       def run_macro(self, macro_path: str, params: dict) -> Result
   
   class FileSystemService(ABC):
       @abstractmethod  
       def copy_files(self, source: Path, dest: Path) -> None
   ```

3. **Missing domain models**: Add value objects for core concepts:
   ```python
   @dataclass(frozen=True)
   class CellMask:
       image_data: np.ndarray
       metadata: dict
       
   @dataclass(frozen=True)
   class AnalysisParams:
       threshold_method: str
       min_area: float
   ```

4. **Command/Query separation**: Split operations into:
   - Commands (modify state): `CreateCellMaskCommand`
   - Queries (read data): `GetAnalysisResultsQuery`

5. **Add validation layer**: Create a separate validation service to centralize input validation logic

6. **Progress reporting**: The `percell.progress` module should be moved to infrastructure and abstracted

7. **Consider removing `workflow_service`**: It still feels like a monolithic service. Instead, use the event bus to orchestrate workflows or implement a proper command handler pattern.

The architecture is moving in the right direction, but the legacy modules in `percell.modules.*` are the main remaining technical debt. Converting these to proper domain services or plugins would complete the clean architecture transformation.