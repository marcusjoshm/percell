# Domain Layer Review and Recommendations for Percell Refactor

## Critical Domain Layer Assessment Points

### 🔴 **Common Issues to Check in Your Domain Layer**

#### 1. **External Dependencies Leak**
Check if your domain layer has any of these (they should NOT be there):
```python
# ❌ WRONG - Domain should not know about external tools
from cellpose import models  # External dependency
import cv2  # External library
import imagej  # External tool
from pathlib import Path  # File system operations
import json  # Serialization concerns
import yaml  # Configuration concerns
```

#### 2. **Infrastructure Concerns**
Look for and remove:
```python
# ❌ WRONG - Domain should not handle infrastructure
class Cell:
    def save_to_disk(self, path):  # File I/O
    def load_from_config(self, config_path):  # Config reading
    def log_error(self, message):  # Logging
    def connect_to_database(self):  # Database
```

#### 3. **UI/Presentation Logic**
Remove any user interaction from domain:
```python
# ❌ WRONG - Domain should not handle UI
class WorkflowOrchestrator:
    def prompt_user_for_input(self):  # User interaction
    def display_progress_bar(self):  # UI concern
    def format_for_display(self):  # Presentation logic
```

### ✅ **What MUST Be in Your Domain Layer**

#### 1. **Core Entities**
```python
# domain/entities/cell.py
from dataclasses import dataclass
from typing import Optional, Dict, List
from domain.value_objects import ROICoordinates, PixelIntensity

@dataclass
class Cell:
    """Core cell entity with business logic"""
    id: str
    roi: 'ROI'
    channel_intensities: Dict[str, PixelIntensity]
    group_id: Optional[str] = None
    
    def calculate_mean_intensity(self, channel: str) -> float:
        """Business logic for intensity calculation"""
        if channel not in self.channel_intensities:
            raise ValueError(f"Channel {channel} not found")
        return self.channel_intensities[channel].mean_value
    
    def is_above_threshold(self, threshold: float, channel: str) -> bool:
        """Business rule for threshold comparison"""
        return self.calculate_mean_intensity(channel) > threshold
    
    def calculate_area(self) -> float:
        """Business logic for area calculation"""
        return self.roi.calculate_area()
```

#### 2. **Workflow Entity**
```python
# domain/entities/workflow.py
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowStep:
    name: str
    order: int
    required: bool = True
    parameters: Dict = None
    
class Workflow:
    """Core workflow entity"""
    def __init__(self, workflow_id: str, name: str):
        self.id = workflow_id
        self.name = name
        self.steps: List[WorkflowStep] = []
        self.current_step_index: int = 0
        self.status = WorkflowStatus.PENDING
        
    def add_step(self, step: WorkflowStep) -> None:
        """Business rule for adding steps"""
        if any(s.name == step.name for s in self.steps):
            raise ValueError(f"Step {step.name} already exists")
        self.steps.append(step)
        self.steps.sort(key=lambda x: x.order)
        
    def get_next_step(self) -> Optional[WorkflowStep]:
        """Business logic for step progression"""
        if self.current_step_index >= len(self.steps):
            return None
        return self.steps[self.current_step_index]
    
    def complete_current_step(self) -> None:
        """Business rule for step completion"""
        if self.status != WorkflowStatus.RUNNING:
            raise ValueError("Workflow must be running to complete steps")
        self.current_step_index += 1
        if self.current_step_index >= len(self.steps):
            self.status = WorkflowStatus.COMPLETED
```

#### 3. **Analysis Result Aggregate**
```python
# domain/entities/analysis_result.py
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime

@dataclass
class AnalysisResult:
    """Aggregate root for analysis results"""
    id: str
    dataset_id: str
    workflow_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    cells: List[Cell] = field(default_factory=list)
    statistics: Dict = field(default_factory=dict)
    
    def add_cell(self, cell: Cell) -> None:
        """Business rule for adding cells"""
        if any(c.id == cell.id for c in self.cells):
            raise ValueError(f"Cell {cell.id} already exists")
        self.cells.append(cell)
        
    def calculate_statistics(self) -> Dict:
        """Core business logic for statistics"""
        if not self.cells:
            return {}
            
        stats = {
            'total_cells': len(self.cells),
            'mean_area': sum(c.calculate_area() for c in self.cells) / len(self.cells),
            'groups': {}
        }
        
        # Group statistics
        groups = {}
        for cell in self.cells:
            if cell.group_id:
                if cell.group_id not in groups:
                    groups[cell.group_id] = []
                groups[cell.group_id].append(cell)
        
        for group_id, group_cells in groups.items():
            stats['groups'][group_id] = {
                'count': len(group_cells),
                'mean_area': sum(c.calculate_area() for c in group_cells) / len(group_cells)
            }
        
        self.statistics = stats
        return stats
```

### 📦 **Essential Value Objects**

```python
# domain/value_objects/roi_coordinates.py
from dataclasses import dataclass
from typing import List, Tuple

@dataclass(frozen=True)
class ROICoordinates:
    """Immutable ROI coordinates"""
    points: Tuple[Tuple[int, int], ...]
    
    def __post_init__(self):
        if len(self.points) < 3:
            raise ValueError("ROI must have at least 3 points")
        # Ensure all points are within valid range
        for x, y in self.points:
            if x < 0 or y < 0:
                raise ValueError(f"Invalid coordinates: ({x}, {y})")
    
    def calculate_centroid(self) -> Tuple[float, float]:
        """Pure calculation - no external dependencies"""
        x_coords = [p[0] for p in self.points]
        y_coords = [p[1] for p in self.points]
        return (sum(x_coords) / len(x_coords), 
                sum(y_coords) / len(y_coords))

# domain/value_objects/pixel_intensity.py
@dataclass(frozen=True)
class PixelIntensity:
    """Immutable pixel intensity measurements"""
    mean_value: float
    max_value: float
    min_value: float
    std_dev: float
    
    def __post_init__(self):
        if self.mean_value < 0 or self.max_value < 0 or self.min_value < 0:
            raise ValueError("Intensity values must be non-negative")
        if self.min_value > self.max_value:
            raise ValueError("Min value cannot exceed max value")
        if not (self.min_value <= self.mean_value <= self.max_value):
            raise ValueError("Mean must be between min and max")
```

### 🎯 **Core Domain Services**

```python
# domain/services/cell_grouping_service.py
from typing import List, Dict
from domain.entities import Cell

class CellGroupingService:
    """Pure domain service for cell grouping logic"""
    
    @staticmethod
    def group_by_intensity(
        cells: List[Cell], 
        channel: str, 
        num_groups: int = 5
    ) -> Dict[str, List[Cell]]:
        """
        Core business algorithm for grouping cells by intensity.
        This is pure domain logic with no external dependencies.
        """
        if not cells:
            return {}
        
        # Sort cells by intensity
        sorted_cells = sorted(
            cells, 
            key=lambda c: c.calculate_mean_intensity(channel)
        )
        
        # Calculate group boundaries
        cells_per_group = len(sorted_cells) // num_groups
        groups = {}
        
        for i in range(num_groups):
            group_id = f"group_{i+1}"
            start_idx = i * cells_per_group
            end_idx = start_idx + cells_per_group if i < num_groups - 1 else len(sorted_cells)
            
            group_cells = sorted_cells[start_idx:end_idx]
            for cell in group_cells:
                cell.group_id = group_id
            
            groups[group_id] = group_cells
        
        return groups
    
    @staticmethod
    def calculate_group_statistics(groups: Dict[str, List[Cell]]) -> Dict:
        """Pure business logic for group statistics"""
        statistics = {}
        for group_id, cells in groups.items():
            statistics[group_id] = {
                'cell_count': len(cells),
                'mean_area': sum(c.calculate_area() for c in cells) / len(cells),
                'area_std': CellGroupingService._calculate_std([c.calculate_area() for c in cells])
            }
        return statistics
    
    @staticmethod
    def _calculate_std(values: List[float]) -> float:
        """Pure calculation helper"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
```

### 🔧 **Domain Service for Threshold Calculation**

```python
# domain/services/threshold_service.py
from typing import List, Tuple
from domain.value_objects import PixelIntensity

class ThresholdService:
    """Pure domain service for threshold calculations"""
    
    @staticmethod
    def calculate_otsu_threshold(histogram: List[int]) -> float:
        """
        Pure Otsu algorithm implementation.
        No dependencies on OpenCV or other libraries.
        """
        total_pixels = sum(histogram)
        if total_pixels == 0:
            return 0
        
        # Calculate probabilities
        probabilities = [count / total_pixels for count in histogram]
        
        # Calculate cumulative sums
        cumulative_prob = []
        cumulative_mean = []
        prob_sum = 0
        mean_sum = 0
        
        for i, prob in enumerate(probabilities):
            prob_sum += prob
            mean_sum += i * prob
            cumulative_prob.append(prob_sum)
            cumulative_mean.append(mean_sum)
        
        # Find threshold that maximizes between-class variance
        max_variance = 0
        optimal_threshold = 0
        
        for t in range(len(histogram)):
            w0 = cumulative_prob[t]
            w1 = 1 - w0
            
            if w0 == 0 or w1 == 0:
                continue
            
            mu0 = cumulative_mean[t] / w0 if w0 > 0 else 0
            mu1 = (cumulative_mean[-1] - cumulative_mean[t]) / w1 if w1 > 0 else 0
            
            variance = w0 * w1 * (mu0 - mu1) ** 2
            
            if variance > max_variance:
                max_variance = variance
                optimal_threshold = t
        
        return float(optimal_threshold)
    
    @staticmethod
    def apply_threshold(
        intensities: List[PixelIntensity], 
        threshold: float
    ) -> Tuple[List[bool], float]:
        """
        Apply threshold to intensities and calculate percentage above.
        Pure business logic.
        """
        results = [intensity.mean_value > threshold for intensity in intensities]
        percentage_above = sum(results) / len(results) * 100 if results else 0
        return results, percentage_above
```

### 📋 **Workflow Orchestration Service**

```python
# domain/services/workflow_orchestrator.py
from typing import Dict, Optional
from domain.entities import Workflow, WorkflowStatus, AnalysisResult
from domain.exceptions import WorkflowException

class WorkflowOrchestrationService:
    """Pure domain service for workflow orchestration"""
    
    def validate_workflow(self, workflow: Workflow) -> bool:
        """Business rules for workflow validation"""
        if not workflow.steps:
            raise WorkflowException("Workflow must have at least one step")
        
        # Check for required steps
        required_steps = ['segmentation', 'analysis']
        step_names = {step.name for step in workflow.steps}
        
        for required in required_steps:
            if required not in step_names:
                raise WorkflowException(f"Required step '{required}' is missing")
        
        # Validate step order
        segmentation_order = next((s.order for s in workflow.steps if s.name == 'segmentation'), None)
        analysis_order = next((s.order for s in workflow.steps if s.name == 'analysis'), None)
        
        if segmentation_order >= analysis_order:
            raise WorkflowException("Segmentation must come before analysis")
        
        return True
    
    def can_proceed_to_next_step(self, workflow: Workflow) -> bool:
        """Business rule for step progression"""
        if workflow.status != WorkflowStatus.RUNNING:
            return False
        
        current_step = workflow.get_next_step()
        if not current_step:
            return False
        
        # Add business rules for step prerequisites
        if current_step.name == 'analysis':
            # Check if segmentation was completed
            return self._is_segmentation_complete(workflow)
        
        return True
    
    def _is_segmentation_complete(self, workflow: Workflow) -> bool:
        """Check if segmentation step was completed"""
        for i in range(workflow.current_step_index):
            if workflow.steps[i].name == 'segmentation':
                return True
        return False
```

### 🚨 **Domain Exceptions**

```python
# domain/exceptions.py
class DomainException(Exception):
    """Base exception for domain errors"""
    pass

class CellException(DomainException):
    """Cell-related domain errors"""
    pass

class WorkflowException(DomainException):
    """Workflow-related domain errors"""
    pass

class ThresholdException(DomainException):
    """Threshold-related domain errors"""
    pass

class InvalidIntensityException(DomainException):
    """Invalid intensity value errors"""
    pass
```

## 🔍 **Checklist for Your Domain Layer Review**

### Must Have:
- [ ] **No external dependencies** (no imports from cellpose, imagej, opencv, etc.)
- [ ] **No file I/O operations** (no Path, open(), read(), write())
- [ ] **No configuration reading** (no json.load, yaml.load)
- [ ] **No database operations** (no SQL, no ORM)
- [ ] **No logging** (logging is infrastructure)
- [ ] **No UI/presentation logic** (no print, input, formatting for display)
- [ ] **Pure business logic only** (algorithms, calculations, rules)
- [ ] **Rich domain models** (entities with behavior, not just data)
- [ ] **Value objects for type safety** (immutable, validated)
- [ ] **Domain services for complex operations** (stateless, pure functions)
- [ ] **Custom domain exceptions** (specific, meaningful errors)

### Should Have:
- [ ] **Aggregate roots** (AnalysisResult managing Cells)
- [ ] **Domain events** (WorkflowCompleted, CellsGrouped)
- [ ] **Specifications** (CellAboveThresholdSpecification)
- [ ] **Factories** (CellFactory, WorkflowFactory)
- [ ] **Repository interfaces** (as ports, not implementations)

## 📝 **Recommended Additions to Your Domain**

### 1. **Domain Events** (for better decoupling)
```python
# domain/events.py
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class DomainEvent:
    occurred_at: datetime = field(default_factory=datetime.now)

@dataclass
class CellsSegmentedEvent(DomainEvent):
    workflow_id: str
    cell_count: int

@dataclass
class CellsGroupedEvent(DomainEvent):
    workflow_id: str
    group_count: int
    cells_per_group: Dict[str, int]

@dataclass
class AnalysisCompletedEvent(DomainEvent):
    workflow_id: str
    result_id: str
    total_cells: int
```

### 2. **Specifications Pattern** (for complex business rules)
```python
# domain/specifications.py
from abc import ABC, abstractmethod
from domain.entities import Cell

class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate) -> bool:
        pass
    
    def and_(self, other: 'Specification') -> 'AndSpecification':
        return AndSpecification(self, other)
    
    def or_(self, other: 'Specification') -> 'OrSpecification':
        return OrSpecification(self, other)

class CellIntensitySpecification(Specification):
    def __init__(self, channel: str, min_intensity: float):
        self.channel = channel
        self.min_intensity = min_intensity
    
    def is_satisfied_by(self, cell: Cell) -> bool:
        return cell.calculate_mean_intensity(self.channel) >= self.min_intensity

class CellAreaSpecification(Specification):
    def __init__(self, min_area: float, max_area: float):
        self.min_area = min_area
        self.max_area = max_area
    
    def is_satisfied_by(self, cell: Cell) -> bool:
        area = cell.calculate_area()
        return self.min_area <= area <= self.max_area
```

### 3. **Factory Pattern** (for complex object creation)
```python
# domain/factories.py
from domain.entities import Workflow, WorkflowStep

class WorkflowFactory:
    @staticmethod
    def create_standard_workflow() -> Workflow:
        """Factory method for standard analysis workflow"""
        workflow = Workflow("standard", "Standard Analysis Workflow")
        
        workflow.add_step(WorkflowStep("data_selection", 1))
        workflow.add_step(WorkflowStep("segmentation", 2))
        workflow.add_step(WorkflowStep("roi_processing", 3))
        workflow.add_step(WorkflowStep("thresholding", 4))
        workflow.add_step(WorkflowStep("analysis", 5))
        
        return workflow
    
    @staticmethod
    def create_quick_workflow() -> Workflow:
        """Factory method for quick analysis workflow"""
        workflow = Workflow("quick", "Quick Analysis Workflow")
        
        workflow.add_step(WorkflowStep("segmentation", 1))
        workflow.add_step(WorkflowStep("analysis", 2))
        
        return workflow
```

## Summary

Your domain layer should be the **pure heart** of your application - containing only business logic, rules, and calculations. It should know nothing about how data is stored, how users interact with it, or what external tools are used. This makes it:

1. **Testable** - No mocking of external dependencies needed
2. **Portable** - Can move to different infrastructure
3. **Maintainable** - Business logic in one place
4. **Understandable** - Focuses only on the problem domain

Review your `ports_adapters_refactor` branch against this checklist and ensure all external dependencies are moved to adapters, leaving only pure business logic in the domain.



## Critical Issues to Look For

### 1. **External Dependencies**
Your domain should NOT have any imports from:
- `cellpose` (should be in adapters)
- `imagej` or `fiji` (should be in adapters)  
- `cv2` or `opencv` (should be in adapters)
- `pathlib`, `os` (file operations belong in adapters)
- `json`, `yaml` (config reading belongs in infrastructure)

### 2. **Core Domain Components You Should Have**

**Entities:**
- `Cell` - with methods like `calculate_mean_intensity()`, `is_above_threshold()`
- `Workflow` - with step management and progression logic
- `ROI` - representing regions of interest
- `AnalysisResult` - aggregate root managing cells and statistics

**Value Objects:**
- `ROICoordinates` - immutable coordinate data
- `PixelIntensity` - validated intensity measurements
- `ExperimentMetadata` - parsed metadata from file names
- `ThresholdParameters` - threshold configuration

**Domain Services:**
- `CellGroupingService` - pure algorithms for grouping cells by intensity
- `ThresholdService` - Otsu and other threshold calculations (pure math, no OpenCV)
- `WorkflowOrchestrationService` - workflow validation and progression rules
- `ROIProcessor` - ROI tracking and manipulation logic

### 3. **Key Principles**

Your domain layer should:
- Contain ONLY business logic and rules
- Have NO knowledge of external tools or frameworks
- Perform pure calculations and algorithms
- Define interfaces (ports) but not implement external interactions

### 4. **Recommended Additions**

Consider adding:
- **Domain Events** (`CellsSegmentedEvent`, `AnalysisCompletedEvent`)
- **Specifications Pattern** for complex business rules
- **Factory Pattern** for creating standard workflows

The domain layer is the heart of your application. It should be completely independent and testable without any external dependencies. All interactions with Cellpose, ImageJ, file systems, and user interfaces should be handled through ports and adapters, not in the domain itself.

Would you like me to help you refactor specific modules or create examples of how to properly structure particular domain services?