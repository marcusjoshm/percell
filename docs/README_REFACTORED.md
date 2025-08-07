# Microscopy Single-Cell Analysis Pipeline - Refactored

This is the refactored version of the microscopy single-cell analysis pipeline, featuring a modular command-line interface architecture inspired by the FLIM-FRET analysis project.

## New Architecture

The project has been refactored to follow a more modular and maintainable structure:

```
microscopy-analysis-single-cell/
├── main.py                          # Main entry point
├── src/                             # Source code directory
│   └── python/                      # Python modules
│       ├── core/                    # Core framework
│       │   ├── cli.py              # Command-line interface
│       │   ├── config.py           # Configuration management
│       │   ├── logger.py           # Logging framework
│       │   ├── pipeline.py         # Pipeline orchestrator
│       │   └── stages.py           # Stage execution framework
│       └── modules/                 # Pipeline modules
│           ├── stage_registry.py    # Stage registration
│           └── stage_classes.py     # Stage implementations
├── scripts/                         # Original analysis scripts
├── macros/                          # ImageJ macros
└── config/                          # Configuration directory
    ├── config.json                  # Main configuration file
    └── config.template.json         # Configuration template
```

## Key Features

### 1. Modular CLI Architecture
- **Clean separation of concerns**: Each component has a specific responsibility
- **Extensible stage system**: Easy to add new pipeline stages
- **Comprehensive logging**: Detailed execution tracking and error reporting
- **Configuration management**: Centralized configuration with validation

### 2. Pipeline Stages
The pipeline is divided into three main stages:

1. **Preprocessing** (`--preprocess`)
   - Data organization and file preparation
   - Image binning and preprocessing
   - Directory structure setup

2. **Segmentation** (`--segment`)
   - Cell segmentation using Cellpose
   - ROI creation and management
   - Mask generation

3. **Analysis** (`--analyze`)
   - Cell grouping and analysis
   - Otsu thresholding
   - Result generation

### 3. Command-Line Interface

#### Basic Usage
```bash
# Run complete pipeline
python main.py --input /path/to/data --output /path/to/output --complete

# Run individual stages
python main.py --input /path/to/data --output /path/to/output --preprocess
python main.py --input /path/to/data --output /path/to/output --segment
python main.py --input /path/to/data --output /path/to/output --analyze

# Interactive mode
python main.py --interactive
```

#### Advanced Options
```bash
# Specify data type and channels
python main.py --input /path/to/data --output /path/to/output --complete \
    --datatype single_timepoint \
    --segmentation-channel ch00 \
    --analysis-channels ch01 ch02 \
    --bins 5

# Skip specific steps
python main.py --input /path/to/data --output /path/to/output --complete \
    --skip-steps preprocessing

# Start from specific stage
python main.py --input /path/to/data --output /path/to/output --complete \
    --start-from segmentation

# Verbose logging
python main.py --input /path/to/data --output /path/to/output --complete --verbose
```

## Configuration

The pipeline uses a JSON configuration file (`config/config.json`) for settings:

```json
{
  "imagej_path": "/Applications/ImageJ.app",
  "cellpose_path": "/path/to/cellpose",
  "python_path": "/usr/bin/python3",
  "analysis": {
    "default_bins": 5,
    "segmentation_model": "cyto",
    "cell_diameter": 100,
    "niter_dynamics": 250,
    "flow_threshold": 0.4,
    "cellprob_threshold": 0
  },
  "output": {
    "create_subdirectories": true,
    "save_intermediate": true,
    "compression": "lzw",
    "overwrite": false
  }
}
```

## Benefits of the Refactored Architecture

### 1. Maintainability
- **Clear separation**: Each component has a single responsibility
- **Modular design**: Easy to modify or extend individual components
- **Type hints**: Better code documentation and IDE support

### 2. Extensibility
- **Stage system**: Easy to add new pipeline stages
- **Plugin architecture**: Stages can be registered dynamically
- **Configuration-driven**: Behavior controlled through config files

### 3. Reliability
- **Comprehensive logging**: Detailed execution tracking
- **Error handling**: Robust error reporting and recovery
- **Validation**: Input validation at multiple levels

### 4. Usability
- **Interactive mode**: User-friendly interactive interface
- **Flexible CLI**: Multiple ways to specify parameters
- **Progress tracking**: Real-time progress updates

## Migration from Original Pipeline

The refactored pipeline maintains compatibility with the original workflow while providing additional features:

### Original Command
```bash
python single_cell_workflow.py --config config/config.json --input /path/to/data --output /path/to/output
```

### New Command
```bash
python main.py --input /path/to/data --output /path/to/output --complete
```

### Key Differences
1. **Simplified interface**: No need to specify config file (uses default)
2. **Stage-specific execution**: Can run individual stages
3. **Better error handling**: More informative error messages
4. **Progress tracking**: Real-time progress updates
5. **Interactive mode**: User-friendly interactive interface

## Development

### Adding New Stages
To add a new pipeline stage:

1. Create a new stage class in `src/python/modules/stage_classes.py`:
```python
class NewStage(StageBase):
    def validate_inputs(self, **kwargs) -> bool:
        # Validate inputs
        pass
    
    def run(self, **kwargs) -> bool:
        # Implement stage logic
        pass
```

2. Register the stage in `src/python/modules/stage_registry.py`:
```python
register_stage('new_stage', order=4)(NewStage)
```

3. Add CLI options in `src/python/core/cli.py`:
```python
parser.add_argument(
    '--new-stage',
    action='store_true',
    help='Run new stage only'
)
```

### Configuration Management
The configuration system supports:
- **Nested keys**: Use dot notation (e.g., `analysis.default_bins`)
- **Validation**: Automatic validation of required settings
- **Defaults**: Sensible defaults for all settings
- **Detection**: Automatic detection of software paths

## Logging

The pipeline provides comprehensive logging:

- **Console output**: Real-time progress updates
- **File logging**: Detailed logs saved to `logs/` directory
- **Error tracking**: Separate error log files
- **Execution summary**: JSON summary of pipeline execution

## Future Enhancements

The modular architecture enables several future enhancements:

1. **Parallel processing**: Multi-threaded stage execution
2. **Web interface**: Web-based pipeline management
3. **Plugin system**: Third-party stage plugins
4. **Cloud integration**: Cloud-based processing
5. **Real-time monitoring**: Live pipeline monitoring

## Contributing

When contributing to the refactored pipeline:

1. **Follow the architecture**: Use the stage system for new features
2. **Add tests**: Include unit tests for new functionality
3. **Update documentation**: Keep README and docstrings current
4. **Use type hints**: Maintain code quality with type annotations
5. **Follow logging**: Use the logging framework for all output

## Support

For issues with the refactored pipeline:
- Check the logs in the `logs/` directory
- Use `--verbose` for detailed output
- Review the configuration file
- Check the original scripts in the `scripts/` directory 