# Flexible Data Selection Refactoring Plan

## Project Context

This refactoring plan is for the PerCell microscopy analysis program. The goal is to make the data selection system work with any microscopy export directory structure, rather than assuming a specific organization.

**Problem**: Current implementation assumes specific directory structures (conditions/timepoints/regions). Real-world microscopy exports vary widely.

**Solution**: Implement flexible, filename-based discovery that works regardless of directory structure.

**Example Input Structure** (what we need to support):
```
2025-10-16_export/
├── A549 UFD1L KO + UFD1L-dTAG Clone 1 As/
│   ├── 18h dTAG13_Merged_z00_ch00.tif
│   ├── 18h dTAG13_Merged_z00_ch01.tif
│   ├── 3h dTAG13_Merged_z00_ch00.tif
│   ├── No dTAG13_Merged_z00_ch00.tif
│   └── MetaData/
└── A549 UFD1L KO + UFD1L-dTAG Clone 2 As/
    ├── 18h dTAG13_Merged_z00_ch00.tif
    └── ...
```

**Key Requirement**: Only hard rule is that first layer of directories are project folders. Everything else should be discovered from filenames.

---

## Phase 1: Enhance Domain Models

### Task 1.1: Update FileMetadata Model

**File**: Find and update `percell/domain/models.py` (or wherever `FileMetadata` is defined)

**Current model**:
```python
@dataclass
class FileMetadata:
    original_name: str
    region: str
    channel: Optional[str] = None
    timepoint: Optional[str] = None
    z_index: Optional[int] = None
    extension: str = ".tif"
```

**Add these fields**:
```python
    # Path-based metadata for flexible grouping
    project_folder: Optional[str] = None  # First directory under root (e.g., "Clone 1 As")
    full_path: Optional[Path] = None      # Complete file path
    relative_path: Optional[str] = None   # Path relative to root
```

**Rationale**: We need to track where files come from in the directory tree, not just their filename metadata.

---

### Task 1.2: Create DatasetGrouping Model

**File**: `percell/domain/models.py`

**Add new model**:
```python
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class DatasetGrouping:
    """Defines how files should be grouped for analysis.
    
    Example:
        group_by=['project_folder', 'region'] means group files by 
        project folder first, then by region name.
        
        filter_by={'channel': ['ch00', 'ch01']} means only include
        files from channels ch00 and ch01.
    """
    group_by: List[str] = field(default_factory=list)
    filter_by: Dict[str, List[str]] = field(default_factory=dict)
```

**Rationale**: This allows users to define their own grouping logic instead of hardcoding assumptions.

---

### Task 1.3: Update DatasetSelection Model

**File**: `percell/domain/models.py`

**Current model**:
```python
@dataclass
class DatasetSelection:
    root: Path
    conditions: Optional[List[str]] = None
    timepoints: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    channels: Optional[List[str]] = None
```

**Add these fields** (keep existing for backward compatibility):
```python
    # NEW: Flexible dimension-based selection
    condition_dimension: str = "project_folder"  # Which dimension represents conditions
    dimension_filters: Dict[str, List[str]] = field(default_factory=dict)  # Generic filters
```

**Important**: Don't remove existing fields! We need backward compatibility.

---

## Phase 2: Create New Domain Service

### Task 2.1: Create FlexibleDataSelectionService

**Create new file**: `percell/domain/flexible_data_selection_service.py`

**Implementation**:

```python
"""Flexible data selection service that works with any directory structure.

This service discovers files and metadata without assuming specific directory
organization. The only requirement is that the first directory level under root
contains project folders.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from .file_naming_service import FileNamingService
from ..models import FileMetadata, DatasetSelection


class FlexibleDataSelectionService:
    """Data selection that adapts to any directory structure."""
    
    def __init__(self) -> None:
        self._naming = FileNamingService()
    
    def discover_all_files(self, root: Path) -> List[Tuple[Path, FileMetadata]]:
        """Discover all microscopy files and parse their metadata.
        
        Recursively scans for .tif/.tiff files and extracts metadata from
        filenames. Also captures path-based information.
        
        Args:
            root: Root directory to scan
            
        Returns:
            List of (filepath, metadata) tuples
        """
        results = []
        
        if not root.exists() or not root.is_dir():
            return results
        
        # Recursively find all TIF files
        for pattern in ["**/*.tif", "**/*.tiff"]:
            for file_path in root.glob(pattern):
                if not file_path.is_file():
                    continue
                
                try:
                    # Parse filename metadata
                    meta = self._naming.parse_microscopy_filename(file_path.name)
                    
                    # Add path-based metadata
                    meta.full_path = file_path
                    meta.project_folder = self._extract_project_folder(file_path, root)
                    meta.relative_path = str(file_path.relative_to(root))
                    
                    results.append((file_path, meta))
                    
                except Exception as e:
                    # Log but don't fail on unparseable files
                    print(f"Warning: Could not parse {file_path.name}: {e}")
                    continue
        
        return results
    
    def _extract_project_folder(self, file_path: Path, root: Path) -> str:
        """Extract the project folder (first directory level under root).
        
        Args:
            file_path: Full path to file
            root: Root directory
            
        Returns:
            Name of project folder, or "root" if file is directly in root
        """
        try:
            relative = file_path.relative_to(root)
            if len(relative.parts) > 1:
                return relative.parts[0]
            return "root"
        except ValueError:
            return "unknown"
    
    def get_available_dimensions(self, 
                                 files_meta: List[Tuple[Path, FileMetadata]]) -> Dict[str, List[str]]:
        """Extract all available dimensions from discovered files.
        
        Dimensions are any metadata that can be used for grouping or filtering:
        - project_folder: First directory under root
        - region: Base filename (e.g., "18h dTAG13_Merged")
        - channel: Channel identifier (e.g., "ch00")
        - timepoint: Timepoint identifier (e.g., "t0")
        - z_index: Z-slice index (e.g., "0", "1", "2")
        
        Args:
            files_meta: List of (filepath, metadata) tuples
            
        Returns:
            Dict mapping dimension names to sorted lists of unique values
        """
        dimensions: Dict[str, Set[str]] = {
            'project_folder': set(),
            'region': set(),
            'channel': set(),
            'timepoint': set(),
            'z_index': set()
        }
        
        for file_path, meta in files_meta:
            if meta.project_folder:
                dimensions['project_folder'].add(meta.project_folder)
            if meta.region:
                dimensions['region'].add(meta.region)
            if meta.channel:
                dimensions['channel'].add(meta.channel)
            if meta.timepoint:
                dimensions['timepoint'].add(meta.timepoint)
            if meta.z_index is not None:
                dimensions['z_index'].add(str(meta.z_index))
        
        # Convert sets to sorted lists
        return {k: sorted(list(v)) for k, v in dimensions.items()}
    
    def group_files(self, 
                   files_meta: List[Tuple[Path, FileMetadata]],
                   group_by: List[str]) -> Dict[Tuple[str, ...], List[Path]]:
        """Group files by specified dimensions.
        
        Example:
            group_by=['project_folder', 'timepoint'] will create groups like:
            ('Clone 1 As', 't0'): [file1.tif, file2.tif, ...]
            ('Clone 1 As', 't1'): [file3.tif, file4.tif, ...]
            ('Clone 2 As', 't0'): [file5.tif, file6.tif, ...]
        
        Args:
            files_meta: List of (filepath, metadata) tuples
            group_by: List of dimension names to group by
            
        Returns:
            Dict mapping group keys (tuples) to lists of file paths
        """
        groups: Dict[Tuple[str, ...], List[Path]] = {}
        
        for file_path, meta in files_meta:
            # Build group key from requested dimensions
            key_parts = []
            for dim in group_by:
                value = getattr(meta, dim, None)
                # Convert to string, use "none" for missing values
                str_value = str(value) if value is not None else "none"
                key_parts.append(str_value)
            
            group_key = tuple(key_parts)
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(file_path)
        
        return groups
    
    def filter_files(self,
                    files_meta: List[Tuple[Path, FileMetadata]],
                    filters: Dict[str, List[str]]) -> List[Path]:
        """Filter files by dimension values.
        
        Example:
            filters={'channel': ['ch00', 'ch01'], 'timepoint': ['t0']}
            Will return only files that are:
            - From channel ch00 OR ch01 AND
            - From timepoint t0
        
        Args:
            files_meta: List of (filepath, metadata) tuples
            filters: Dict mapping dimension names to lists of allowed values
            
        Returns:
            List of file paths that match all filters
        """
        if not filters:
            return [fp for fp, _ in files_meta]
        
        result = []
        
        for file_path, meta in files_meta:
            include = True
            
            # Check each filter dimension
            for dim, allowed_values in filters.items():
                meta_value = getattr(meta, dim, None)
                
                # Convert to string for comparison
                str_value = str(meta_value) if meta_value is not None else None
                
                # If this dimension doesn't match any allowed value, exclude file
                if str_value not in allowed_values:
                    include = False
                    break
            
            if include:
                result.append(file_path)
        
        return result
    
    def validate_selection(self,
                          files_meta: List[Tuple[Path, FileMetadata]],
                          selection: DatasetSelection) -> bool:
        """Validate that a selection is possible with discovered files.
        
        Args:
            files_meta: List of discovered (filepath, metadata) tuples
            selection: User's selection to validate
            
        Returns:
            True if selection is valid, False otherwise
        """
        if not files_meta:
            return False
        
        available = self.get_available_dimensions(files_meta)
        
        # Check if requested dimension values exist
        dimension_filters = selection.dimension_filters
        
        for dim, requested_values in dimension_filters.items():
            available_values = available.get(dim, [])
            
            for value in requested_values:
                if value not in available_values:
                    print(f"Warning: {dim}='{value}' not found in available values: {available_values}")
                    return False
        
        # Also check legacy fields for backward compatibility
        if selection.channels:
            if not set(selection.channels).issubset(set(available.get('channel', []))):
                return False
        
        if selection.timepoints:
            if not set(selection.timepoints).issubset(set(available.get('timepoint', []))):
                return False
        
        return True
    
    def get_dimension_summary(self, files_meta: List[Tuple[Path, FileMetadata]]) -> str:
        """Generate a human-readable summary of discovered dimensions.
        
        Useful for logging and user feedback.
        
        Args:
            files_meta: List of discovered (filepath, metadata) tuples
            
        Returns:
            Formatted string summarizing discovered dimensions
        """
        dimensions = self.get_available_dimensions(files_meta)
        
        lines = [f"Discovered {len(files_meta)} files with the following dimensions:"]
        
        for dim, values in dimensions.items():
            if values:
                preview = ', '.join(values[:5])
                more = f" (and {len(values) - 5} more)" if len(values) > 5 else ""
                lines.append(f"  {dim}: {len(values)} unique values - {preview}{more}")
            else:
                lines.append(f"  {dim}: none found")
        
        return '\n'.join(lines)
```

**Key Features**:
1. No assumptions about directory structure
2. Works purely from filenames and first-level directories
3. Discovers all dimensions automatically
4. Flexible grouping and filtering
5. Backward compatible with legacy selection format

---

### Task 2.2: Enhance FileNamingService Parser

**File**: `percell/domain/file_naming_service.py`

**Current implementation** expects patterns like `_s(\d+)`, `_z(\d+)`, `_ch(\d+)`, `_t(\d+)`

**Problem**: The example files use different patterns:
- `18h dTAG13_Merged_z00_ch00.tif` - no underscores before z/ch
- Region name has spaces: "18h dTAG13"

**Update `parse_microscopy_filename` method**:

```python
def parse_microscopy_filename(self, filename: str) -> FileMetadata:
    """Parse a microscopy filename to extract metadata.
    
    Now handles multiple naming conventions:
    - Standard: "region_s1_t0_ch1_z5.tif"
    - Leica-style: "18h dTAG13_Merged_z00_ch00.tif"
    - Simple: "MyExperiment_ch00.tif"
    
    Args:
        filename: Filename to parse.

    Returns:
        FileMetadata: Parsed metadata.
    """
    # Accept .tif/.tiff only
    _, ext = os.path.splitext(filename)
    if ext.lower() not in {".tif", ".tiff"}:
        raise ValueError(f"Unsupported extension: {ext}")

    base = filename[: -len(ext)] if ext else filename

    # Enhanced patterns - more flexible matching
    # Match with or without underscore prefix, case insensitive
    token_patterns = {
        "tile": r"[_\s]?s(\d+)",
        "z_index": r"[_\s]?z(\d+)",
        "channel": r"[_\s]?ch(\d+)",
        "timepoint": r"[_\s]?t(\d+)",
    }

    # Extract tokens without caring about order; record spans to remove
    spans = []
    values: Dict[str, object] = {}
    
    for key, pat in token_patterns.items():
        m = re.search(pat, base, re.IGNORECASE)
        if m:
            # Record the full match span (including optional prefix)
            spans.append((m.start(), m.end()))
            val = m.group(1)
            
            if key == "z_index":
                values[key] = int(val)
            elif key == "channel":
                values[key] = f"ch{val}"
            elif key == "timepoint":
                values[key] = f"t{val}"
            # tile is not persisted in FileMetadata

    # Remove found token substrings to get region/image name
    # Sort in reverse order to remove from end to start (preserves earlier indices)
    spans.sort(reverse=True)
    region = base
    for s, e in spans:
        region = region[:s] + region[e:]
    
    # Clean up the region name
    region = region.strip("_").strip()
    
    # If region is empty, use the original base name
    if not region:
        region = base

    return FileMetadata(
        original_name=filename,
        region=region,
        channel=values.get("channel"),
        timepoint=values.get("timepoint"),
        z_index=values.get("z_index"),
        extension=ext,
    )
```

**Test cases to verify**:
```python
# Should parse correctly:
parse_microscopy_filename("18h dTAG13_Merged_z00_ch00.tif")
# Expected: region="18h dTAG13_Merged", channel="ch00", timepoint=None, z_index=0

parse_microscopy_filename("3h dTAG13_Merged_z02_ch01.tif")
# Expected: region="3h dTAG13_Merged", channel="ch01", timepoint=None, z_index=2

parse_microscopy_filename("No dTAG13_Merged_z00_ch00.tif")
# Expected: region="No dTAG13_Merged", channel="ch00", timepoint=None, z_index=0

parse_microscopy_filename("region_t0_ch1_z5.tif")
# Expected: region="region", channel="ch1", timepoint="t0", z_index=5
```

---

## Phase 3: Update Application Layer

### Task 3.1: Add Feature Flag to Config

**File**: `percell/config/default_config.yaml` (or wherever default config is)

**Add under data_selection section**:
```yaml
data_selection:
  # Feature flag for flexible selection (set to false for legacy behavior)
  use_flexible_selection: true
  
  # Existing config...
  selected_datatype: null
  selected_conditions: []
  selected_timepoints: []
  selected_regions: []
  segmentation_channel: null
  analysis_channels: []
```

---

### Task 3.2: Refactor DataSelectionStage

**File**: `percell/application/stages/data_selection_stage.py`

**Changes to `__init__` method**:

```python
def __init__(self, config, logger, stage_name="data_selection"):
    super().__init__(config, logger, stage_name)
    
    # Legacy instance variables (keep for backward compatibility)
    self.experiment_metadata = {}
    self.selected_datatype = None
    self.selected_conditions = []
    self.selected_timepoints = []
    self.selected_regions = []
    self.segmentation_channel = None
    self.analysis_channels = []
    
    # Domain services
    self._selection_service = DataSelectionService()  # Legacy
    self._naming_service = FileNamingService()
    
    # NEW: Flexible selection service and state
    from percell.domain.flexible_data_selection_service import FlexibleDataSelectionService
    self._flexible_selection = FlexibleDataSelectionService()
    self.discovered_files: List[Tuple[Path, FileMetadata]] = []
    self.available_dimensions: Dict[str, List[str]] = {}
    self.condition_dimension: str = "project_folder"  # What represents a "condition"
```

**Update `run` method** to support dual mode:

```python
def run(self, **kwargs) -> bool:
    """Run the data selection stage."""
    try:
        self.logger.info("Starting Data Selection Stage")
        
        # Store input and output directories
        self.input_dir = Path(kwargs['input_dir'])
        self.output_dir = Path(kwargs['output_dir'])
        self._fs = kwargs.get('fs')
        
        # Check feature flag
        use_flexible = self.config.get('data_selection.use_flexible_selection', True)
        
        if use_flexible:
            self.logger.info("Using flexible data selection mode")
            return self._run_flexible_workflow(**kwargs)
        else:
            self.logger.info("Using legacy data selection mode")
            return self._run_legacy_workflow(**kwargs)
            
    except Exception as e:
        self.logger.error(f"Error in Data Selection Stage: {e}")
        return False
```

**Add new method** `_run_flexible_workflow`:

```python
def _run_flexible_workflow(self, **kwargs) -> bool:
    """Run flexible data selection workflow.
    
    This workflow:
    1. Sets up output directory structure
    2. Discovers all files and dimensions
    3. Interactive selection of dimensions
    4. Copies filtered files to output
    """
    try:
        # Step 1: Setup output directory structure
        self.logger.info("Setting up output directory structure...")
        if not self._setup_output_structure():
            return False
        
        # Step 2: Discover files and dimensions (replaces _extract_experiment_metadata)
        self.logger.info("Discovering files and dimensions...")
        if not self._discover_files_and_dimensions():
            return False
        
        # Step 3: Interactive dimension-based selection (replaces _run_interactive_selection)
        self.logger.info("Starting interactive dimension-based selection...")
        if not self._run_flexible_interactive_selection():
            return False
        
        # Step 4: Save selections to config
        self.logger.info("Saving data selections...")
        self._save_flexible_selections_to_config()
        
        # Step 5: Create output directories for selected data
        self.logger.info("Creating output directories...")
        if not self._create_flexible_output_directories():
            return False
        
        # Step 6: Copy filtered files (replaces _copy_selected_files)
        self.logger.info("Copying selected files...")
        if not self._copy_filtered_files():
            return False
        
        self.logger.info("Flexible Data Selection Stage completed successfully")
        return True
        
    except Exception as e:
        self.logger.error(f"Error in flexible workflow: {e}")
        return False
```

**Add new method** `_run_legacy_workflow`:

```python
def _run_legacy_workflow(self, **kwargs) -> bool:
    """Run legacy data selection workflow (original implementation).
    
    Kept for backward compatibility.
    """
    # This is the original run() method logic
    try:
        if not self._setup_output_structure():
            return False
        
        if not self._prepare_input_structure(str(self.input_dir)):
            return False
        
        if not self._extract_experiment_metadata(str(self.input_dir)):
            return False
        
        if not self._run_interactive_selection():
            return False
        
        self._save_selections_to_config()
        
        if not self._create_selected_condition_directories():
            return False
        
        if not self._copy_selected_files():
            return False
        
        self.logger.info("Legacy Data Selection Stage completed successfully")
        return True
        
    except Exception as e:
        self.logger.error(f"Error in legacy workflow: {e}")
        return False
```

---

### Task 3.3: Implement Flexible Discovery Method

**Add to DataSelectionStage**:

```python
def _discover_files_and_dimensions(self) -> bool:
    """Discover all files and extract available dimensions.
    
    Replaces _extract_experiment_metadata for flexible mode.
    """
    try:
        self.logger.info(f"Scanning directory: {self.input_dir}")
        
        # Use flexible service to discover all files
        self.discovered_files = self._flexible_selection.discover_all_files(self.input_dir)
        
        if not self.discovered_files:
            self.logger.error("No microscopy files found in input directory")
            return False
        
        self.logger.info(f"Discovered {len(self.discovered_files)} files")
        
        # Extract available dimensions
        self.available_dimensions = self._flexible_selection.get_available_dimensions(
            self.discovered_files
        )
        
        # Log summary
        summary = self._flexible_selection.get_dimension_summary(self.discovered_files)
        self.logger.info(f"\n{summary}")
        print(f"\n{summary}\n")
        
        # Store in experiment_metadata for compatibility
        self.experiment_metadata = {
            'discovered_files_count': len(self.discovered_files),
            'available_dimensions': self.available_dimensions
        }
        
        return True
        
    except Exception as e:
        self.logger.error(f"Error discovering files and dimensions: {e}")
        return False
```

---

### Task 3.4: Implement Flexible Interactive Selection

**Add to DataSelectionStage**:

```python
def _run_flexible_interactive_selection(self) -> bool:
    """Run flexible interactive selection based on discovered dimensions.
    
    Replaces _run_interactive_selection for flexible mode.
    """
    try:
        # Step 1: Select what dimension represents "conditions"
        if not self._select_condition_dimension():
            return False
        
        # Step 2: Select specific conditions
        if not self._select_dimension_values('condition', f"Select {self.condition_dimension}s to analyze"):
            return False
        
        # Step 3: Select channels
        if 'channel' in self.available_dimensions and self.available_dimensions['channel']:
            if not self._select_channels_flexible():
                return False
        
        # Step 4: Select timepoints (if any exist)
        if 'timepoint' in self.available_dimensions and self.available_dimensions['timepoint']:
            if not self._select_timepoints_flexible():
                return False
        
        # Step 5: Select regions (if needed)
        if 'region' in self.available_dimensions and len(self.available_dimensions['region']) > 1:
            if not self._select_regions_flexible():
                return False
        
        return True
        
    except Exception as e:
        self.logger.error(f"Error in flexible interactive selection: {e}")
        return False

def _select_condition_dimension(self) -> bool:
    """Let user choose which dimension represents experimental conditions."""
    print("\n" + "="*80)
    print("STEP 1: Define Experimental Conditions")
    print("="*80)
    print("\nWhich dimension represents your experimental conditions?")
    print("(Conditions are the different experimental groups you want to compare)")
    
    # Only show dimensions that have multiple values
    available_for_conditions = {
        dim: values for dim, values in self.available_dimensions.items()
        if len(values) > 1
    }
    
    if not available_for_conditions:
        self.logger.error("No dimensions with multiple values found. Cannot define conditions.")
        return False
    
    print("\nAvailable dimensions:")
    dim_list = list(available_for_conditions.keys())
    for i, dim in enumerate(dim_list, 1):
        values = available_for_conditions[dim]
        preview = ', '.join(values[:3])
        more = f" (and {len(values)-3} more)" if len(values) > 3 else ""
        print(f"{i}. {dim}: {len(values)} unique values - {preview}{more}")
    
    # Default to project_folder if available
    default_dim = 'project_folder' if 'project_folder' in available_for_conditions else dim_list[0]
    
    while True:
        user_input = input(f"\nEnter dimension number or name (default: {default_dim}): ").strip()
        
        if not user_input:
            self.condition_dimension = default_dim
            break
        elif user_input.isdigit() and 1 <= int(user_input) <= len(dim_list):
            self.condition_dimension = dim_list[int(user_input) - 1]
            break
        elif user_input in available_for_conditions:
            self.condition_dimension = user_input
            break
        else:
            print("Invalid selection. Please try again.")
    
    self.logger.info(f"Selected condition dimension: {self.condition_dimension}")
    print(f"\n✓ Using '{self.condition_dimension}' as experimental conditions")
    
    return True

def _select_dimension_values(self, dimension_key: str, prompt: str) -> bool:
    """Generic method to select values from a dimension.
    
    Args:
        dimension_key: Which dimension to select from (e.g., 'channel', 'timepoint')
        prompt: User-facing prompt text
    """
    # For conditions, use the chosen condition dimension
    if dimension_key == 'condition':
        actual_dimension = self.condition_dimension
    else:
        actual_dimension = dimension_key
    
    available = self.available_dimensions.get(actual_dimension, [])
    
    if not available:
        self.logger.warning(f"No {actual_dimension} values available")
        return True
    
    print("\n" + "="*80)
    print(prompt.upper())
    print("="*80)
    
    selected = self._handle_list_selection(available, actual_dimension, [])
    
    # Store in appropriate instance variable
    if dimension_key == 'condition':
        self.selected_conditions = selected
    
    return True

def _select_channels_flexible(self) -> bool:
    """Select channels for segmentation and analysis."""
    print("\n" + "="*80)
    print("STEP: SELECT CHANNELS")
    print("="*80)
    
    available_channels = self.available_dimensions.get('channel', [])
    
    # First select segmentation channel
    print("\nSelect the channel for SEGMENTATION (cell/nuclei detection):")
    print("This channel will be used to identify individual cells.")
    seg_channel = self._handle_list_selection(available_channels, "segmentation channel", [])
    if seg_channel:
        self.segmentation_channel = seg_channel[0]
        self.logger.info(f"Selected segmentation channel: {self.segmentation_channel}")
    
    # Then select analysis channels
    print("\nSelect channels for ANALYSIS:")
    print("These channels will be measured for each segmented cell.")
    self.analysis_channels = self._handle_list_selection(available_channels, "analysis channel", [])
    self.logger.info(f"Selected analysis channels: {self.analysis_channels}")
    
    return True

def _select_timepoints_flexible(self) -> bool:
    """Select timepoints to include in analysis."""
    print("\n" + "="*80)
    print("STEP: SELECT TIMEPOINTS")
    print("="*80)
    
    available = self.available_dimensions.get('timepoint', [])
    
    print(f"\nAvailable timepoints: {', '.join(available)}")
    print("Select which timepoints to include in analysis.")
    
    self.selected_timepoints = self._handle_list_selection(available, "timepoint", [])
    self.logger.info(f"Selected timepoints: {self.selected_timepoints}")
    
    return True

def _select_regions_flexible(self) -> bool:
    """Select regions to include in analysis."""
    print("\n" + "="*80)
    print("STEP: SELECT REGIONS (OPTIONAL)")
    print("="*80)
    
    available = self.available_dimensions.get('region', [])
    
    print(f"\nFound {len(available)} unique regions (base filenames):")
    for i, region in enumerate(available[:10], 1):
        print(f"  {i}. {region}")
    if len(available) > 10:
        print(f"  ... and {len(available) - 10} more")
    
    print("\nYou can select specific regions or press Enter to include all.")
    
    user_input = input("Select regions (or press Enter for all): ").strip()
    
    if not user_input:
        self.selected_regions = available
        print(f"✓ Including all {len(available)} regions")
    else:
        self.selected_regions = self._handle_list_selection(available, "region", [])
    
    self.logger.info(f"Selected {len(self.selected_regions)} regions")
    
    return True
```

---

### Task 3.5: Implement File Copying Method

**Add to DataSelectionStage**:

```python
def _create_flexible_output_directories(self) -> bool:
    """Create output directories based on selected conditions."""
    try:
        raw_data_dir = self.output_dir / "raw_data"
        raw_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a directory for each selected condition
        for condition in self.selected_conditions:
            condition_dir = raw_data_dir / condition
            condition_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {condition_dir}")
        
        return True
        
    except Exception as e:
        self.logger.error(f"Error creating output directories: {e}")
        return False

def _copy_filtered_files(self) -> bool:
    """Copy files based on flexible filters.
    
    Replaces _copy_selected_files for flexible mode.
    """
    try:
        self.logger.info("Filtering and copying files...")
        
        # Build filters from selections
        filters = {}
        
        # Add condition filter (using the chosen condition dimension)
        filters[self.condition_dimension] = self.selected_conditions
        
        # Add channel filter
        if self.analysis_channels:
            filters['channel'] = self.analysis_channels
        
        # Add timepoint filter
        if self.selected_timepoints:
            filters['timepoint'] = self.selected_timepoints
        
        # Add region filter
        if self.selected_regions and len(self.selected_regions) < len(self.available_dimensions.get('region', [])):
            filters['region'] = self.selected_regions
        
        self.logger.info(f"Applying filters: {filters}")
        
        # Filter files using flexible service
        filtered_files = self._flexible_selection.filter_files(
            self.discovered_files,
            filters
        )
        
        self.logger.info(f"Filtered to {len(filtered_files)} files")
        
        if not filtered_files:
            self.logger.error("No files match the selection criteria")
            return False
        
        # Copy files to output, organized by condition
        total_copied = 0
        raw_data_dir = self.output_dir / "raw_data"
        
        for file_path in filtered_files:
            # Find the corresponding metadata
            file_meta = None
            for fp, meta in self.discovered_files:
                if fp == file_path:
                    file_meta = meta
                    break
            
            if not file_meta:
                self.logger.warning(f"Could not find metadata for {file_path}")
                continue
            
            # Determine output path based on condition dimension
            condition_value = getattr(file_meta, self.condition_dimension, "unknown")
            output_dir = raw_data_dir / condition_value
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            output_path = output_dir / file_path.name
            
            fs_port = getattr(self, '_fs', None)
            if fs_port is not None:
                fs_port.copy(file_path, output_path, overwrite=True)
            else:
                from percell.adapters.local_filesystem_adapter import LocalFileSystemAdapter
                LocalFileSystemAdapter().copy(file_path, output_path, overwrite=True)
            
            total_copied += 1
            
            if total_copied % 50 == 0:
                self.logger.info(f"Copied {total_copied} files...")
        
        self.logger.info(f"Successfully copied {total_copied} files")
        
        if total_copied == 0:
            self.logger.error("No files were copied")
            return False
        
        return True
        
    except Exception as e:
        self.logger.error(f"Error copying filtered files: {e}")
        return False
```

---

### Task 3.6: Implement Config Save Method

**Add to DataSelectionStage**:

```python
def _save_flexible_selections_to_config(self):
    """Save flexible selections to config.
    
    Saves both in new flexible format and legacy format for compatibility.
    """
    try:
        # Save in flexible format
        self.config.set('data_selection.condition_dimension', self.condition_dimension)
        self.config.set('data_selection.dimension_filters', {
            self.condition_dimension: self.selected_conditions,
            'channel': self.analysis_channels,
            'timepoint': self.selected_timepoints,
            'region': self.selected_regions
        })
        
        # Also save in legacy format for backward compatibility
        self.config.set('data_selection.selected_conditions', self.selected_conditions)
        self.config.set('data_selection.selected_timepoints', self.selected_timepoints)
        self.config.set('data_selection.selected_regions', self.selected_regions)
        self.config.set('data_selection.segmentation_channel', self.segmentation_channel)
        self.config.set('data_selection.analysis_channels', self.analysis_channels)
        
        # Save metadata
        self.config.set('data_selection.experiment_metadata', self.experiment_metadata)
        self.config.set('data_selection.available_dimensions', self.available_dimensions)
        
        # Save the config
        self.config.save()
        
        self.logger.info("Flexible data selections saved to configuration")
        
    except Exception as e:
        self.logger.error(f"Error saving flexible selections to config: {e}")
```

---

## Phase 4: Testing

### Task 4.1: Create Test Fixtures

**Create directory structure**: `tests/fixtures/microscopy_data/`

**Fixture 1: Leica Export Style** (like the example)
```
tests/fixtures/microscopy_data/leica_export/
├── ProjectA/
│   ├── 18h treatment_Merged_z00_ch00.tif
│   ├── 18h treatment_Merged_z00_ch01.tif
│   ├── 3h treatment_Merged_z00_ch00.tif
│   └── 3h treatment_Merged_z00_ch01.tif
└── ProjectB/
    ├── 18h treatment_Merged_z00_ch00.tif
    └── 18h treatment_Merged_z00_ch01.tif
```

**Fixture 2: Standard Naming**
```
tests/fixtures/microscopy_data/standard_naming/
├── Condition1/
│   ├── region1_t0_ch0_z0.tif
│   ├── region1_t0_ch1_z0.tif
│   ├── region1_t1_ch0_z0.tif
│   └── region1_t1_ch1_z0.tif
└── Condition2/
    ├── region1_t0_ch0_z0.tif
    └── region1_t0_ch1_z0.tif
```

**Fixture 3: Nested Structure**
```
tests/fixtures/microscopy_data/nested_structure/
├── Project1/
│   ├── Replicate1/
│   │   ├── data_t0_ch0.tif
│   │   └── data_t0_ch1.tif
│   └── Replicate2/
│       ├── data_t0_ch0.tif
│       └── data_t0_ch1.tif
└── Project2/
    └── Replicate1/
        ├── data_t0_ch0.tif
        └── data_t0_ch1.tif
```

---

### Task 4.2: Create Unit Tests

**Create file**: `tests/unit/domain/test_flexible_data_selection_service.py`

```python
"""Unit tests for FlexibleDataSelectionService."""

import pytest
from pathlib import Path
from percell.domain.flexible_data_selection_service import FlexibleDataSelectionService
from percell.domain.models import FileMetadata


class TestFlexibleDataSelectionService:
    """Test flexible data selection service."""
    
    @pytest.fixture
    def service(self):
        return FlexibleDataSelectionService()
    
    @pytest.fixture
    def leica_fixture_dir(self):
        """Path to Leica-style test fixture."""
        return Path(__file__).parent.parent.parent / "fixtures" / "microscopy_data" / "leica_export"
    
    def test_discover_all_files_leica_structure(self, service, leica_fixture_dir):
        """Test file discovery with Leica export structure."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")
        
        files_meta = service.discover_all_files(leica_fixture_dir)
        
        # Should find all .tif files
        assert len(files_meta) > 0
        
        # Check that metadata is populated
        for file_path, meta in files_meta:
            assert meta.original_name is not None
            assert meta.project_folder is not None
            assert meta.full_path == file_path
    
    def test_get_available_dimensions_leica(self, service, leica_fixture_dir):
        """Test dimension extraction from Leica files."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")
        
        files_meta = service.discover_all_files(leica_fixture_dir)
        dimensions = service.get_available_dimensions(files_meta)
        
        # Should have multiple dimensions
        assert 'project_folder' in dimensions
        assert 'channel' in dimensions
        assert 'region' in dimensions
        
        # Check that dimensions are sorted
        if dimensions['channel']:
            assert dimensions['channel'] == sorted(dimensions['channel'])
    
    def test_group_files_by_project_folder(self, service, leica_fixture_dir):
        """Test grouping files by project folder."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")
        
        files_meta = service.discover_all_files(leica_fixture_dir)
        groups = service.group_files(files_meta, ['project_folder'])
        
        # Should have groups for each project folder
        assert len(groups) > 0
        
        # Each group should have files
        for group_key, files in groups.items():
            assert len(files) > 0
    
    def test_filter_files_by_channel(self, service, leica_fixture_dir):
        """Test filtering files by channel."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")
        
        files_meta = service.discover_all_files(leica_fixture_dir)
        dimensions = service.get_available_dimensions(files_meta)
        
        if not dimensions.get('channel'):
            pytest.skip("No channels found in test data")
        
        # Filter to first channel only
        first_channel = dimensions['channel'][0]
        filtered = service.filter_files(files_meta, {'channel': [first_channel]})
        
        # Should have fewer files than total
        assert len(filtered) < len(files_meta)
        assert len(filtered) > 0
    
    def test_filter_files_multiple_dimensions(self, service, leica_fixture_dir):
        """Test filtering by multiple dimensions."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")
        
        files_meta = service.discover_all_files(leica_fixture_dir)
        dimensions = service.get_available_dimensions(files_meta)
        
        filters = {}
        if dimensions.get('channel'):
            filters['channel'] = [dimensions['channel'][0]]
        if dimensions.get('project_folder'):
            filters['project_folder'] = [dimensions['project_folder'][0]]
        
        filtered = service.filter_files(files_meta, filters)
        
        # Should be more restrictive than single filter
        assert len(filtered) > 0
        
        # Verify all files match filters
        for file_path in filtered:
            meta = next(m for f, m in files_meta if f == file_path)
            for dim, values in filters.items():
                assert str(getattr(meta, dim)) in values
    
    def test_get_dimension_summary(self, service, leica_fixture_dir):
        """Test dimension summary generation."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")
        
        files_meta = service.discover_all_files(leica_fixture_dir)
        summary = service.get_dimension_summary(files_meta)
        
        # Should be a non-empty string
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Discovered" in summary
```

---

### Task 4.3: Create Enhanced Filename Parser Tests

**Create file**: `tests/unit/domain/test_file_naming_service_enhanced.py`

```python
"""Test enhanced filename parsing for various conventions."""

import pytest
from percell.domain.file_naming_service import FileNamingService


class TestEnhancedFileNaming:
    """Test parsing of various filename conventions."""
    
    @pytest.fixture
    def service(self):
        return FileNamingService()
    
    def test_parse_leica_style_filename(self, service):
        """Test parsing Leica export style filenames."""
        meta = service.parse_microscopy_filename("18h dTAG13_Merged_z00_ch00.tif")
        
        assert meta.region == "18h dTAG13_Merged"
        assert meta.channel == "ch00"
        assert meta.z_index == 0
        assert meta.extension == ".tif"
    
    def test_parse_leica_multiple_channels(self, service):
        """Test parsing different channels."""
        meta1 = service.parse_microscopy_filename("18h dTAG13_Merged_z00_ch00.tif")
        meta2 = service.parse_microscopy_filename("18h dTAG13_Merged_z00_ch01.tif")
        
        assert meta1.region == meta2.region
        assert meta1.channel == "ch00"
        assert meta2.channel == "ch01"
    
    def test_parse_region_with_spaces(self, service):
        """Test parsing regions with spaces in names."""
        meta = service.parse_microscopy_filename("No dTAG13_Merged_z00_ch00.tif")
        
        assert meta.region == "No dTAG13_Merged"
        assert meta.channel == "ch00"
    
    def test_parse_standard_naming(self, service):
        """Test parsing standard underscore-based naming."""
        meta = service.parse_microscopy_filename("region1_t0_ch1_z5.tif")
        
        assert meta.region == "region1"
        assert meta.timepoint == "t0"
        assert meta.channel == "ch1"
        assert meta.z_index == 5
    
    def test_parse_minimal_filename(self, service):
        """Test parsing filename with minimal metadata."""
        meta = service.parse_microscopy_filename("experiment_ch00.tif")
        
        assert meta.region == "experiment"
        assert meta.channel == "ch00"
        assert meta.timepoint is None
        assert meta.z_index is None
    
    def test_parse_with_timepoint(self, service):
        """Test parsing filename with timepoint."""
        meta = service.parse_microscopy_filename("data_t5_ch2.tif")
        
        assert meta.region == "data"
        assert meta.timepoint == "t5"
        assert meta.channel == "ch2"
    
    def test_parse_case_insensitive(self, service):
        """Test that parsing is case insensitive."""
        meta1 = service.parse_microscopy_filename("data_CH00_T0.tif")
        meta2 = service.parse_microscopy_filename("data_ch00_t0.tif")
        
        assert meta1.channel == meta2.channel
        assert meta1.timepoint == meta2.timepoint
```

---

### Task 4.4: Create Integration Test

**Create file**: `tests/integration/test_flexible_data_selection_stage.py`

```python
"""Integration tests for flexible data selection stage."""

import pytest
from pathlib import Path
from percell.application.stages.data_selection_stage import DataSelectionStage
from percell.config.config import Config
import logging


class TestFlexibleDataSelectionStage:
    """Test the complete flexible data selection workflow."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create a test config."""
        config = Config()
        config.set('data_selection.use_flexible_selection', True)
        return config
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return logging.getLogger('test')
    
    @pytest.fixture
    def leica_fixture_dir(self):
        """Path to Leica test fixture."""
        return Path(__file__).parent.parent / "fixtures" / "microscopy_data" / "leica_export"
    
    def test_discover_files_and_dimensions(self, config, logger, leica_fixture_dir, tmp_path):
        """Test file and dimension discovery."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")
        
        stage = DataSelectionStage(config, logger)
        stage.input_dir = leica_fixture_dir
        stage.output_dir = tmp_path / "output"
        
        # Run discovery
        success = stage._discover_files_and_dimensions()
        
        assert success is True
        assert len(stage.discovered_files) > 0
        assert len(stage.available_dimensions) > 0
        assert 'project_folder' in stage.available_dimensions
    
    def test_flexible_workflow_programmatic(self, config, logger, leica_fixture_dir, tmp_path):
        """Test flexible workflow with programmatic selections (no user input)."""
        if not leica_fixture_dir.exists():
            pytest.skip("Test fixture not found")
        
        stage = DataSelectionStage(config, logger)
        stage.input_dir = leica_fixture_dir
        stage.output_dir = tmp_path / "output"
        
        # Discover files
        stage._discover_files_and_dimensions()
        
        # Make programmatic selections
        stage.condition_dimension = 'project_folder'
        stage.selected_conditions = stage.available_dimensions['project_folder'][:1]  # First project only
        
        if stage.available_dimensions.get('channel'):
            stage.analysis_channels = [stage.available_dimensions['channel'][0]]
            stage.segmentation_channel = stage.available_dimensions['channel'][0]
        
        if stage.available_dimensions.get('timepoint'):
            stage.selected_timepoints = stage.available_dimensions['timepoint']
        
        stage.selected_regions = stage.available_dimensions.get('region', [])
        
        # Create output directories
        success = stage._create_flexible_output_directories()
        assert success is True
        
        # Copy files
        success = stage._copy_filtered_files()
        assert success is True
        
        # Verify files were copied
        raw_data_dir = stage.output_dir / "raw_data"
        assert raw_data_dir.exists()
        
        # Check that at least one file was copied
        copied_files = list(raw_data_dir.rglob("*.tif"))
        assert len(copied_files) > 0
```

---

## Phase 5: Documentation

### Task 5.1: Update User Documentation

**Create file**: `docs/flexible_data_selection.md`

```markdown
# Flexible Data Selection

PerCell now supports flexible file organization! You no longer need to organize your microscopy data in a specific directory structure.

## Requirements

The only hard requirement is:
- **Root directory contains project folders** (first level subdirectories)
- **Files follow basic naming conventions** with identifiable channels, timepoints, and z-slices

## Supported Naming Conventions

PerCell automatically recognizes these patterns in filenames:

### Channels
- `ch00`, `ch01`, `ch02`, ... (case insensitive)
- `_ch0`, `_ch1`, `_ch2`, ...
- Can appear anywhere in the filename

### Timepoints
- `t0`, `t1`, `t2`, ... (case insensitive)
- `_t0`, `_t1`, `_t2`, ...
- Can appear anywhere in the filename

### Z-slices
- `z00`, `z01`, `z02`, ... (case insensitive)
- `_z0`, `_z1`, `_z2`, ...
- Can appear anywhere in the filename

## Example Directory Structures

### Leica Export Style
```
my_experiment/
├── Project A/
│   ├── 18h treatment_Merged_z00_ch00.tif
│   ├── 18h treatment_Merged_z00_ch01.tif
│   ├── 3h treatment_Merged_z00_ch00.tif
│   └── 3h treatment_Merged_z00_ch01.tif
└── Project B/
    ├── 18h treatment_Merged_z00_ch00.tif
    └── 18h treatment_Merged_z00_ch01.tif
```

### Standard Naming
```
my_experiment/
├── Control/
│   ├── region1_t0_ch0_z0.tif
│   ├── region1_t0_ch1_z0.tif
│   └── region1_t1_ch0_z0.tif
└── Treatment/
    ├── region1_t0_ch0_z0.tif
    └── region1_t0_ch1_z0.tif
```

### Nested Structure
```
my_experiment/
├── Experiment1/
│   ├── Replicate1/
│   │   ├── data_t0_ch0.tif
│   │   └── data_t0_ch1.tif
│   └── Replicate2/
│       └── data_t0_ch0.tif
└── Experiment2/
    └── data_t0_ch0.tif
```

## How It Works

1. **File Discovery**: PerCell scans your root directory recursively for all `.tif` and `.tiff` files

2. **Metadata Extraction**: For each file, PerCell extracts:
   - Project folder (first directory level)
   - Region/dataset name (base filename without ch/t/z markers)
   - Channel, timepoint, and z-slice from filename patterns

3. **Dimension Discovery**: PerCell identifies all unique values for each dimension:
   - Project folders
   - Regions (unique base filenames)
   - Channels
   - Timepoints
   - Z-slices

4. **Interactive Selection**: You choose:
   - Which dimension represents your "conditions" (usually project folders)
   - Which conditions to analyze
   - Which channels, timepoints, and regions to include

5. **Smart Filtering**: Files are filtered and copied based on your selections

## Interactive Workflow

When you run data selection, you'll be guided through these steps:

### Step 1: Define Conditions
Choose which dimension represents your experimental conditions:
```
Which dimension represents your experimental conditions?

Available dimensions:
1. project_folder: 2 unique values - ProjectA, ProjectB
2. region: 3 unique values - 18h treatment_Merged, 3h treatment_Merged, No treatment_Merged

Enter dimension number or name (default: project_folder):
```

### Step 2: Select Conditions
Choose which condition values to analyze:
```
Select project_folders to analyze:
1. ProjectA
2. ProjectB

Enter selection (numbers, names, or 'all'): all
```

### Step 3: Select Channels
Choose segmentation and analysis channels:
```
Select the channel for SEGMENTATION:
1. ch00
2. ch01

Enter selection: 1

Select channels for ANALYSIS:
1. ch00
2. ch01

Enter selection: all
```

### Step 4: Select Timepoints (if applicable)
Choose which timepoints to include:
```
Available timepoints: t0, t1, t2

Enter selection: all
```

### Step 5: Select Regions (optional)
Filter to specific regions if needed:
```
Found 3 unique regions (base filenames):
  1. 18h treatment_Merged
  2. 3h treatment_Merged
  3. No treatment_Merged

Select regions (or press Enter for all):
```

## Configuration

### Enable/Disable Flexible Selection

In your config file (`config.yaml`):

```yaml
data_selection:
  use_flexible_selection: true  # Set to false for legacy behavior
```

### Legacy Mode

If you have existing workflows that depend on specific directory structures, you can use legacy mode:

```yaml
data_selection:
  use_flexible_selection: false
```

Legacy mode expects:
- Condition directories at the first level
- Timepoint directories inside condition directories
- Specific naming patterns

## Troubleshooting

### No files found
- Check that your files have `.tif` or `.tiff` extensions
- Verify that at least one project folder exists under your root directory
- Check file permissions

### Files not parsing correctly
- Ensure filenames contain `ch`, `t`, or `z` markers for channels, timepoints, and z-slices
- Markers can be uppercase or lowercase
- Markers can have underscore prefixes or not

### Missing dimensions
If a dimension doesn't appear in the discovery:
- Verify the naming pattern in your files
- Check that multiple unique values exist (dimensions with only one value may not be useful for selection)

## Examples

### Example 1: Leica Direct Export
```bash
# Input directory structure (direct from microscope)
2025-10-16_export/
├── Clone 1/
│   ├── 18h dTAG13_Merged_z00_ch00.tif
│   └── 18h dTAG13_Merged_z00_ch01.tif
└── Clone 2/
    ├── 18h dTAG13_Merged_z00_ch00.tif
    └── 18h dTAG13_Merged_z00_ch01.tif

# PerCell discovers:
# - project_folder: Clone 1, Clone 2
# - region: 18h dTAG13_Merged
# - channel: ch00, ch01
# - z_index: 0

# You select:
# - condition_dimension: project_folder
# - conditions: Clone 1, Clone 2
# - segmentation_channel: ch00
# - analysis_channels: ch00, ch01
```

### Example 2: Complex Nested Structure
```bash
# Input directory structure (organized by researcher)
my_experiment/
├── Batch1/
│   ├── Controls/
│   │   ├── sample1_t0_ch0.tif
│   │   └── sample1_t0_ch1.tif
│   └── Treated/
│       ├── sample1_t0_ch0.tif
│       └── sample1_t0_ch1.tif
└── Batch2/
    └── Controls/
        ├── sample2_t0_ch0.tif
        └── sample2_t0_ch1.tif

# PerCell discovers:
# - project_folder: Batch1, Batch2
# - region: sample1, sample2
# - channel: ch0, ch1
# - timepoint: t0

# Option A: Use project folders as conditions
# - Compares Batch1 vs Batch2

# Option B: Group by region first, then use project folder
# - Compares samples across batches
```

## Migration from Legacy Mode

If you're migrating from legacy data selection:

1. **Your data still works!** The legacy mode is fully supported.

2. **To try flexible mode:**
   - Set `use_flexible_selection: true` in config
   - Run data selection as normal
   - The system will discover your existing structure

3. **Benefits of switching:**
   - Work with export formats directly
   - Less manual file reorganization
   - More flexible condition definitions

4. **Backward compatibility:**
   - Your existing config values are preserved
   - The system writes both old and new formats
   - Other pipeline stages work the same way
```

---

### Task 5.2: Create Migration Guide

**Create file**: `docs/MIGRATION_FLEXIBLE_SELECTION.md`

```markdown
# Migration Guide: Flexible Data Selection

This guide helps you migrate to the new flexible data selection system.

## What Changed?

### Before (Legacy Mode)
- Required specific directory structure:
  - `root/condition/timepoint/files.tif`
- Expected specific filename patterns
- Made assumptions about what "condition" means

### After (Flexible Mode)
- Works with any directory structure
- Only requires project folders at first level
- Discovers dimensions from filenames
- User defines what "condition" means

## Do I Need to Migrate?

**No!** Legacy mode still works perfectly. Migrate only if:
- You want to use microscope export formats directly
- You need more flexible organization
- You want to define custom groupings

## Migration Steps

### Step 1: Backup Your Config

```bash
cp config.yaml config.yaml.backup
```

### Step 2: Enable Flexible Mode

Edit `config.yaml`:
```yaml
data_selection:
  use_flexible_selection: true
```

### Step 3: Test with Sample Data

Run data selection on a small dataset first:
```bash
percell select-data --input /path/to/sample --output /path/to/output
```

### Step 4: Verify Results

Check that:
- All expected files were discovered
- Dimensions were correctly extracted
- Output structure matches expectations

### Step 5: Update Your Workflow

If you have scripts that:
- Assume specific directory structures
- Parse config in specific ways
- Check for specific metadata fields

Update them to use the new flexible fields:
```yaml
# Old format (still supported)
selected_conditions: [...]
selected_timepoints: [