# PerCell Documentation

This directory contains all PerCell documentation organized by topic.

## Directory Structure

### 📚 [setup/](setup/)
Installation and setup guides
- [Getting Started](setup/Getting_Started.md) - Quick start guide
- [Quick Start](setup/QUICK_START.md) - Fast setup instructions  
- [Global Installation](setup/GLOBAL_INSTALLATION.md) - System-wide installation
- [GPU Setup (Windows)](setup/GPU_SETUP_WINDOWS.md) - GPU configuration for Windows
- [Windows Guide](setup/WINDOWS_GUIDE.md) - Comprehensive Windows setup
- [Setup Fixes](setup/SETUP_FIXES.md) - Common setup issues
- [exFAT Compatibility](setup/exFAT_compatibility.md) - File system compatibility notes

### 🔌 [plugins/](plugins/)
Plugin system documentation
- [Plugin Guide](plugins/PLUGIN_GUIDE.md) - **Main comprehensive guide**
- [Plugin Development](plugins/PLUGIN_DEVELOPMENT.md) - Development details
- [Plugin Discovery (Explained)](plugins/PLUGIN_DISCOVERY_EXPLAINED.md) - Discovery system deep dive
- [Plugin Discovery (Simple)](plugins/PLUGIN_DISCOVERY_SIMPLE.md) - Discovery overview
- [Plugin System README](plugins/PLUGIN_SYSTEM_README.md) - Quick reference
- [Feature Summary](plugins/FEATURE_SUMMARY.md) - Feature overview
- [Conversion Summary](plugins/CONVERSION_SUMMARY.md) - Script conversion guide
- [Test & Docs Summary](plugins/TEST_AND_DOCS_SUMMARY.md) - Testing documentation

### 🏗️ [architecture/](architecture/)
System architecture documentation
- [Architecture](architecture/Architecture.md) - System architecture overview
- [Centralized Paths](architecture/CENTRALIZED_PATHS.md) - Path management system
- [Dependency Injection Analysis](architecture/dependency_injection_analysis.md)
- [Code Cleanup Analysis](architecture/code_cleanup_analysis.md)
- Additional architecture diagrams and analysis

### 🔄 [migration/](migration/)
Migration and upgrade guides
- [Configuration Migration Guide](migration/CONFIGURATION_MIGRATION_GUIDE.md)
- [Migration Guide](migration/migration_guide.md)
- [Migration Checklist](migration/migration_checklist.md)
- [Migration Order](migration/migration_order.md)
- [Migration Utils](migration/MIGRATION_utils.md)

### 🛠️ [development/](development/)
Development documentation
- [Documentation Guide](development/DOCUMENTATION.md)
- [Status Bar](development/STATUS_BAR.md)
- [Progress Styles](development/progress_styles.md)
- [README Refactored](development/README_REFACTORED.md)

### 📊 [project/](project/)
Project management and reviews
- [Project Review](project/PROJECT_REVIEW.md)
- [Windows Refactoring Guide](project/percell-windows-refactoring-guide.md)

### 📦 [archive/](archive/)
Archived/deprecated documentation

## Quick Links

### New Users
1. Start with [Getting Started](setup/Getting_Started.md)
2. Follow platform-specific setup:
   - Windows: [Windows Guide](setup/WINDOWS_GUIDE.md)
   - GPU: [GPU Setup](setup/GPU_SETUP_WINDOWS.md)

### Plugin Developers
1. Read [Plugin Guide](plugins/PLUGIN_GUIDE.md) - comprehensive resource
2. Use template: `python -m percell.plugins.template_generator`
3. Convert scripts: `python -m percell.plugins.converter`

### Contributors
1. Review [Architecture](architecture/Architecture.md)
2. Check [Development Docs](development/DOCUMENTATION.md)
3. See [Project Review](project/PROJECT_REVIEW.md)

## Main Documentation

- **Project README**: [../README.md](../README.md)
- **Changelog**: [../CHANGELOG.md](../CHANGELOG.md)
- **API Reference**: [api.md](api.md)

## Contributing to Documentation

When adding new documentation:
1. Place it in the appropriate subdirectory
2. Update this README with a link
3. Use clear, descriptive filenames
4. Include cross-references to related docs
