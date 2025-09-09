# PyPI Publication Setup Guide

This guide explains how to set up Percell for publication on PyPI so users can install it with `pip install percell`.

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org/account/register/)
2. **TestPyPI Account**: Create an account at [test.pypi.org](https://test.pypi.org/account/register/)
3. **API Tokens**: Generate API tokens for both PyPI and TestPyPI

## Step 1: Create PyPI Accounts and API Tokens

### Create Accounts
1. Go to [pypi.org](https://pypi.org/account/register/) and create an account
2. Go to [test.pypi.org](https://test.pypi.org/account/register/) and create an account

### Generate API Tokens
1. **PyPI Token**:
   - Go to [pypi.org/manage/account/](https://pypi.org/manage/account/)
   - Scroll to "API tokens" section
   - Click "Add API token"
   - Give it a name (e.g., "percell-package")
   - Copy the token (starts with `pypi-`)

2. **TestPyPI Token**:
   - Go to [test.pypi.org/manage/account/](https://test.pypi.org/manage/account/)
   - Follow the same process as above
   - Copy the token (starts with `pypi-`)

## Step 2: Configure GitHub Secrets

Add the API tokens as GitHub repository secrets:

1. Go to your GitHub repository
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Add these secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token
   - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token

## Step 3: Test the Release Process

### Test on TestPyPI First

```bash
# Install release dependencies
pip install build twine

# Build the package
python -m build

# Check the package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

### Test Installation from TestPyPI

```bash
# Create a test environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ percell

# Test the installation
percell --help
```

## Step 4: Release to PyPI

### Option A: Using the Release Script (Recommended)

```bash
# Make the script executable
chmod +x release.py

# Bump version and prepare release
python release.py --bump patch --test

# After testing, publish to PyPI
python release.py --publish
```

### Option B: Manual Release

```bash
# Build the package
python -m build

# Upload to PyPI
twine upload dist/*
```

### Option C: GitHub Actions (Automatic)

1. Create a new release on GitHub:
   - Go to "Releases" → "Create a new release"
   - Tag version: `v1.0.0` (or your version)
   - Release title: `Percell v1.0.0`
   - Description: Release notes
   - Click "Publish release"

2. The GitHub Action will automatically:
   - Build the package
   - Upload to PyPI
   - Create build artifacts

## Step 5: Verify Publication

1. **Check PyPI**: Visit [pypi.org/project/percell/](https://pypi.org/project/percell/)
2. **Test Installation**: 
   ```bash
   pip install percell
   percell --help
   ```

## Version Management

### Semantic Versioning
- **Major** (1.0.0 → 2.0.0): Breaking changes
- **Minor** (1.0.0 → 1.1.0): New features, backward compatible
- **Patch** (1.0.0 → 1.0.1): Bug fixes, backward compatible

### Bumping Versions
```bash
# Patch version (bug fixes)
python release.py --bump patch

# Minor version (new features)
python release.py --bump minor

# Major version (breaking changes)
python release.py --bump major

# Specific version
python release.py --version 2.1.0
```

## Troubleshooting

### Common Issues

1. **Package name already taken**: Choose a different name in `pyproject.toml`
2. **Upload failed**: Check API token permissions
3. **Version already exists**: Bump the version number
4. **Build errors**: Check `setup.py` and `pyproject.toml` syntax

### Useful Commands

```bash
# Check package before upload
twine check dist/*

# View package contents
tar -tzf dist/percell-*.tar.gz

# Test package installation
pip install --force-reinstall dist/*.whl
```

## Security Best Practices

1. **Never commit API tokens** to version control
2. **Use API tokens** instead of passwords
3. **Rotate tokens** regularly
4. **Use TestPyPI** for testing before production releases

## Post-Publication

After successful publication:

1. **Update documentation** with PyPI installation instructions
2. **Announce the release** on relevant channels
3. **Monitor for issues** and user feedback
4. **Plan next release** based on user needs

## Support

For issues with PyPI publication:
- [PyPI Help](https://pypi.org/help/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
