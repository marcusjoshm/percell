# Workflow Configuration System

This document describes the centralized workflow configuration system in Percell, which provides a single source of truth for tool selection across the entire application.

## Overview

The `WorkflowConfigurationService` manages which tools are used at each stage of the microscopy analysis workflow. All parts of the application reference this service to determine the correct stages to execute.

## Architecture

### Core Components

1. **WorkflowConfigurationService** (`percell/domain/services/workflow_configuration_service.py`)
   - Central service managing workflow tool selection
   - Provides methods to get/set tools for each workflow stage
   - Validates tool selections
   - Returns configured stage names and display names

2. **Stage Implementations** (`percell/application/stages/`)
   - Individual stage classes (e.g., `SegmentationStage`, `ThresholdGroupedCellsStage`)
   - Each stage has a unique `stage_name` used for registration

3. **Configuration Storage** (`config.json`)
   - Persistent storage of workflow configuration
   - Located at `percell/config/config.json`

## Current Workflow Stages

The complete workflow consists of these configurable stages:

| Stage Category | Configuration Key | Available Tools | Stage Names |
|----------------|------------------|-----------------|-------------|
| **Segmentation** | `workflow.segmentation_tool` | `cellpose` | `cellpose_segmentation` |
| **Processing** | `workflow.processing_tool` | `cellpose` | `process_cellpose_single_cell` |
| **Thresholding** | `workflow.thresholding_tool` | `semi_auto`, `full_auto` | `semi_auto_threshold_grouped_cells`, `full_auto_threshold_grouped_cells` |
| Data Selection | N/A | N/A | `data_selection` |
| ROI Measurement | N/A | N/A | `measure_roi_area` |
| Analysis | N/A | N/A | `analysis` |

## Using the Workflow Configuration

### For End Users

#### Via Interactive Menu

1. Launch Percell in interactive mode
2. Navigate to: **Main Menu → Configuration → Workflow Configuration**
3. Select the workflow stage to configure (Segmentation, Processing, or Thresholding)
4. Choose your preferred tool from the available options
5. Configuration is saved automatically

#### Via Configuration File

Edit `percell/config/config.json`:

```json
{
  "workflow": {
    "segmentation_tool": "cellpose",
    "processing_tool": "cellpose",
    "thresholding_tool": "full_auto"
  }
}
```

### For Developers

#### Accessing Workflow Configuration in Code

```python
from percell.domain.services import create_workflow_configuration_service
from percell.domain.services.configuration_service import create_configuration_service

# Create services
config = create_configuration_service("path/to/config.json")
workflow_config = create_workflow_configuration_service(config)

# Get configured tools
seg_tool = workflow_config.get_segmentation_tool()  # Returns 'cellpose'
thresh_tool = workflow_config.get_thresholding_tool()  # Returns 'semi_auto' or 'full_auto'

# Get stage names for execution
seg_stage = workflow_config.get_segmentation_stage_name()  # Returns 'cellpose_segmentation'
thresh_stage = workflow_config.get_thresholding_stage_name()  # Returns 'semi_auto_threshold_grouped_cells'

# Get display names for UI
seg_display = workflow_config.get_segmentation_display_name()  # Returns 'Cellpose'
thresh_display = workflow_config.get_thresholding_display_name()  # Returns 'Semi-Auto Threshold'

# Get complete workflow stages
stages = workflow_config.get_complete_workflow_stages()
# Returns: [('data_selection', 'Data Selection'),
#           ('cellpose_segmentation', 'Cellpose'),
#           ...]
```

#### Querying Available Tools

```python
# Get all available tools for a stage
seg_tools = workflow_config.get_available_segmentation_tools()
# Returns: {'cellpose': WorkflowTool(...)}

thresh_tools = workflow_config.get_available_thresholding_tools()
# Returns: {'semi_auto': WorkflowTool(...), 'full_auto': WorkflowTool(...)}

# Get workflow summary
summary = workflow_config.get_workflow_summary()
# Returns: {'segmentation': 'Cellpose', 'processing': 'Cellpose Processing',
#           'thresholding': 'Semi-Auto Threshold'}
```

## Adding New Tools

### Step 1: Implement the Stage Class

Create a new stage class in `percell/application/stages/`:

```python
from percell.application.stages_api import StageBase

class NewToolStage(StageBase):
    def __init__(self, config, logger, stage_name="new_tool_stage"):
        super().__init__(config, logger, stage_name)

    def validate_inputs(self, **kwargs) -> bool:
        # Validate prerequisites
        return True

    def run(self, **kwargs) -> bool:
        # Implement tool logic
        return True
```

### Step 2: Register the Stage

Add to `percell/application/stage_registry.py`:

```python
from percell.application.stages import NewToolStage

def register_all_stages():
    # ... existing registrations ...
    register_stage('new_tool_stage', order=10)(NewToolStage)
```

Export from `percell/application/stages/__init__.py`:

```python
from percell.application.stages.new_tool_stage import NewToolStage

__all__ = [
    # ... existing exports ...
    "NewToolStage",
]
```

### Step 3: Add to WorkflowConfigurationService

Update `percell/domain/services/workflow_configuration_service.py`:

```python
class WorkflowConfigurationService:
    # Add to the appropriate tool category
    THRESHOLDING_TOOLS = {
        'semi_auto': WorkflowTool(...),
        'full_auto': WorkflowTool(...),
        'new_tool': WorkflowTool(
            stage_name='new_tool_stage',
            display_name='New Tool',
            description='Description of the new tool'
        ),
    }
```

### Step 4: Update Configuration Menu (Optional)

The menu system automatically picks up new tools from `WorkflowConfigurationService`, so no changes are needed unless you want custom UI behavior.

### Step 5: Test

```bash
# Test that the new tool appears in the menu
percell --interactive

# Test CLI access
percell --new-tool-stage --input /path --output /path
```

## Example: Adding a New Segmentation Tool

Let's say you want to add support for a new segmentation tool called "StarDist":

### 1. Create the Stage

```python
# percell/application/stages/stardist_segmentation_stage.py
class StarDistSegmentationStage(StageBase):
    def __init__(self, config, logger, stage_name="stardist_segmentation"):
        super().__init__(config, logger, stage_name)

    def run(self, **kwargs) -> bool:
        # Implement StarDist segmentation
        pass
```

### 2. Register

```python
# In stage_registry.py
register_stage('stardist_segmentation', order=3)(StarDistSegmentationStage)
```

### 3. Add to WorkflowConfigurationService

```python
# In workflow_configuration_service.py
SEGMENTATION_TOOLS = {
    'cellpose': WorkflowTool(
        stage_name='cellpose_segmentation',
        display_name='Cellpose',
        description='SAM-based segmentation using Cellpose'
    ),
    'stardist': WorkflowTool(
        stage_name='stardist_segmentation',
        display_name='StarDist',
        description='Star-convex polygon segmentation'
    ),
}
```

### 4. Add CLI Argument

```python
# In cli_parser.py
parser.add_argument('--stardist-segmentation', action='store_true',
                   help='Run StarDist segmentation')
```

### 5. Update Pipeline

```python
# In pipeline_api.py
if getattr(self.args, "stardist_segmentation", False):
    stages.append("stardist_segmentation")
```

That's it! The tool is now:
- Available in the Workflow Configuration menu
- Usable via CLI (`--stardist-segmentation`)
- Automatically used by CompleteWorkflowStage when configured
- Visible in AdvancedWorkflowStage

## Best Practices

### 1. Always Use WorkflowConfigurationService

❌ **Don't hardcode stage names:**
```python
# Bad
stage_name = "cellpose_segmentation"
```

✅ **Do use WorkflowConfigurationService:**
```python
# Good
from percell.domain.services import create_workflow_configuration_service
workflow_config = create_workflow_configuration_service(config)
stage_name = workflow_config.get_segmentation_stage_name()
```

### 2. Consistent Naming Convention

Stage names should follow the pattern: `{tool}_{stage_type}`

Examples:
- `cellpose_segmentation`
- `stardist_segmentation`
- `semi_auto_threshold_grouped_cells`
- `full_auto_threshold_grouped_cells`

### 3. Tool Keys Should Be Simple

Use simple, lowercase keys without underscores:

✅ Good: `cellpose`, `stardist`, `semiauto`, `fullauto`
❌ Bad: `cellpose_tool`, `StarDist`, `semi-auto`

### 4. Descriptive Display Names

Display names should be human-readable and match common usage:
- "Cellpose" not "cellpose"
- "Semi-Auto Threshold" not "semi_auto"

### 5. Always Validate Configuration

The `WorkflowConfigurationService` automatically validates tool selections. Use its setter methods rather than setting config directly:

```python
# Good - validates that tool exists
workflow_config.set_thresholding_tool('full_auto')

# Bad - no validation
config.set('workflow.thresholding_tool', 'invalid_tool')
```

## Migration Guide

If you have existing code that references specific stage names, update it to use `WorkflowConfigurationService`:

### Before

```python
stages = [
    ('data_selection', 'Data Selection'),
    ('cellpose_segmentation', 'Cellpose Segmentation'),
    ('semi_auto_threshold_grouped_cells', 'Threshold'),
]
```

### After

```python
from percell.domain.services import create_workflow_configuration_service

workflow_config = create_workflow_configuration_service(config)
stages = workflow_config.get_complete_workflow_stages()
```

## Troubleshooting

### Tool Not Appearing in Menu

1. Check that the tool is defined in `WorkflowConfigurationService`
2. Verify the stage is registered in `stage_registry.py`
3. Ensure the stage class is exported from `__init__.py`

### Configuration Not Persisting

1. Check file permissions on `config.json`
2. Verify `workflow_config.set_*_tool()` is being called (includes `config.save()`)
3. Check for exceptions in the configuration service

### Stage Not Executing

1. Verify the stage is registered with correct name
2. Check that `workflow_config.get_*_stage_name()` returns the expected value
3. Look for validation errors in stage's `validate_inputs()` method

## Future Extensions

The workflow configuration system is designed to be easily extended:

1. **Multi-Tool Workflows**: Support running multiple tools in parallel
2. **Tool Parameters**: Add per-tool configuration options
3. **Conditional Workflows**: Select tools based on data characteristics
4. **Plugin System**: Allow external tools to register themselves
5. **Workflow Templates**: Save and load entire workflow configurations

## Summary

The centralized `WorkflowConfigurationService` provides:

✅ **Single Source of Truth** - All code references the same configuration
✅ **Easy Extension** - Add new tools in 5 simple steps
✅ **Type Safety** - Validated tool selections
✅ **User-Friendly** - Interactive menu and persistent configuration
✅ **Developer-Friendly** - Clean API for programmatic access

For questions or contributions, please refer to the main project documentation.
