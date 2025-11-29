# Changelog

All notable changes to PerCell will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Comprehensive Plugin System** - New plugin architecture for extending PerCell functionality
  - Plugin base classes and interfaces (`PerCellPlugin`, `PluginMetadata`)
  - Automatic plugin discovery and registration system
  - Lazy plugin instantiation for improved performance
  - Plugin template generator (`python -m percell.plugins.template_generator`)
  - Script-to-plugin converter (`python -m percell.plugins.converter`)
  - Legacy plugin adapter for backward compatibility
  - AST-based plugin discovery for handling missing dependencies
  - Integration with PerCell services (ImageJ, filesystem, Cellpose, image processor)
  - Automatic menu integration - plugins appear in Plugins menu automatically
  - Plugin validation system for checking requirements before execution
  - Comprehensive documentation (Plugin Guide, Development Guide, API Reference)
  - 48 unit tests for plugin system core functionality

- **Plugin Examples**
  - Auto Image Preprocessing Plugin (legacy wrapper)
  - Intensity Analysis Plugin (full conversion from script)

### Changed
- Plugins menu now dynamically populated from plugin registry
- Logging improvements in `imagej_tasks.py` for better debugging

### Documentation
- Added `docs/PLUGIN_GUIDE.md` - Comprehensive plugin development guide
- Added `docs/PLUGIN_DEVELOPMENT.md` - Detailed development documentation
- Added `PLUGIN_SYSTEM_README.md` - Quick reference guide
- Added `FEATURE_SUMMARY.md` - Plugin system feature summary
- Added `CONVERSION_SUMMARY.md` - Script conversion guide

### Developer Experience
- Plugin template generator for quick plugin scaffolding
- Script converter for migrating existing scripts to plugins
- Extensive inline documentation and type hints
- Clear error messages and validation feedback

### Tests
- Added `tests/unit/plugins/test_plugin_registry.py` - Registry and discovery tests
- Added `tests/unit/plugins/test_template_generator.py` - Template generator tests
- Added `tests/unit/plugins/test_plugin_execution.py` - Execution and validation tests

---

## [Previous Versions]

(Add previous version history here as needed)
