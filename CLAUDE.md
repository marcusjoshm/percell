# Claude Instructions for Percell

## Project Overview
Percell is a Python package for cell image analysis and processing.

## Project Structure
- `percell/` - Main package directory
- `tests/` - Test files
- `docs/` - Documentation
- `image_metadata/` - Image metadata handling
- `analysis_artifacts/` - Analysis output artifacts

## Development Setup
This project uses:
- Python (see pyproject.toml for version requirements)
- Virtual environment in `.venv/`
- pytest for testing
- Type checking with mypy

## Common Commands
- **Testing**: `pytest tests/`
- **Type checking**: `mypy percell/`
- **Install in development mode**: `pip install -e .`

## Code Style
- Follow existing patterns in the codebase
- Use type hints where present
- Follow PEP 8 style guidelines
- Maintain existing import structure

## Important Notes
- This is a scientific/research package for cell image analysis
- Be careful with data processing pipelines
- Check existing tests before making changes
- Preserve backwards compatibility for analysis workflows