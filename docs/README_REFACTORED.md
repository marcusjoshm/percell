11
# Microscopy Single-Cell Analysis Pipeline - Refactored

This refactoring introduces clear architectural layers, a pluggable analysis system, and optional event-driven orchestration. It reduces coupling across modules and makes it easier to add features and tests.

## New Architecture

High-level layering:

```
Application (CLI)
├── Services (orchestration, plugin manager, event bus)
├── Domain (business logic contracts, plugin interfaces)
├── Infrastructure (external tools, file I/O adapters)
└── Core (config, logging, pipeline, stage framework)
```

Repository layout (key folders):

```
percell/
├── percell/
│   ├── core/            # Config, logger, pipeline, stages
│   ├── domain/          # AnalysisPlugin interface and context/result models
│   ├── services/        # PluginManager, PipelineEventBus, future factories
│   ├── infrastructure/  # FileService, ImageJService, external adapters
│   ├── plugins/         # Built-in plugins and registry
│   ├── cli/             # CLI adapter (re-exports core CLI)
│   └── modules/         # Existing stage implementations and registry (legacy)
├── docs/
└── tests/
```

## Key Features

### 1. Modular Architecture
- **Clean boundaries**: Core vs. Domain vs. Services vs. Infrastructure
- **Extensible stage system**: Stages registered via `modules.stage_registry`
- **Plugin-ready**: Standard `AnalysisPlugin` interface + `PluginManager`
- **Event-driven orchestration**: Optional `PipelineEventBus` for decoupled notifications
- **Configuration management**: Centralized JSON with validation

### 2. Stage and Plugin Overview
- Stages: Operational workflow steps executed by `StageExecutor`
- Plugins: Extensible analysis units implementing `AnalysisPlugin`
- Both can coexist. Existing stages remain under `percell/modules`; plugins live under `percell/plugins`.

### 3. Command-Line Interface

#### Basic Usage
```bash
# Run complete pipeline
python -m percell.main.main --input /path/to/data --output /path/to/output --complete-workflow

# Run selected stages
python -m percell.main.main --input /path/to/data --output /path/to/output --analysis

# Interactive menu
python -m percell.main.main --interactive
```

#### Advanced Options
```bash
# Specify data type and channels
python -m percell.main.main --input ... --output ... --complete-workflow \
  --datatype single_timepoint \
  --segmentation-channel ch00 \
  --analysis-channels ch01 ch02 \
  --bins 5

# Skip steps / start from specific
python -m percell.main.main --input ... --output ... --complete-workflow --skip-steps analysis
python -m percell.main.main --input ... --output ... --complete-workflow --start-from analysis

# Verbose logging
python -m percell.main.main --input ... --output ... --complete-workflow --verbose
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
- **Plugin architecture**: Analysis plugins registered via `PluginManager`
- **Configuration-driven**: Behavior controlled through config files

### 3. Reliability
- **Comprehensive logging**: Detailed execution tracking
- **Error handling**: Robust error reporting and recovery
- **Validation**: Input validation at multiple levels

### 4. Usability
- **Interactive mode**: User-friendly interactive interface
- **Flexible CLI**: Multiple ways to specify parameters
- **Progress tracking**: Real-time progress updates

## Dependency Injection (DI) and Event Bus

- DI-friendly constructors for stages: `StageBase(config, logger, stage_name, event_bus=None)`
- `StageExecutor` accepts `event_bus` and passes it to each stage it constructs
- `PipelineEventBus` publishes `StageStarted` and `StageCompleted` events for decoupled observers

## Development

### Adding New Stages (legacy stage system)
1. Implement your stage in `percell/modules/stage_classes.py` deriving from `StageBase`
2. Register it in `percell/modules/stage_registry.py` using `register_stage('name', order=N)`
3. Add CLI flags in `percell/core/cli.py` if needed

### Writing a Plugin
1. Implement `AnalysisPlugin` in `percell/plugins/your_plugin.py`
```python
from percell.domain.plugin import AnalysisPlugin, AnalysisContext, AnalysisResult

class MyPlugin(AnalysisPlugin):
    @property
    def name(self) -> str:
        return 'my_plugin'

    def validate_inputs(self, context: AnalysisContext) -> bool:
        return True

    def process(self, context: AnalysisContext) -> AnalysisResult:
        return AnalysisResult(success=True, details={'ok': True})
```
2. Register it via `percell/plugins/registry.py` or at runtime using `PluginManager.register_plugin()`

### Services (use instead of direct subprocess where practical)
- `percell.infrastructure.FileService`
- `percell.infrastructure.ImageJService`

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
3. **Plugin system**: Third-party plugins discoverable and configurable
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