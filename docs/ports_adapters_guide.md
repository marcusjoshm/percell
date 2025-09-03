# Ports and Adapters Architecture Guide for Percell Refactoring

## Part 1: Understanding Ports and Adapters (Hexagonal Architecture)

### Core Concepts

**Ports and Adapters Architecture** (also known as Hexagonal Architecture) is a design pattern that isolates the core business logic from external concerns. Think of it as creating a protected "core" that doesn't know or care about the outside world.

### Key Components

1. **Domain/Core (The Hexagon Center)**
   - Contains pure business logic
   - Has no dependencies on external systems
   - Defines the rules and workflows of your application
   - In your case: workflow orchestration logic, cell analysis algorithms

2. **Ports (Interfaces/Contracts)**
   - Define HOW the core communicates with the outside world
   - Act as gatekeepers/contracts
   - Come in two types:
     - **Inbound/Primary Ports**: Ways to trigger core logic (APIs, CLIs, GUIs)
     - **Outbound/Secondary Ports**: Ways for core to request external services (databases, file systems, external tools)

3. **Adapters (Implementations)**
   - Implement the port interfaces
   - Handle the actual communication with external systems
   - Transform data between external format and domain format
   - Types:
     - **Inbound/Primary Adapters**: REST controllers, CLI handlers, GUI controllers
     - **Outbound/Secondary Adapters**: File system access, Cellpose integration, ImageJ integration

### Visual Representation

```
        [CLI Adapter] ──> [Workflow Port]
                              │
    [GUI Adapter] ────> [Data Selection Port]     ╔═══════════════╗
                              │                    ║               ║
                              ▼                    ║  DOMAIN CORE  ║
                         ┌─────────┐              ║               ║
                         │         │ ◀────────────║   Workflows   ║
    [Config Adapter] ──> │  PORTS  │              ║   Analysis    ║
                         │         │ ◀────────────║   Processing  ║
                         └─────────┘              ║               ║
                              ▲                    ╚═══════════════╝
                              │                           │
    [FileSystem Adapter] ◀────┴──── [Storage Port]      │
                                                         │
    [Cellpose Adapter] ◀──────────── [Segmentation Port]│
                                                         │
    [ImageJ Adapter] ◀────────────── [ImageProcessing Port]
```

## Part 2: Percell-Specific Architecture Design

### Proposed Domain Structure

```
percell/
├── domain/                      # Core business logic
│   ├── entities/
│   │   ├── cell.py             # Cell entity
│   │   ├── roi.py              # ROI entity
│   │   ├── image.py            # Image entity
│   │   ├── workflow.py         # Workflow entity
│   │   └── metadata.py         # Metadata entity
│   ├── value_objects/
│   │   ├── file_path.py        # File path value object
│   │   ├── intensity.py        # Pixel intensity value
│   │   └── dimensions.py       # Image dimensions
│   ├── services/
│   │   ├── workflow_orchestrator.py
│   │   ├── cell_analyzer.py
│   │   ├── roi_processor.py
│   │   └── threshold_calculator.py
│   └── exceptions/
│       └── domain_exceptions.py
│
├── application/                 # Application services (use cases)
│   ├── use_cases/
│   │   ├── run_complete_workflow.py
│   │   ├── select_data.py
│   │   ├── segment_cells.py
│   │   ├── process_cells.py
│   │   ├── threshold_cells.py
│   │   └── analyze_results.py
│   └── dto/                    # Data Transfer Objects
│       ├── workflow_request.py
│       └── analysis_result.py
│
├── ports/                       # Port interfaces
│   ├── inbound/
│   │   ├── workflow_port.py
│   │   ├── data_selection_port.py
│   │   └── analysis_port.py
│   └── outbound/
│       ├── storage_port.py
│       ├── segmentation_port.py
│       ├── image_processing_port.py
│       ├── metadata_port.py
│       └── plugin_port.py
│
├── adapters/                    # Adapter implementations
│   ├── inbound/
│   │   ├── cli/
│   │   │   ├── cli_adapter.py
│   │   │   └── menu_system.py
│   │   └── api/
│   │       └── rest_adapter.py (future)
│   └── outbound/
│       ├── storage/
│       │   ├── file_system_adapter.py
│       │   └── path_manager.py
│       ├── segmentation/
│       │   ├── cellpose_adapter.py
│       │   └── cellpose_wrapper.py
│       ├── image_processing/
│       │   ├── imagej_adapter.py
│       │   └── macro_executor.py
│       ├── metadata/
│       │   ├── metadata_adapter.py
│       │   └── filename_parser.py
│       └── plugins/
│           ├── plugin_manager.py
│           └── plugin_loader.py
│
├── infrastructure/              # Infrastructure concerns
│   ├── config/
│   │   ├── config_manager.py
│   │   └── settings.py
│   ├── logging/
│   │   └── logger.py
│   └── dependencies/
│       └── container.py        # Dependency injection
│
└── main.py                      # Application entry point
```

### Detailed Port and Adapter Specifications

#### 1. **Metadata Management System**

**Port Interface:**
```python
# ports/outbound/metadata_port.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from domain.entities.metadata import Metadata

class MetadataPort(ABC):
    @abstractmethod
    def extract_metadata(self, file_path: str) -> Metadata:
        pass
    
    @abstractmethod
    def query_metadata(self, filters: Dict) -> List[Metadata]:
        pass
    
    @abstractmethod
    def generate_naming_convention(self, metadata: Metadata) -> str:
        pass
```

**Adapter Implementation:**
```python
# adapters/outbound/metadata/metadata_adapter.py
class FileNameMetadataAdapter(MetadataPort):
    def extract_metadata(self, file_path: str) -> Metadata:
        # Parse condition, timepoint, region, channel from path
        pass
```

#### 2. **Storage Management System**

**Port Interface:**
```python
# ports/outbound/storage_port.py
class StoragePort(ABC):
    @abstractmethod
    def create_directory(self, path: str) -> None:
        pass
    
    @abstractmethod
    def list_files(self, pattern: str) -> List[str]:
        pass
    
    @abstractmethod
    def read_image(self, path: str) -> np.ndarray:
        pass
    
    @abstractmethod
    def write_image(self, data: np.ndarray, path: str) -> None:
        pass
    
    @abstractmethod
    def cleanup_temp_files(self) -> None:
        pass
```

#### 3. **Segmentation System**

**Port Interface:**
```python
# ports/outbound/segmentation_port.py
class SegmentationPort(ABC):
    @abstractmethod
    def segment_cells(self, image: np.ndarray, parameters: Dict) -> List[ROI]:
        pass
    
    @abstractmethod
    def validate_segmentation(self, rois: List[ROI]) -> bool:
        pass
```

**Adapter:**
```python
# adapters/outbound/segmentation/cellpose_adapter.py
class CellposeAdapter(SegmentationPort):
    def __init__(self, cellpose_path: str):
        self.cellpose_path = cellpose_path
        
    def segment_cells(self, image: np.ndarray, parameters: Dict) -> List[ROI]:
        # Launch Cellpose, process image, return ROIs
        pass
```

#### 4. **Image Processing System**

**Port Interface:**
```python
# ports/outbound/image_processing_port.py
class ImageProcessingPort(ABC):
    @abstractmethod
    def execute_macro(self, macro_name: str, params: Dict) -> Any:
        pass
    
    @abstractmethod
    def resize_rois(self, rois: List[ROI], scale: float) -> List[ROI]:
        pass
    
    @abstractmethod
    def interactive_threshold(self, image: np.ndarray) -> np.ndarray:
        pass
```

#### 5. **Workflow Orchestration System**

**Domain Service:**
```python
# domain/services/workflow_orchestrator.py
class WorkflowOrchestrator:
    def __init__(self, 
                 storage: StoragePort,
                 segmentation: SegmentationPort,
                 image_processing: ImageProcessingPort,
                 metadata: MetadataPort):
        self.storage = storage
        self.segmentation = segmentation
        self.image_processing = image_processing
        self.metadata = metadata
    
    def execute_workflow(self, workflow_definition: WorkflowDefinition):
        # Orchestrate steps based on workflow definition
        pass
```

#### 6. **Plugin Management System**

**Port Interface:**
```python
# ports/outbound/plugin_port.py
class PluginPort(ABC):
    @abstractmethod
    def discover_plugins(self) -> List[Plugin]:
        pass
    
    @abstractmethod
    def load_plugin(self, plugin_id: str) -> Any:
        pass
    
    @abstractmethod
    def register_plugin(self, plugin: Plugin) -> None:
        pass
```

### Dependency Injection Setup

```python
# infrastructure/dependencies/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()
    
    # Adapters
    storage_adapter = providers.Singleton(
        FileSystemAdapter,
        base_path=config.storage.base_path
    )
    
    cellpose_adapter = providers.Singleton(
        CellposeAdapter,
        cellpose_path=config.cellpose.path
    )
    
    imagej_adapter = providers.Singleton(
        ImageJAdapter,
        imagej_path=config.imagej.path
    )
    
    metadata_adapter = providers.Singleton(
        FileNameMetadataAdapter
    )
    
    # Domain Services
    workflow_orchestrator = providers.Factory(
        WorkflowOrchestrator,
        storage=storage_adapter,
        segmentation=cellpose_adapter,
        image_processing=imagej_adapter,
        metadata=metadata_adapter
    )
    
    # Application Services
    run_workflow_use_case = providers.Factory(
        RunCompleteWorkflow,
        orchestrator=workflow_orchestrator
    )
```

### Benefits of This Architecture for Percell

1. **Easy Tool Swapping**: Replace Cellpose with another segmentation tool by creating a new adapter
2. **Plugin Support**: Add new analysis methods as plugins without modifying core
3. **Testing**: Mock adapters for unit testing without external dependencies
4. **Multiple Interfaces**: Add GUI or REST API without changing business logic
5. **Workflow Flexibility**: Define custom workflows using the same building blocks
6. **Clear Separation**: Business logic is isolated from technical details

### Migration Strategy

#### Phase 1: Setup Structure (Week 1)
1. Create directory structure
2. Set up dependency injection
3. Create base port interfaces

#### Phase 2: Extract Domain (Week 2-3)
1. Identify and extract entities
2. Move business logic to domain services
3. Create value objects for type safety

#### Phase 3: Implement Adapters (Week 3-4)
1. Create storage adapter (file system operations)
2. Create Cellpose adapter
3. Create ImageJ adapter
4. Create metadata adapter

#### Phase 4: Build Application Layer (Week 5)
1. Implement use cases
2. Wire up dependency injection
3. Create CLI adapter

#### Phase 5: Testing & Refinement (Week 6)
1. Add unit tests for domain
2. Add integration tests for adapters
3. Refactor based on testing insights

### Example Workflow Execution

```python
# main.py
def main():
    # Setup DI container
    container = Container()
    container.config.from_yaml('config/settings.yaml')
    
    # Get use case from container
    workflow_runner = container.run_workflow_use_case()
    
    # Define workflow
    workflow = WorkflowDefinition(
        name="standard_analysis",
        steps=[
            SelectDataStep(),
            SegmentationStep(tool="cellpose"),
            ProcessCellsStep(),
            ThresholdStep(),
            AnalysisStep()
        ]
    )
    
    # Execute
    result = workflow_runner.execute(
        workflow=workflow,
        input_dir="/path/to/data",
        output_dir="/path/to/output"
    )
```

### Key Design Decisions

1. **Separate Metadata from Storage**: Metadata operations are independent of file operations
2. **Plugin System**: Extensibility through a dedicated plugin port
3. **Workflow as First-Class Entity**: Workflows are domain objects that can be composed
4. **Tool Agnostic Core**: The domain doesn't know about Cellpose or ImageJ
5. **Event-Driven Options**: Can add event bus for loose coupling between components

This architecture will make your Percell project:
- More maintainable
- Easier to test
- More extensible
- Tool-agnostic
- Ready for future enhancements (GUI, REST API, new analysis tools)

I'll help you understand ports and adapters architecture and design a refactoring plan for your percell project. Let me first examine your codebase to better understand the current structure.Let me look at the actual code structure to better understand the current architecture:Let me search for the repository structure differently:Based on my examination of your percell project and my understanding of your requirements, I'll explain ports and adapters architecture and provide you with a comprehensive refactoring plan.I've created a comprehensive guide for refactoring your Percell project to a Ports and Adapters architecture. Let me break down the key points:

## 1. How Ports and Adapters Works

The architecture separates your application into three layers:

- **Core/Domain**: Your business logic that doesn't depend on external systems
- **Ports**: Interfaces that define contracts for communication
- **Adapters**: Implementations that handle actual external interactions

Think of it like this: Your core workflow logic shouldn't care whether you're using Cellpose or another segmentation tool - it just needs "something that segments cells." The port defines what "segmenting cells" means, and the adapter handles the specific Cellpose implementation.

## 2. Specific Design for Percell

Based on your project, I've identified these key components:

### Core Services (Domain Layer)
- **WorkflowOrchestrator**: Manages workflow execution order
- **CellAnalyzer**: Core analysis algorithms  
- **ROIProcessor**: ROI manipulation logic
- **ThresholdCalculator**: Thresholding logic

### Port Categories

**Inbound Ports** (How users interact):
- WorkflowPort (for CLI/GUI to trigger workflows)
- DataSelectionPort (for file selection interface)
- AnalysisPort (for analysis requests)

**Outbound Ports** (How core uses external tools):
- StoragePort (file system operations)
- SegmentationPort (Cellpose or alternatives)
- ImageProcessingPort (ImageJ or alternatives)
- MetadataPort (filename parsing and metadata)
- PluginPort (plugin management)

### Adapters

Each port gets concrete implementations:
- **CellposeAdapter**: Wraps Cellpose functionality
- **ImageJAdapter**: Wraps ImageJ macro execution
- **FileSystemAdapter**: Handles all file I/O
- **MetadataAdapter**: Parses filenames for metadata
- **PluginManager**: Loads and manages plugins

## Key Benefits for Your Project

1. **Tool Independence**: Swap Cellpose for another tool by writing a new adapter
2. **Plugin System**: Add features without touching core logic
3. **Testing**: Test business logic without running Cellpose/ImageJ
4. **Multiple UIs**: Add a web interface later without changing the core

## Migration Approach

Start with these steps:

1. **Create the structure** without moving code yet
2. **Extract interfaces** for your current functionality
3. **Wrap external tools** (Cellpose, ImageJ) in adapters
4. **Move business logic** to the domain layer
5. **Wire everything** with dependency injection

The architecture I've designed specifically addresses your needs:
- Metadata is a separate component that other parts can use
- File management is centralized through the StoragePort
- Each external tool (Cellpose, ImageJ) has its own adapter
- Workflows are first-class entities that can be composed
- Plugins can be added through the PluginPort

Would you like me to help you start implementing specific parts of this architecture, or would you like more detail on any particular component?