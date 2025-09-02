#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Adapter for Directory Management Service

This module provides a command-line interface for the DirectoryManagementService,
allowing users to manage input and output directories with configuration persistence.
"""

import argparse
import sys
from pathlib import Path
from percell.main.composition_root import get_composition_root
from typing import Optional


def _create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the directory management CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Manage input and output directories with configuration persistence'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Set defaults command
    set_parser = subparsers.add_parser('set', help='Set default directories')
    set_parser.add_argument('--input', required=True, help='Input directory path')
    set_parser.add_argument('--output', required=True, help='Output directory path')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check default directories')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List recent directories')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear recent directories')
    clear_parser.add_argument('--type', choices=['input', 'output'], help='Directory type to clear (default: both)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate workflow directories')
    validate_parser.add_argument('--input', required=True, help='Input directory path to validate')
    validate_parser.add_argument('--output', required=True, help='Output directory path to validate')
    
    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Interactive directory setup')
    interactive_parser.add_argument('--input', help='Input directory path (optional)')
    interactive_parser.add_argument('--output', help='Output directory path (optional)')
    
    # Auto-save command
    auto_save_parser = subparsers.add_parser('auto-save', help='Automatically save directories as defaults')
    auto_save_parser.add_argument('--input', required=True, help='Input directory path')
    auto_save_parser.add_argument('--output', required=True, help='Output directory path')
    
    return parser


def _set_default_directories(input_path: str, output_path: str) -> None:
    """
    Set default input and output directories.
    
    Args:
        input_path: Input directory path
        output_path: Output directory path
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('directory_management_service')
        
        result = service.set_default_directories(input_path, output_path)
        
        if result['success']:
            print("✅ Default directories set successfully")
            print(f"   Input: {result['input_path']}")
            print(f"   Output: {result['output_path']}")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to set default directories")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error setting default directories: {e}")
        sys.exit(1)


def _check_default_directories() -> None:
    """
    Check if default directories are set and valid.
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('directory_management_service')
        
        result = service.check_default_directories()
        
        if result['valid']:
            print("✅ Default directories are valid")
            print(f"   Input: {result['input_path']}")
            print(f"   Output: {result['output_path']}")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Default directories are invalid")
            print(f"   Input: {result['input_path']}")
            print(f"   Output: {result['output_path']}")
            print(f"   {result['message']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error checking default directories: {e}")
        sys.exit(1)


def _list_recent_directories() -> None:
    """
    List all recent directories from configuration.
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('directory_management_service')
        
        result = service.list_recent_directories()
        
        if result['success']:
            print("📁 Recent Directories")
            print("=" * 50)
            
            print("\n📂 Recent Input Directories:")
            if result['recent_inputs']:
                for i, path in enumerate(result['recent_inputs'], 1):
                    print(f"  {i}. {path}")
            else:
                print("  None")
            
            print("\n📂 Recent Output Directories:")
            if result['recent_outputs']:
                for i, path in enumerate(result['recent_outputs'], 1):
                    print(f"  {i}. {path}")
            else:
                print("  None")
            
            print("\n⚙️  Default Directories:")
            print(f"  Input: {result['default_input'] if result['default_input'] else 'Not set'}")
            print(f"  Output: {result['default_output'] if result['default_output'] else 'Not set'}")
            
            print(f"\n✅ {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to list recent directories")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error listing recent directories: {e}")
        sys.exit(1)


def _clear_recent_directories(directory_type: Optional[str] = None) -> None:
    """
    Clear recent directories.
    
    Args:
        directory_type: Type of directory to clear ('input', 'output', or None for both)
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('directory_management_service')
        
        result = service.clear_recent_directories(directory_type)
        
        if result['success']:
            print(f"✅ {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to clear recent directories")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error clearing recent directories: {e}")
        sys.exit(1)


def _validate_workflow_directories(input_path: str, output_path: str) -> None:
    """
    Validate directories for workflow execution.
    
    Args:
        input_path: Input directory path to validate
        output_path: Output directory path to validate
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('directory_management_service')
        
        result = service.validate_workflow_directories(input_path, output_path)
        
        if result['valid']:
            print("✅ Workflow directories validated successfully")
            print(f"   Input: {result['input_path']}")
            print(f"   Output: {result['output_path']}")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Workflow directories validation failed")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error validating workflow directories: {e}")
        sys.exit(1)


def _interactive_directory_setup(input_path: Optional[str] = None, output_path: Optional[str] = None) -> None:
    """
    Interactive directory setup.
    
    Args:
        input_path: Optional input directory path
        output_path: Optional output directory path
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('directory_management_service')
        
        result = service.get_paths_interactively(input_path, output_path)
        
        if result['success']:
            print("✅ Interactive directory setup completed")
            print(f"   Input: {result['input_path']}")
            print(f"   Output: {result['output_path']}")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Interactive directory setup failed")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error in interactive directory setup: {e}")
        sys.exit(1)


def _auto_save_directories(input_path: str, output_path: str) -> None:
    """
    Automatically save directories as defaults.
    
    Args:
        input_path: Input directory path
        output_path: Output directory path
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('directory_management_service')
        
        result = service.save_recent_directories_automatically(input_path, output_path)
        
        if result['success']:
            print("✅ Directories automatically saved as defaults")
            print(f"   Input: {result['input_path']}")
            print(f"   Output: {result['output_path']}")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to auto-save directories")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error auto-saving directories: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the directory management CLI.
    """
    parser = _create_parser()
    args = parser.parse_args()
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command handler
    if args.command == 'set':
        _set_default_directories(args.input, args.output)
    elif args.command == 'check':
        _check_default_directories()
    elif args.command == 'list':
        _list_recent_directories()
    elif args.command == 'clear':
        _clear_recent_directories(args.type)
    elif args.command == 'validate':
        _validate_workflow_directories(args.input, args.output)
    elif args.command == 'interactive':
        _interactive_directory_setup(args.input, args.output)
    elif args.command == 'auto-save':
        _auto_save_directories(args.input, args.output)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
