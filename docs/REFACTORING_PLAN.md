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

## Immediate Actionable Steps

1. **Extract Configuration Management**: Move all config-related code to a single, well-defined service
2. **Create Plugin Interfaces**: Define standard interfaces for analysis operations
3. **Separate CLI from Core**: Move CLI logic to its own layer that orchestrates core services
4. **Implement Factory Pattern**: For creating analysis stages/plugins dynamically
5. **Add Integration Tests**: To ensure refactoring doesn't break existing functionality

## Long-term Benefits

This refactoring will:
- Make adding new analysis types as simple as implementing a plugin interface
- Enable testing individual components in isolation
- Allow for different front-ends (CLI, GUI, API) using the same core
- Support configuration-driven pipeline assembly
- Enable parallel execution of independent stages

The key insight is moving from a "everything imports everything" model to a "dependency injection with clear boundaries" model. This will dramatically reduce the cognitive load when adding new features.