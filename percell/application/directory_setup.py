from __future__ import annotations

"""Application-level helpers for interactive directory setup and persistence."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def validate_directory_path(path: str, create_if_missing: bool = False) -> bool:
    try:
        path_obj = Path(path)
        if path_obj.exists():
            return path_obj.is_dir()
        if create_if_missing:
            path_obj.mkdir(parents=True, exist_ok=True)
            return True
        return False
    except Exception:
        return False


def get_recent_directories(config: Dict, directory_type: str) -> List[str]:
    if 'directories' not in config:
        return []
    recent_key = f"recent_{directory_type}s"
    return config['directories'].get(recent_key, [])


def add_recent_directory(config: Dict, directory_type: str, path: str, max_recent: int = 5) -> None:
    if 'directories' not in config:
        config['directories'] = {}
    recent_key = f"recent_{directory_type}s"
    if recent_key not in config['directories']:
        config['directories'][recent_key] = []
    if path in config['directories'][recent_key]:
        config['directories'][recent_key].remove(path)
    config['directories'][recent_key].insert(0, path)
    config['directories'][recent_key] = config['directories'][recent_key][:max_recent]


def prompt_for_directory(directory_type: str, recent_dirs: List[str], default_path: str = "") -> str:
    print(f"\n=== {directory_type.title()} Directory Selection ===")
    if recent_dirs:
        print(f"Recent {directory_type} directories:")
        for i, p in enumerate(recent_dirs, 1):
            print(f"  {i}. {p}")
        print(f"  {len(recent_dirs) + 1}. Enter new path\n")
        while True:
            choice = input(f"Select {directory_type} directory (1-{len(recent_dirs) + 1}) or enter path: ").strip()
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(recent_dirs):
                    selected_path = recent_dirs[idx - 1]
                    print(f"Selected: {selected_path}")
                    return selected_path
                if idx == len(recent_dirs) + 1:
                    break
                print(f"Please enter a number between 1 and {len(recent_dirs) + 1}")
                continue
            if choice:
                return choice
            print("Please enter a valid path or number")
    while True:
        if default_path:
            path = input(f"Enter {directory_type} directory path (default: {default_path}): ").strip() or default_path
        else:
            path = input(f"Enter {directory_type} directory path: ").strip()
        if not path:
            print("Please enter a valid path")
            continue
        path = path.strip("'\"")
        if directory_type == "input":
            if not validate_directory_path(path, create_if_missing=False):
                print(f"Error: Input directory '{path}' does not exist or is not accessible")
                continue
        else:
            if not validate_directory_path(path, create_if_missing=True):
                print(f"Error: Cannot create or access output directory '{path}'")
                continue
        return path


def get_paths_interactively(
    config: Dict,
    args_input: Optional[str] = None,
    args_output: Optional[str] = None,
) -> Tuple[str, str, bool]:
    recent_inputs = get_recent_directories(config, 'input')
    recent_outputs = get_recent_directories(config, 'output')
    default_input = config.get('directories', {}).get('input', '')
    default_output = config.get('directories', {}).get('output', '')

    if not args_input:
        input_path = prompt_for_directory('input', recent_inputs, default_input)
    else:
        input_path = args_input
        if not validate_directory_path(input_path, create_if_missing=False):
            print(f"Warning: Input directory '{input_path}' does not exist or is not accessible")
            input_path = prompt_for_directory('input', recent_inputs, default_input)

    if not args_output:
        output_path = prompt_for_directory('output', recent_outputs, default_output)
    else:
        output_path = args_output
        if not validate_directory_path(output_path, create_if_missing=True):
            print(f"Warning: Cannot create or access output directory '{output_path}'")
            output_path = prompt_for_directory('output', recent_outputs, default_output)

    print(f"\nSelected paths:")
    print(f"  Input: {input_path}")
    print(f"  Output: {output_path}")

    save_defaults = input("\nSave these paths as defaults? (y/n): ").strip().lower()
    config_modified = False
    if save_defaults in ['y', 'yes']:
        if 'directories' not in config:
            config['directories'] = {}
        config['directories']['input'] = input_path
        config['directories']['output'] = output_path
        add_recent_directory(config, 'input', input_path)
        add_recent_directory(config, 'output', output_path)
        config_modified = True
        print("Paths saved as defaults!")
    return input_path, output_path, config_modified


def save_config(config: Dict, config_path: str) -> None:
    try:
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Warning: Could not save config to {config_path}: {e}")


def load_config(config_path: str) -> Dict:
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config from {config_path}: {e}")
        return {}


def save_recent_directories_automatically(
    config: Dict,
    input_path: str,
    output_path: str,
    config_path: str,
) -> None:
    try:
        if 'directories' not in config:
            config['directories'] = {}
        config['directories']['input'] = input_path
        config['directories']['output'] = output_path
        add_recent_directory(config, 'input', input_path)
        add_recent_directory(config, 'output', output_path)
        save_config(config, config_path)
        print(f"✅ Automatically saved directories as defaults:")
        print(f"  Input: {input_path}")
        print(f"  Output: {output_path}")
    except Exception as e:
        print(f"Warning: Could not save directory defaults: {e}")



# ------------------------- Compatibility helpers -------------------------

def set_default_directories(config: Dict, config_path: str) -> Tuple[str, str]:
    """Interactive workflow to set and persist default input/output directories."""
    print("\n=== Set Default Directories ===")
    print("This will set the default input and output directories for future runs.")
    print("These directories will be used automatically unless overridden with --input and --output arguments.")

    # Recent and current defaults
    recent_inputs = get_recent_directories(config, 'input')
    recent_outputs = get_recent_directories(config, 'output')
    current_input = config.get('directories', {}).get('input', '')
    current_output = config.get('directories', {}).get('output', '')

    print(f"\nCurrent defaults:")
    print(f"  Input: {current_input if current_input else 'Not set'}")
    print(f"  Output: {current_output if current_output else 'Not set'}")

    # Prompt user
    print(f"\nSetting input directory:")
    input_path = prompt_for_directory('input', recent_inputs, current_input)

    print(f"\nSetting output directory:")
    output_path = prompt_for_directory('output', recent_outputs, current_output)

    # Update config
    if 'directories' not in config:
        config['directories'] = {}
    config['directories']['input'] = input_path
    config['directories']['output'] = output_path

    # Add to recent and persist
    add_recent_directory(config, 'input', input_path)
    add_recent_directory(config, 'output', output_path)
    save_config(config, config_path)

    print(f"\n✅ Default directories set successfully!")
    print(f"  Input: {input_path}")
    print(f"  Output: {output_path}")
    print(f"  Config saved to: {config_path}")

    return input_path, output_path


def check_default_directories(config: Dict) -> Tuple[bool, str, str]:
    """Validate presence and accessibility of default directories in config."""
    if 'directories' not in config:
        return False, "", ""

    input_path = config['directories'].get('input', '')
    output_path = config['directories'].get('output', '')
    if not input_path or not output_path:
        return False, input_path, output_path

    input_valid = validate_directory_path(input_path, create_if_missing=False)
    output_valid = validate_directory_path(output_path, create_if_missing=True)
    return input_valid and output_valid, input_path, output_path


def get_default_directories(config: Dict) -> Tuple[str, str]:
    """Return (input, output) defaults from config if present."""
    if 'directories' not in config:
        return "", ""
    return (
        config['directories'].get('input', ''),
        config['directories'].get('output', ''),
    )
