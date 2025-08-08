# Global Installation Guide

This document explains how to make the `percell` command available globally on your system.

## Current Setup

The `percell` command is now available globally through a symbolic link in `/usr/local/bin/percell`. This means you can run `percell` from any terminal window without needing to:

1. Navigate to the percell project folder
2. Activate the virtual environment
3. Run the command

**Status**: ✅ Working - The global installation is now functional!

## How It Works

1. **Virtual Environment**: The percell package is installed in the `venv` virtual environment
2. **Entry Point**: The `setup.py` defines a console script entry point that creates the `percell` command
3. **Symbolic Link**: A symbolic link is created from `/usr/local/bin/percell` to the actual command in the virtual environment
4. **Global Access**: Since `/usr/local/bin` is in your system PATH, the command is available everywhere

## Verification

To verify the installation is working:

```bash
# Check if percell is available
which percell

# Should output: /usr/local/bin/percell

# Test the command
percell --help
```

## Alternative Installation Methods

### Method 1: Using pipx (Recommended for Python applications)

If you prefer to use `pipx` for managing Python applications:

```bash
# Install pipx if you don't have it
brew install pipx

# Install percell globally using pipx
pipx install -e /path/to/percell

# Or if you want to install from a git repository
pipx install git+https://github.com/marcusjoshm/percell.git
```

### Method 2: Manual PATH Addition

If you prefer to add the percell directory to your PATH:

1. Add this line to your shell configuration file (`.zshrc`, `.bashrc`, etc.):
   ```bash
   export PATH="/Users/joshuamarcus/percell/venv/bin:$PATH"
   ```

2. Reload your shell configuration:
   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

### Method 3: Using the Launcher Script

A launcher script `percell_launcher.sh` is provided in the project root. You can:

1. Make it executable: `chmod +x percell_launcher.sh`
2. Add it to your PATH or create a symbolic link:
   ```bash
   ln -sf /path/to/percell/percell_launcher.sh /usr/local/bin/percell
   ```

## Troubleshooting

### Command Not Found

If `percell` command is not found:

1. Check if the symbolic link exists:
   ```bash
   ls -la /usr/local/bin/percell
   ```

2. Verify the virtual environment exists:
   ```bash
   ls -la /Users/leelab/percell/venv/bin/percell
   ```

3. Recreate the symbolic link:
   ```bash
   sudo ln -sf /Users/leelab/percell/venv/bin/percell /usr/local/bin/percell
   ```

**Common Issue**: If you installed the package with `pip install -e .` but the global command doesn't work, the symbolic link may not have been created. 

**Quick Fix**: Run the fix script from the project root:
```bash
./percell/setup/fix_global_install.sh
```

Or run the installation script again or manually create the symlink as shown above.

### Permission Issues

If you get permission errors:

1. Check if `/usr/local/bin` is writable:
   ```bash
   ls -ld /usr/local/bin
   ```

2. If not, you may need to use `sudo` or change ownership:
   ```bash
   sudo chown $(whoami) /usr/local/bin
   ```

### Virtual Environment Issues

If the virtual environment is corrupted or missing:

1. Recreate the virtual environment:
   ```bash
   cd /Users/joshuamarcus/percell
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

2. Recreate the symbolic link:
   ```bash
   ln -sf /Users/joshuamarcus/percell/venv/bin/percell /usr/local/bin/percell
   ```

## Updating the Installation

When you update the percell code:

1. Activate the virtual environment:
   ```bash
   source /Users/joshuamarcus/percell/venv/bin/activate
   ```

2. Reinstall the package:
   ```bash
   pip install -e .
   ```

The global command will automatically use the updated version since it's a symbolic link.

## Uninstalling

To remove the global installation:

```bash
# Remove the symbolic link
rm /usr/local/bin/percell

# Optionally remove the virtual environment
rm -rf /Users/joshuamarcus/percell/venv
```
