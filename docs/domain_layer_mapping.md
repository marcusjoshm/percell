# Domain Layer Mapping for Percell Modules

Based on your project's workflow orchestration for single-cell microscopy analysis, here's how your current modules should be organized in the domain layer:

## Domain Layer Organization

### 🔷 **Entities** (Core Business Objects)
These represent the main concepts in your domain that have identity and lifecycle:

#### Recommended Entities:
```python
# domain/entities/cell.py
class Cell:
    """Represents a single cell with its properties"""
    def __init__(self, cell_id: str, roi: ROI, intensity_values: Dict):
        self.id = cell_id
        self.roi = roi
        self.intensity_values = intensity_values
        self.group_id: Optional[str] = None
        self.threshold_mask: Optional[np.ndarray] = None
        self.area: Optional[float] = None
        self.metadata: Dict = {}

# domain/entities/roi.py
class ROI:
    """Region of Interest representing cell boundaries"""
    def __init__(self, coordinates: List[Tuple], image_dimensions: Dimensions):
        self.coordinates = coordinates
        self.image_dimensions = image_dimensions
        self.scaled_coordinates: Optional[List[Tuple]] = None
        
# domain/entities/workflow.py
class Workflow:
    """Represents a complete analysis workflow"""
    def __init__(self, workflow_id: str, name: str):
        self.id = workflow_id
        self.name = name
        self.steps: List[WorkflowStep] = []
        self.status: WorkflowStatus = WorkflowStatus.PENDING
        
# domain/entities/image_dataset.py
class ImageDataset:
    """Represents a collection of related images"""
    def __init__(self, condition: str, timepoint: Optional[str], region: str):
        self.condition = condition
        self.timepoint = timepoint
        self.region = region
        self.channels: Dict[str, Image] = {}
        
# domain/entities/analysis_result.py
class AnalysisResult:
    """Represents the output of an analysis"""
    def __init__(self, dataset: ImageDataset):
        self.dataset = dataset
        self.cells: List[Cell] = []
        self.statistics: Dict = {}
        self.timestamp = datetime.now()
```

### 🔶 **Value Objects** (Immutable Data Holders)
These are objects that are defined by their attributes rather than identity:

#### Recommended Value Objects:
```python
# domain/value_objects/file_path.py
@dataclass(frozen=True)
class FilePath:
    """Immutable file path with validation"""
    path: str
    
    def __post_init__(self):
        if " " in self.path:
            raise ValueError("File paths cannot contain spaces")
        if not os.path.exists(self.path):
            raise ValueError(f"Path does not exist: {self.path}")

# domain/value_objects/pixel_intensity.py
@dataclass(frozen=True)
class PixelIntensity:
    """Represents pixel intensity with bounds checking"""
    value: float
    channel: str
    
    def __post_init__(self):
        if not 0 <= self.value <= 65535:  # 16-bit image max
            raise ValueError(f"Invalid intensity value: {self.value}")

# domain/value_objects/dimensions.py
@dataclass(frozen=True)
class Dimensions:
    """Image dimensions"""
    width: int
    height: int
    depth: Optional[int] = None
    
# domain/value_objects/metadata.py
@dataclass(frozen=True)
class ExperimentMetadata:
    """Metadata extracted from file naming convention"""
    condition: str
    timepoint: Optional[str]
    region: str
    channel: str
    
# domain/value_objects/threshold_params.py
@dataclass(frozen=True)
class ThresholdParameters:
    """Parameters for thresholding operations"""
    method: str  # 'otsu', 'manual', 'adaptive'
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
```

### 🔵 **Domain Services** (Core Business Logic)
These contain the business logic that doesn't naturally fit in entities:

#### Recommended Services:

```python
# domain/services/workflow_orchestrator.py
class WorkflowOrchestrator:
    """Orchestrates the execution of analysis workflows"""
    def execute_workflow(self, workflow: Workflow, dataset: ImageDataset) -> AnalysisResult
    def validate_workflow(self, workflow: Workflow) -> bool
    def get_next_step(self, workflow: Workflow) -> Optional[WorkflowStep]

# domain/services/cell_analyzer.py
class CellAnalyzer:
    """Core cell analysis algorithms"""
    def calculate_intensity_statistics(self, cell: Cell, image: np.ndarray) -> Dict
    def group_cells_by_intensity(self, cells: List[Cell], num_groups: int) -> Dict[int, List[Cell]]
    def measure_cell_area(self, cell: Cell) -> float
    def calculate_colocalization(self, cell: Cell, channel1: np.ndarray, channel2: np.ndarray) -> float

# domain/services/roi_processor.py
class ROIProcessor:
    """ROI manipulation and processing"""
    def resize_roi(self, roi: ROI, scale_factor: float) -> ROI
    def track_rois_across_timepoints(self, rois_t1: List[ROI], rois_t2: List[ROI]) -> Dict
    def duplicate_roi_for_channels(self, roi: ROI, channels: List[str]) -> Dict[str, ROI]
    def validate_roi(self, roi: ROI, image_dimensions: Dimensions) -> bool

# domain/services/threshold_calculator.py
class ThresholdCalculator:
    """Thresholding algorithms"""
    def calculate_otsu_threshold(self, image: np.ndarray) -> float
    def apply_threshold(self, image: np.ndarray, params: ThresholdParameters) -> np.ndarray
    def generate_binary_mask(self, image: np.ndarray, threshold: float) -> np.ndarray
    
# domain/services/metadata_extractor.py
class MetadataExtractor:
    """Extract and process metadata from file structures"""
    def extract_from_path(self, path: FilePath) -> ExperimentMetadata
    def build_hierarchy(self, paths: List[FilePath]) -> Dict
    def generate_output_path(self, metadata: ExperimentMetadata, base_dir: str) -> str
```

## Module Migration Mapping

Based on typical module names in microscopy analysis software, here's where your existing modules should go:

### Modules that belong in **Domain Services**:
- `data_analysis.py` → `domain/services/cell_analyzer.py`
- `process_cells.py` → `domain/services/roi_processor.py`
- `threshold_cells.py` → `domain/services/threshold_calculator.py`
- `workflow_orchestration.py` → `domain/services/workflow_orchestrator.py`
- `metadata_extraction.py` → `domain/services/metadata_extractor.py`
- `cell_tracking.py` → `domain/services/roi_processor.py` (merge with ROI processing)
- `intensity_grouping.py` → `domain/services/cell_analyzer.py` (part of analysis)

### Modules that belong in **Adapters** (NOT domain):
- `cellpose_wrapper.py` → `adapters/outbound/segmentation/cellpose_adapter.py`
- `imagej_macros.py` → `adapters/outbound/image_processing/imagej_adapter.py`
- `file_operations.py` → `adapters/outbound/storage/file_system_adapter.py`
- `config_manager.py` → `infrastructure/config/config_manager.py`
- `cli_interface.py` → `adapters/inbound/cli/cli_adapter.py`
- `data_selection.py` → `adapters/inbound/cli/data_selection_adapter.py`

### Modules that belong in **Application Layer** (Use Cases):
- `run_workflow.py` → `application/use_cases/run_complete_workflow.py`
- `segment_cells.py` → `application/use_cases/segment_cells.py`
- `analyze_results.py` → `application/use_cases/analyze_results.py`

## Key Principles for Domain Layer

### ✅ **What BELONGS in Domain:**
1. **Business rules**: Cell grouping algorithms, intensity calculations
2. **Core algorithms**: Thresholding methods, ROI tracking logic
3. **Workflow logic**: Step ordering, validation rules
4. **Domain-specific calculations**: Cell area, colocalization metrics
5. **Data transformations**: ROI resizing, coordinate transformations

### ❌ **What DOES NOT belong in Domain:**
1. **External tool integration**: Cellpose, ImageJ
2. **File I/O**: Reading/writing images, creating directories
3. **UI logic**: Menu systems, user prompts
4. **Configuration**: Reading config files, environment variables
5. **Infrastructure**: Logging, database connections

## Example Refactoring

### Before (Mixed Concerns):
```python
# modules/process_cells.py - MIXED CONCERNS
import cv2
from cellpose import models
import os

def process_cells(input_dir, output_dir):
    # File I/O - should be in adapter
    os.makedirs(output_dir, exist_ok=True)
    
    # External tool - should be in adapter
    model = models.Cellpose(gpu=True, model_type='cyto')
    
    # Business logic - belongs in domain
    for cell in cells:
        area = calculate_area(cell)
        intensity = measure_intensity(cell)
        
    # File I/O again - should be in adapter
    cv2.imwrite(f"{output_dir}/result.tif", result)
```

### After (Separated Concerns):
```python
# domain/services/cell_analyzer.py - PURE DOMAIN
class CellAnalyzer:
    def process_cells(self, cells: List[Cell]) -> List[Cell]:
        # Pure business logic only
        processed_cells = []
        for cell in cells:
            cell.area = self.calculate_area(cell)
            cell.intensity = self.measure_intensity(cell)
            processed_cells.append(cell)
        return processed_cells
    
    def calculate_area(self, cell: Cell) -> float:
        # Pure calculation
        return len(cell.roi.coordinates)
    
    def measure_intensity(self, cell: Cell) -> float:
        # Pure algorithm
        return sum(cell.intensity_values.values()) / len(cell.intensity_values)

# adapters/outbound/segmentation/cellpose_adapter.py - ADAPTER
class CellposeAdapter(SegmentationPort):
    def segment(self, image: np.ndarray) -> List[ROI]:
        # External tool interaction
        model = models.Cellpose(gpu=True, model_type='cyto')
        masks = model.eval(image)
        return self.convert_masks_to_rois(masks)

# application/use_cases/process_cells.py - USE CASE
class ProcessCellsUseCase:
    def __init__(self, analyzer: CellAnalyzer, storage: StoragePort, segmentation: SegmentationPort):
        self.analyzer = analyzer
        self.storage = storage
        self.segmentation = segmentation
    
    def execute(self, input_path: str, output_path: str):
        # Orchestrate the workflow
        image = self.storage.read_image(input_path)
        rois = self.segmentation.segment(image)
        cells = [Cell(roi=roi) for roi in rois]
        processed = self.analyzer.process_cells(cells)
        self.storage.save_results(processed, output_path)
```

## Migration Priority

1. **High Priority** (Core business logic):
   - `workflow_orchestrator.py`
   - `cell_analyzer.py`
   - `roi_processor.py`
   - `threshold_calculator.py`

2. **Medium Priority** (Supporting logic):
   - `metadata_extractor.py`
   - Entity classes (Cell, ROI, Workflow)
   - Value objects

3. **Low Priority** (Can be done later):
   - Additional analysis algorithms
   - Optimization functions
   - Utility calculations

This organization ensures your domain layer contains only pure business logic, making it testable, maintainable, and independent of external dependencies.

Let me examine the modules in your percell repository to understand the current code structure and determine what belongs in the domain layer.Let me fetch the actual repository content to see the modules directory:I can see the repository structure from the README, but I need to look at the actual code modules. Let me search for more specific information about the modules directory:Let me create a comprehensive analysis based on typical module patterns I can infer from the repository structure and your description. Based on your project description and typical patterns in microscopy analysis software, here's my analysis of which modules should be moved to the domain layer:I've created a comprehensive guide for organizing your Percell modules into the proper domain layer structure. Here are the key takeaways:

## Domain Layer Organization

### **Entities** (Your core business objects):
- **Cell**: Represents individual cells with their properties
- **ROI**: Region of interest for cell boundaries  
- **Workflow**: Complete analysis workflow definition
- **ImageDataset**: Collection of related microscopy images
- **AnalysisResult**: Output from analysis runs

### **Value Objects** (Immutable data):
- **FilePath**: Validated file paths without spaces
- **PixelIntensity**: Intensity values with bounds checking
- **Dimensions**: Image width/height/depth
- **ExperimentMetadata**: Parsed file naming metadata
- **ThresholdParameters**: Thresholding configuration

### **Domain Services** (Core algorithms):
- **WorkflowOrchestrator**: Manages workflow execution
- **CellAnalyzer**: Intensity calculations, grouping, area measurements
- **ROIProcessor**: ROI resizing, tracking, duplication
- **ThresholdCalculator**: Otsu and other thresholding algorithms
- **MetadataExtractor**: File path parsing and metadata extraction

## Key Migration Rules

### ✅ **Move TO Domain Layer**:
- Cell grouping algorithms
- Intensity calculations  
- ROI tracking logic
- Thresholding methods
- Workflow validation
- Area/colocalization measurements

### ❌ **Keep OUT of Domain Layer**:
- Cellpose integration → Goes to Adapters
- ImageJ macro execution → Goes to Adapters
- File I/O operations → Goes to Adapters
- CLI menus/prompts → Goes to Adapters
- Config file reading → Goes to Infrastructure

The main principle is: **Domain code should be pure business logic with no external dependencies**. This makes it:
- Easy to unit test (no mocking Cellpose/ImageJ)
- Portable (can swap tools without changing core logic)
- Maintainable (business rules in one place)

Would you like me to help you start implementing specific domain entities or services, or would you prefer guidance on refactoring a particular module first?