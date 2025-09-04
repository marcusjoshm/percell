# Percell Refactoring Guide: Ports and Adapters Architecture

## Executive Summary

This guide provides a systematic approach to refactor the Percell microscopy pipeline from its current monolithic structure to a clean Ports and Adapters (Hexagonal) architecture. The refactoring will improve testability, maintainability, and extensibility while preserving all existing functionality.

## 1. Architecture Overview

### Target Structure
```
percell/
├── domain/                 # Pure business logic
│   ├── entities/           # Business objects with identity
│   ├── value_objects/      # Immutable domain concepts
│   └── services/           # Domain operations
├── application/            # Use cases and orchestration
│   ├── use_cases/          # Application services
│   └── commands/           # Command objects
├── ports/                  # Interface definitions
│   ├── inbound/            # Driving ports (UI, API)
│   └── outbound/           # Driven ports (persistence, external)
├── adapters/               # Interface implementations
│   ├── inbound/            # CLI, future API adapters
│   └── outbound/           # File, ImageJ, Cellpose adapters
└── infrastructure/         # Framework and utilities
    ├── config/             # Configuration management
    └── bootstrap/          # Dependency injection
```

## 2. Phase 1: Foundation (Week 1-2)

### Step 1.1: Create Domain Layer Structure

Create the base domain structure without breaking existing code:

```python
# percell/domain/value_objects/experiment.py
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class DataType(Enum):
    SINGLE_TIMEPOINT = "single"
    MULTI_TIMEPOINT = "multi"

@dataclass(frozen=True)
class Channel:
    name: str
    is_segmentation: bool = False
    is_analysis: bool = False

@dataclass(frozen=True)
class Timepoint:
    id: str
    order: int

@dataclass(frozen=True)
class Region:
    id: str
    name: str

@dataclass(frozen=True)
class ExperimentSelection:
    data_type: DataType
    input_dir: Path
    output_dir: Path
    conditions: List[str]
    channels: List[Channel]
    timepoints: List[Timepoint]
    regions: List[Region]
```

```python
# percell/domain/value_objects/processing.py
@dataclass(frozen=True)
class BinningParameters:
    num_bins: int
    strategy: str  # "gmm", "kmeans", "uniform"
    
@dataclass(frozen=True)
class SegmentationParameters:
    model: str
    diameter: float
    flow_threshold: float
    cellprob_threshold: float
```

### Step 1.2: Define Core Port Interfaces

Start with the most critical ports:

```python
# percell/ports/outbound/image_port.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import numpy as np

class ImageReaderPort(ABC):
    @abstractmethod
    def read(self, path: Path) -> np.ndarray:
        """Read image from path"""
        pass
    
    @abstractmethod
    def read_with_metadata(self, path: Path) -> tuple[np.ndarray, Dict[str, Any]]:
        """Read image with metadata"""
        pass

class ImageWriterPort(ABC):
    @abstractmethod
    def write(self, path: Path, image: np.ndarray, metadata: Optional[Dict] = None) -> None:
        """Write image to path"""
        pass
```

```python
# percell/ports/outbound/macro_runner_port.py
class MacroRunnerPort(ABC):
    @abstractmethod
    def run_macro(self, macro_name: str, parameters: Dict[str, Any]) -> MacroResult:
        """Execute ImageJ macro with parameters"""
        pass
    
    @abstractmethod
    def validate_macro(self, macro_name: str) -> bool:
        """Check if macro exists and is valid"""
        pass
```

### Step 1.3: Extract First Domain Service

Start with the ROI tracking service as it's well-contained:

```python
# percell/domain/services/roi_tracking_service.py
import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Tuple, Dict

class ROITrackingService:
    """Pure domain service for ROI tracking logic"""
    
    def match_rois(self, 
                   source_rois: List[ROI], 
                   target_rois: List[ROI],
                   max_distance: float = 50.0) -> Dict[int, int]:
        """
        Match ROIs between timepoints using Hungarian algorithm.
        Returns mapping of source_id -> target_id
        """
        if not source_rois or not target_rois:
            return {}
        
        # Extract centroids
        source_centers = [self._get_centroid(roi) for roi in source_rois]
        target_centers = [self._get_centroid(roi) for roi in target_rois]
        
        # Build cost matrix
        cost_matrix = self._build_cost_matrix(source_centers, target_centers)
        
        # Solve assignment
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        # Filter by max distance
        matches = {}
        for i, j in zip(row_indices, col_indices):
            if cost_matrix[i, j] <= max_distance:
                matches[source_rois[i].id] = target_rois[j].id
        
        return matches
    
    def _get_centroid(self, roi: ROI) -> Tuple[float, float]:
        """Calculate ROI centroid"""
        # Pure calculation, no I/O
        return roi.calculate_centroid()
    
    def _build_cost_matrix(self, source: List, target: List) -> np.ndarray:
        """Build distance matrix between point sets"""
        # Pure numpy operations
        pass
```

## 3. Phase 2: Adapter Implementation (Week 2-3)

### Step 2.1: Create Adapter for ImageReaderPort

```python
# percell/adapters/outbound/tifffile_image_adapter.py
import tifffile
import numpy as np
from percell.ports.outbound.image_port import ImageReaderPort, ImageWriterPort

class TiffFileImageAdapter(ImageReaderPort, ImageWriterPort):
    """Tifffile-based implementation of image ports"""
    
    def read(self, path: Path) -> np.ndarray:
        return tifffile.imread(str(path))
    
    def read_with_metadata(self, path: Path) -> tuple[np.ndarray, Dict[str, Any]]:
        with tifffile.TiffFile(str(path)) as tif:
            image = tif.asarray()
            metadata = {
                'imagej_metadata': tif.imagej_metadata,
                'resolution': self._extract_resolution(tif)
            }
        return image, metadata
    
    def write(self, path: Path, image: np.ndarray, metadata: Optional[Dict] = None) -> None:
        tifffile.imwrite(str(path), image, metadata=metadata)
```

### Step 2.2: Create Adapter for MacroRunnerPort

```python
# percell/adapters/outbound/imagej_macro_adapter.py
import subprocess
import tempfile
from percell.ports.outbound.macro_runner_port import MacroRunnerPort
from percell.core.progress import run_subprocess_with_spinner

class ImageJMacroAdapter(MacroRunnerPort):
    def __init__(self, imagej_path: Path, macro_dir: Path):
        self.imagej_path = imagej_path
        self.macro_dir = macro_dir
    
    def run_macro(self, macro_name: str, parameters: Dict[str, Any]) -> MacroResult:
        # Create temporary macro with injected parameters
        macro_content = self._prepare_macro(macro_name, parameters)
        
        with tempfile.NamedTemporaryFile(suffix='.ijm', mode='w', delete=False) as f:
            f.write(macro_content)
            temp_macro = f.name
        
        try:
            # Run ImageJ
            cmd = [str(self.imagej_path), '--headless', '--run', temp_macro]
            result = run_subprocess_with_spinner(
                cmd, 
                f"Running {macro_name}",
                capture_output=True
            )
            return MacroResult(success=result.returncode == 0, output=result.stdout)
        finally:
            Path(temp_macro).unlink(missing_ok=True)
```

## 4. Phase 3: Application Services (Week 3-4)

### Step 3.1: Create Use Cases

Transform existing stage logic into clean use cases:

```python
# percell/application/use_cases/segment_cells.py
from percell.ports.outbound.image_port import ImageReaderPort, ImageWriterPort
from percell.ports.outbound.segmenter_port import SegmenterPort
from percell.domain.value_objects import SegmentationParameters

class SegmentCellsUseCase:
    def __init__(self,
                 image_reader: ImageReaderPort,
                 image_writer: ImageWriterPort,
                 segmenter: SegmenterPort):
        self.image_reader = image_reader
        self.image_writer = image_writer
        self.segmenter = segmenter
    
    def execute(self, 
                input_path: Path,
                output_path: Path,
                parameters: SegmentationParameters) -> SegmentationResult:
        """Execute cell segmentation workflow"""
        
        # 1. Read input image
        image = self.image_reader.read(input_path)
        
        # 2. Run segmentation
        masks = self.segmenter.segment(image, parameters)
        
        # 3. Save results
        self.image_writer.write(output_path, masks)
        
        # 4. Return structured result
        return SegmentationResult(
            input_path=input_path,
            output_path=output_path,
            cell_count=len(np.unique(masks)) - 1,
            parameters=parameters
        )
```

### Step 3.2: Refactor GroupCells Module

This is a high-priority module mixing domain logic with I/O:

```python
# percell/domain/services/cell_grouping_service.py
import numpy as np
from sklearn.mixture import GaussianMixture
from typing import List, Tuple

class CellGroupingService:
    """Pure domain service for cell grouping logic"""
    
    def compute_auc(self, intensity_profile: np.ndarray) -> float:
        """Compute area under curve for intensity profile"""
        # Pure calculation
        return np.trapz(intensity_profile)
    
    def group_cells_by_intensity(self,
                                 cell_intensities: List[float],
                                 parameters: BinningParameters) -> List[int]:
        """Assign cells to bins based on intensity"""
        if parameters.strategy == "gmm":
            return self._gmm_grouping(cell_intensities, parameters.num_bins)
        elif parameters.strategy == "kmeans":
            return self._kmeans_grouping(cell_intensities, parameters.num_bins)
        else:
            return self._uniform_grouping(cell_intensities, parameters.num_bins)
    
    def aggregate_cells_in_group(self,
                                 cell_images: List[np.ndarray],
                                 group_assignments: List[int]) -> Dict[int, np.ndarray]:
        """Sum cell images by group"""
        # Pure numpy operations
        aggregated = {}
        for group_id in np.unique(group_assignments):
            mask = np.array(group_assignments) == group_id
            group_cells = [img for img, m in zip(cell_images, mask) if m]
            aggregated[group_id] = np.sum(group_cells, axis=0)
        return aggregated
```

```python
# percell/application/use_cases/group_cells.py
class GroupCellsUseCase:
    def __init__(self,
                 cell_grouping_service: CellGroupingService,
                 image_reader: ImageReaderPort,
                 image_writer: ImageWriterPort,
                 metadata_store: MetadataStorePort):
        self.grouping = cell_grouping_service
        self.image_reader = image_reader
        self.image_writer = image_writer
        self.metadata_store = metadata_store
    
    def execute(self, cell_dir: Path, output_dir: Path, parameters: BinningParameters):
        # 1. Load all cell images
        cell_files = sorted(cell_dir.glob("*.tif"))
        cells = [self.image_reader.read(f) for f in cell_files]
        
        # 2. Compute intensities (domain logic)
        intensities = [self.grouping.compute_auc(cell) for cell in cells]
        
        # 3. Group cells (domain logic)
        assignments = self.grouping.group_cells_by_intensity(intensities, parameters)
        
        # 4. Aggregate by group (domain logic)
        aggregated = self.grouping.aggregate_cells_in_group(cells, assignments)
        
        # 5. Save outputs (through ports)
        for group_id, group_image in aggregated.items():
            output_path = output_dir / f"group_{group_id}.tif"
            self.image_writer.write(output_path, group_image)
        
        # 6. Save metadata
        metadata = self._build_metadata(intensities, assignments, parameters)
        self.metadata_store.save(output_dir / "grouping_metadata.csv", metadata)
```

## 5. Phase 4: Dependency Injection (Week 4)

### Step 4.1: Create Container

```python
# percell/infrastructure/bootstrap/container.py
from dependency_injector import containers, providers
from percell.adapters.outbound.tifffile_image_adapter import TiffFileImageAdapter
from percell.adapters.outbound.imagej_macro_adapter import ImageJMacroAdapter
from percell.domain.services import CellGroupingService, ROITrackingService
from percell.application.use_cases import SegmentCellsUseCase, GroupCellsUseCase

class Container(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()
    
    # Domain Services (pure, no dependencies)
    cell_grouping_service = providers.Singleton(CellGroupingService)
    roi_tracking_service = providers.Singleton(ROITrackingService)
    
    # Adapters
    image_adapter = providers.Singleton(TiffFileImageAdapter)
    
    macro_adapter = providers.Singleton(
        ImageJMacroAdapter,
        imagej_path=config.imagej_path,
        macro_dir=config.macro_dir
    )
    
    # Use Cases
    segment_cells_use_case = providers.Factory(
        SegmentCellsUseCase,
        image_reader=image_adapter,
        image_writer=image_adapter,
        segmenter=macro_adapter  # or CellposeAdapter
    )
    
    group_cells_use_case = providers.Factory(
        GroupCellsUseCase,
        cell_grouping_service=cell_grouping_service,
        image_reader=image_adapter,
        image_writer=image_adapter,
        metadata_store=providers.Singleton(PandasMetadataAdapter)
    )
```

### Step 4.2: Refactor Stage Classes

Transform monolithic stages to use injected use cases:

```python
# percell/adapters/inbound/cli/stages/segmentation_stage.py
from percell.core.stages import StageBase
from percell.application.use_cases import SegmentCellsUseCase

class SegmentationStage(StageBase):
    def __init__(self, segment_use_case: SegmentCellsUseCase):
        super().__init__()
        self.segment_use_case = segment_use_case
    
    def run(self, args):
        # Convert args to domain objects
        parameters = SegmentationParameters(
            model=args.cellpose_model,
            diameter=args.diameter,
            flow_threshold=args.flow_threshold,
            cellprob_threshold=args.cellprob_threshold
        )
        
        # Delegate to use case
        for image_path in self._find_images(args.input_dir):
            output_path = self._get_output_path(image_path, args.output_dir)
            result = self.segment_use_case.execute(
                input_path=image_path,
                output_path=output_path,
                parameters=parameters
            )
            self.logger.info(f"Segmented {result.cell_count} cells")
```

## 6. Phase 5: Testing Strategy (Ongoing)

### Step 5.1: Test Domain Services

```python
# tests/domain/services/test_cell_grouping_service.py
import pytest
import numpy as np
from percell.domain.services import CellGroupingService
from percell.domain.value_objects import BinningParameters

class TestCellGroupingService:
    def test_compute_auc(self):
        service = CellGroupingService()
        profile = np.array([1, 2, 3, 2, 1])
        auc = service.compute_auc(profile)
        assert auc == pytest.approx(9.0)  # trapz([1,2,3,2,1])
    
    def test_uniform_grouping(self):
        service = CellGroupingService()
        intensities = [1, 2, 3, 4, 5, 6]
        params = BinningParameters(num_bins=2, strategy="uniform")
        groups = service.group_cells_by_intensity(intensities, params)
        assert len(set(groups)) == 2
        assert groups == [0, 0, 0, 1, 1, 1]  # uniform split
```

### Step 5.2: Test Use Cases with Mocks

```python
# tests/application/use_cases/test_group_cells.py
from unittest.mock import Mock, MagicMock
from percell.application.use_cases import GroupCellsUseCase

def test_group_cells_use_case():
    # Create mocks
    grouping_service = Mock()
    image_reader = Mock()
    image_writer = Mock()
    metadata_store = Mock()
    
    # Setup mock returns
    image_reader.read.return_value = np.ones((100, 100))
    grouping_service.compute_auc.return_value = 42.0
    grouping_service.group_cells_by_intensity.return_value = [0, 0, 1, 1]
    
    # Execute use case
    use_case = GroupCellsUseCase(
        grouping_service, image_reader, image_writer, metadata_store
    )
    use_case.execute(Path("/input"), Path("/output"), BinningParameters(2, "uniform"))
    
    # Verify interactions
    assert grouping_service.compute_auc.called
    assert image_writer.write.called
    assert metadata_store.save.called
```

## 7. Migration Checklist

### Week 1-2: Foundation
- [ ] Create domain layer structure (entities, value objects, services directories)
- [ ] Define core value objects (Channel, Timepoint, Region, etc.)
- [ ] Define port interfaces (Image, Macro, ROI, Metadata ports)
- [ ] Extract ROI tracking service as pure domain logic
- [ ] Extract cell grouping service as pure domain logic

### Week 2-3: Adapters
- [ ] Implement TiffFileImageAdapter
- [ ] Implement ImageJMacroAdapter
- [ ] Implement CellposeAdapter
- [ ] Implement PandasMetadataAdapter
- [ ] Create filesystem adapter for testing

### Week 3-4: Application Layer
- [ ] Create SegmentCellsUseCase
- [ ] Create GroupCellsUseCase
- [ ] Create TrackROIsUseCase
- [ ] Create AnalyzeMasksUseCase
- [ ] Refactor stage_classes.py to use use cases

### Week 4: Integration
- [ ] Set up dependency injection container
- [ ] Refactor main.py to use container
- [ ] Update pipeline.py to work with new structure
- [ ] Create integration tests

### Week 5: Testing & Documentation
- [ ] Write unit tests for all domain services
- [ ] Write unit tests for use cases with mocks
- [ ] Create integration test suite
- [ ] Update documentation
- [ ] Create architecture diagrams

## 8. Backward Compatibility

During migration, maintain backward compatibility:

```python
# percell/modules/group_cells.py (temporary shim)
"""Legacy interface maintained during migration"""
from percell.infrastructure.bootstrap import get_container

def main():
    """Legacy CLI entry point"""
    args = parse_args()
    container = get_container()
    use_case = container.group_cells_use_case()
    
    # Map legacy args to new structure
    parameters = BinningParameters(
        num_bins=args.bins,
        strategy=args.method
    )
    
    use_case.execute(
        Path(args.input_dir),
        Path(args.output_dir),
        parameters
    )

if __name__ == "__main__":
    main()
```

## 9. Key Benefits After Refactoring

1. **Testability**: Pure domain logic can be tested without any I/O
2. **Flexibility**: Easy to swap implementations (e.g., different image libraries)
3. **Maintainability**: Clear separation of concerns
4. **Extensibility**: New features can be added without touching core logic
5. **Performance**: Can introduce async/parallel processing at adapter level
6. **Debugging**: Easier to isolate issues to specific layers

## 10. Common Pitfalls to Avoid

1. **Don't refactor everything at once** - Work incrementally
2. **Don't break existing functionality** - Keep shims during migration
3. **Don't over-abstract** - Start simple, refactor when patterns emerge
4. **Don't ignore tests** - Write tests for new code immediately
5. **Don't mix layers** - Maintain strict boundaries between layers

## Next Steps

1. Start with Phase 1: Create the domain structure
2. Pick one high-value module (recommend `group_cells.py`) for full refactoring
3. Validate the approach works end-to-end
4. Apply pattern to remaining modules
5. Remove legacy code once all migrations are complete

This refactoring will transform Percell from a script collection into a maintainable, extensible application ready for growth and new features.