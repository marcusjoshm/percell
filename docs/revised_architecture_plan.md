# Revised Hexagonal Architecture Plan for PerCell

Based on the actual business workflow description, here's a more accurate architectural design:

## **Core Business Domain (Hexagon Center)**

### **True Business Logic Services**

#### 1. **DataSelectionService** 
**Business Purpose:** File selection and channel configuration
**Core Logic:**
- Parse microscopy file naming conventions
- Extract conditions, timepoints, regions, channels
- Validate user selections for consistency
- Generate file lists for processing

#### 2. **WorkflowOrchestrationService**
**Business Purpose:** Coordinate the 5-step analysis workflow
**Core Logic:**
- Validate workflow steps and dependencies
- Manage workflow state and progress
- Handle workflow customization rules
- Coordinate step execution order

#### 3. **CellSegmentationService** 
**Business Purpose:** Single cell segmentation business rules
**Core Logic:**
- Image binning calculations for speed optimization
- Segmentation parameter validation
- ROI resizing calculations
- Multi-channel ROI duplication logic

#### 4. **IntensityAnalysisService**
**Business Purpose:** Cell intensity analysis and grouping
**Core Logic:**
- Cell intensity measurement algorithms
- Brightness-based grouping algorithms
- Thresholding parameter calculations
- Binary mask analysis rules

#### 5. **FileNamingService**
**Business Purpose:** Consistent file naming across workflow
**Core Logic:**
- Naming convention rules and validation
- File type suffix management
- Directory structure rules
- Name parsing and generation

#### 6. **AnalysisAggregationService**
**Business Purpose:** Combine analysis results
**Core Logic:**
- Results combination algorithms
- CSV generation rules
- Data validation logic
- Analysis completeness checks

## **Ports (Interfaces)**

### **Driving Ports (User Interactions)**

#### 1. **UserInterfacePort**
```python
class UserInterfacePort(Protocol):
    def show_main_menu(self) -> MenuSelection
    def show_data_selection_interface(self, available_data: DataCatalog) -> DataSelection
    def prompt_for_directories(self) -> DirectoryConfiguration
    def show_workflow_options(self) -> WorkflowChoice
    def display_progress(self, step: str, progress: float) -> None
```

#### 2. **WorkflowExecutionPort** 
```python
class WorkflowExecutionPort(Protocol):
    def execute_main_workflow(self, config: WorkflowConfig) -> WorkflowResult
    def execute_custom_workflow(self, steps: List[WorkflowStep]) -> WorkflowResult
    def execute_single_step(self, step: WorkflowStep, context: StepContext) -> StepResult
```

### **Driven Ports (External Tool Integrations)**

#### 1. **CellposeIntegrationPort**
```python
class CellposeIntegrationPort(Protocol):
    def launch_cellpose_gui(self, input_files: List[Path]) -> CellposeResult
    def validate_cellpose_output(self, output_dir: Path) -> ValidationResult
    def extract_roi_files(self, cellpose_output: Path) -> List[Path]
```

#### 2. **ImageJIntegrationPort**
```python
class ImageJIntegrationPort(Protocol):
    def execute_macro(self, macro: MacroScript, params: MacroParams) -> MacroResult
    def launch_interactive_thresholding(self, grouped_images: List[Path]) -> ThresholdingResult
    def batch_analyze_masks(self, mask_files: List[Path]) -> AnalysisResult
```

#### 3. **FileManagementPort**
```python
class FileManagementPort(Protocol):
    def scan_input_directory(self, directory: Path) -> FileCatalog
    def create_output_structure(self, base_dir: Path, structure: DirectoryStructure) -> None
    def copy_and_rename_files(self, file_operations: List[FileOperation]) -> None
    def organize_results(self, results: AnalysisResults, output_dir: Path) -> None
```

#### 4. **ImageProcessingPort**
```python
class ImageProcessingPort(Protocol):
    def bin_images(self, images: List[Path], factor: int) -> List[Path]
    def resize_rois(self, rois: List[ROI], scale_factor: float) -> List[ROI]
    def extract_cells(self, image: Path, rois: List[ROI]) -> List[Path]
    def group_cells_by_intensity(self, cell_images: List[Path]) -> Dict[str, List[Path]]
```

## **Adapters (Implementations)**

### **Driving Adapters**

#### 1. **ClickCLIAdapter** 
**Implements:** UserInterfacePort
**Purpose:** Interactive command-line interface
**Current Code:** `percell/core/cli.py`

#### 2. **MainApplicationAdapter**
**Implements:** WorkflowExecutionPort  
**Purpose:** Main application entry and workflow execution
**Current Code:** `percell/main/main.py`

### **Driven Adapters**

#### 1. **CellposeSubprocessAdapter**
**Implements:** CellposeIntegrationPort
**Purpose:** Launch and manage Cellpose via subprocess
**Dependencies:** subprocess, cellpose installation

#### 2. **ImageJMacroAdapter** 
**Implements:** ImageJIntegrationPort
**Purpose:** Execute ImageJ macros and interactive operations
**Dependencies:** ImageJ/Fiji installation, macro files
**Current Code:** Scattered throughout modules

#### 3. **LocalFileSystemAdapter**
**Implements:** FileManagementPort
**Purpose:** Local file operations and organization
**Dependencies:** pathlib, shutil, os

#### 4. **PILImageProcessingAdapter**
**Implements:** ImageProcessingPort  
**Purpose:** Image processing operations
**Dependencies:** PIL, numpy, tifffile

## **Application Layer (Orchestration)**

### **ApplicationServices** (Between Ports and Domain)

#### 1. **WorkflowCoordinator**
**Purpose:** Coordinate domain services for complete workflows
**Dependencies:** All domain services + ports

#### 2. **StepExecutionCoordinator** 
**Purpose:** Execute individual workflow steps
**Dependencies:** Relevant domain services + ports

#### 3. **ConfigurationManager**
**Purpose:** Handle configuration loading and validation
**Dependencies:** FileManagementPort + domain validation

## **Revised Migration Plan**

### **Phase 1: Extract Core Business Logic (40-50 hours)**

#### Step 1.1: File Naming and Parsing Logic
**Files:** Parts of multiple modules that handle file naming
**Extract to:** FileNamingService
**Risk:** Low
**Hours:** 8-10

#### Step 1.2: Data Selection Logic  
**Files:** CLI data selection code
**Extract to:** DataSelectionService
**Risk:** Low  
**Hours:** 10-12

#### Step 1.3: Intensity Analysis Logic
**Files:** Cell grouping and analysis code
**Extract to:** IntensityAnalysisService  
**Risk:** Medium
**Hours:** 12-15

#### Step 1.4: Workflow Orchestration Logic
**Files:** Pipeline and workflow coordination
**Extract to:** WorkflowOrchestrationService
**Risk:** Medium
**Hours:** 10-13

### **Phase 2: Create External Tool Adapters (50-60 hours)**

#### Step 2.1: ImageJ Integration Adapter
**Current:** Scattered macro execution code
**Create:** ImageJMacroAdapter
**Risk:** High (complex external integration)
**Hours:** 20-25

#### Step 2.2: Cellpose Integration Adapter  
**Current:** Cellpose launch code
**Create:** CellposeSubprocessAdapter
**Risk:** Medium
**Hours:** 12-15

#### Step 2.3: File System Adapter
**Current:** File operations throughout codebase
**Create:** LocalFileSystemAdapter  
**Risk:** Low
**Hours:** 10-12

#### Step 2.4: Image Processing Adapter
**Current:** PIL/image processing code
**Create:** PILImageProcessingAdapter
**Risk:** Low
**Hours:** 8-8

### **Phase 3: Create Application Coordination (30-40 hours)**

#### Step 3.1: Application Services
**Create:** WorkflowCoordinator, StepExecutionCoordinator
**Risk:** Medium
**Hours:** 15-20

#### Step 3.2: Port Interfaces
**Create:** All port interfaces with proper abstractions
**Risk:** Low
**Hours:** 10-12

#### Step 3.3: Integration and Testing
**Purpose:** Wire everything together and test
**Risk:** High
**Hours:** 15-20

## **Total Effort: 120-150 hours**

## **Key Benefits of This Architecture**

### **1. External Tool Isolation**
- Cellpose integration isolated in adapter
- ImageJ macros isolated in adapter  
- Can mock for testing without external dependencies

### **2. Business Logic Clarity**
- File naming logic centralized
- Workflow orchestration clearly defined
- Analysis algorithms isolated and testable

### **3. Flexibility**
- Can swap Cellpose for other segmentation tools
- Can add new analysis algorithms easily
- Can change file formats without touching business logic

### **4. Testability**
- Core business logic testable in isolation
- Can mock external tools for unit testing
- Integration tests can focus on adapters

## **Critical Success Factors**

### **1. Preserve External Tool Integration**
- ImageJ macros must work identically
- Cellpose integration must be seamless
- User experience must remain the same

### **2. Maintain File Naming Consistency**
- FileNamingService must handle all current conventions
- Backward compatibility with existing files
- Clear naming rules for new file types

### **3. Workflow Flexibility**
- Custom workflows must remain possible
- Individual step execution must work
- Progress tracking must be maintained

This architecture properly separates the true business logic (file analysis, naming conventions, workflow rules) from external tool integration (Cellpose, ImageJ) and infrastructure concerns (file I/O, CLI interface).