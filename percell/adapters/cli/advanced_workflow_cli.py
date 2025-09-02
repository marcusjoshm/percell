#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Adapter for Advanced Workflow Service

This module provides a command-line interface for the AdvancedWorkflowService,
allowing users to build and execute custom workflows from predefined steps.
"""

import argparse
import sys
from pathlib import Path
from percell.main.composition_root import get_composition_root


def _create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the advanced workflow CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Advanced Workflow Builder for Single Cell Analysis'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        required=True,
        help='Output directory for the workflow'
    )
    
    parser.add_argument(
        '--steps',
        nargs='+',
        type=int,
        help='Space-separated sequence of step numbers to execute'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode to select steps'
    )
    
    parser.add_argument(
        '--list-steps',
        action='store_true',
        help='List available workflow steps and exit'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate workflow inputs and exit'
    )
    
    parser.add_argument(
        '--check-dependencies',
        action='store_true',
        help='Check dependencies between selected steps'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be executed without running'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser


def _validate_arguments(args: argparse.Namespace) -> bool:
    """
    Validate the provided command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if arguments are valid, False otherwise
    """
    # Check if output directory can be created
    try:
        output_path = Path(args.output_dir)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error: Cannot create output directory: {e}")
        return False
    
    # Check if steps are provided when not in interactive mode
    if not args.interactive and not args.steps and not args.list_steps and not args.validate:
        print("Error: Must specify --steps or --interactive mode")
        return False
    
    # Validate step numbers if provided
    if args.steps:
        if any(step < 1 or step > 11 for step in args.steps):
            print("Error: Step numbers must be between 1 and 11")
            return False
    
    return True


def _list_available_steps() -> None:
    """
    List available workflow steps.
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('advanced_workflow_service')
        
        steps = service.get_available_steps()
        
        print("\n" + "="*80)
        print(" Advanced Workflow Builder - Available Steps ".center(80, '='))
        print("="*80)
        print("0. Back to main menu")
        for idx, (step_key, step_label) in enumerate(steps, start=1):
            print(f"{idx}. {step_label}")
        
        print("\n" + "-"*80)
        print(" Enter a space-separated sequence of numbers to define your custom workflow ")
        print(" Example: 1 2 3 4 5 6 7 8 9 10 11 ")
        print(" Type 0 or Q to return to the main menu ")
        print("-"*80)
        
    except Exception as e:
        print(f"Error listing steps: {e}")
        sys.exit(1)


def _validate_workflow_inputs(output_dir: str) -> None:
    """
    Validate workflow inputs.
    
    Args:
        output_dir: Output directory to validate
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('advanced_workflow_service')
        
        result = service.validate_workflow_inputs(output_dir=output_dir)
        
        if result['valid']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error validating inputs: {e}")
        sys.exit(1)


def _check_step_dependencies(steps: list) -> None:
    """
    Check dependencies between selected steps.
    
    Args:
        steps: List of step numbers
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('advanced_workflow_service')
        
        # Convert step numbers to step keys
        available_steps = service.get_available_steps()
        step_keys = [available_steps[step-1][0] for step in steps]
        
        result = service.validate_step_dependencies(step_keys)
        
        if result['valid']:
            print(f"✅ {result['message']}")
        else:
            print(f"⚠️  {result['message']}")
            if 'warnings' in result:
                print("Dependency warnings:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
            
    except Exception as e:
        print(f"Error checking dependencies: {e}")
        sys.exit(1)


def _get_workflow_summary(steps: list) -> str:
    """
    Get a summary of the selected workflow steps.
    
    Args:
        steps: List of step numbers
        
    Returns:
        Formatted workflow summary
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('advanced_workflow_service')
        
        # Convert step numbers to step keys
        available_steps = service.get_available_steps()
        step_keys = [available_steps[step-1][0] for step in steps]
        
        return service.get_workflow_summary(step_keys)
        
    except Exception as e:
        return f"Error generating summary: {e}"


def _run_interactive_mode(output_dir: str) -> None:
    """
    Run the advanced workflow in interactive mode.
    
    Args:
        output_dir: Output directory for the workflow
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('advanced_workflow_service')
        
        # Show available steps
        _list_available_steps()
        
        # Get user input
        try:
            selection_raw = input("\n>>> Custom workflow (space-separated numbers, or 0/Q to exit): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nWorkflow cancelled")
            return
        
        if not selection_raw or selection_raw.lower() in {"0", "q", "quit", "exit"}:
            print("Exiting Advanced Workflow")
            return
        
        # Build workflow from selection
        result = service.build_workflow_from_selection(selection_raw)
        
        if not result['success']:
            print(f"Error: {result['error']}")
            return
        
        if result.get('cancelled'):
            print(result['message'])
            return
        
        selected_steps = result['selected_steps']
        
        # Show workflow summary
        print("\n" + _get_workflow_summary(selected_steps))
        
        # Check dependencies
        dep_result = service.validate_step_dependencies(selected_steps)
        if not dep_result['valid']:
            print(f"\n⚠️  {dep_result['message']}")
            if 'warnings' in dep_result:
                print("Dependency warnings:")
                for warning in dep_result['warnings']:
                    print(f"  - {warning}")
            
            try:
                choice = input("\nContinue anyway? [y/N]: ").strip().lower()
                if choice not in ('y', 'yes'):
                    print("Workflow cancelled")
                    return
            except (EOFError, KeyboardInterrupt):
                print("\nWorkflow cancelled")
                return
        
        # Execute workflow
        print(f"\nExecuting workflow with {len(selected_steps)} steps...")
        execution_result = service.execute_workflow(selected_steps, output_dir)
        
        if execution_result['success']:
            print(f"✅ {execution_result['message']}")
        else:
            print(f"❌ {execution_result['error']}")
            if 'completed_steps' in execution_result:
                print(f"Completed steps: {', '.join(execution_result['completed_steps'])}")
            
    except Exception as e:
        print(f"Error in interactive mode: {e}")
        sys.exit(1)


def _run_workflow_from_args(steps: list, output_dir: str, dry_run: bool = False) -> None:
    """
    Run workflow from command line arguments.
    
    Args:
        steps: List of step numbers
        output_dir: Output directory for the workflow
        dry_run: Whether to show what would be executed without running
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('advanced_workflow_service')
        
        # Convert step numbers to step keys
        available_steps = service.get_available_steps()
        step_keys = [available_steps[step-1][0] for step in steps]
        
        # Show workflow summary
        summary = _get_workflow_summary(steps)
        print(summary)
        
        # Check dependencies
        dep_result = service.validate_step_dependencies(step_keys)
        if not dep_result['valid']:
            print(f"\n⚠️  {dep_result['message']}")
            if 'warnings' in dep_result:
                print("Dependency warnings:")
                for warning in dep_result['warnings']:
                    print(f"  - {warning}")
        
        if dry_run:
            print("\n🔍 DRY RUN MODE - No actual execution")
            print("To execute the workflow, remove --dry-run flag")
            return
        
        # Execute workflow
        print(f"\nExecuting workflow with {len(step_keys)} steps...")
        execution_result = service.execute_workflow(step_keys, output_dir)
        
        if execution_result['success']:
            print(f"✅ {execution_result['message']}")
        else:
            print(f"❌ {execution_result['error']}")
            if 'completed_steps' in execution_result:
                print(f"Completed steps: {', '.join(execution_result['completed_steps'])}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error executing workflow: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the advanced workflow CLI.
    """
    parser = _create_parser()
    args = parser.parse_args()
    
    # Handle special operations first
    if args.list_steps:
        _list_available_steps()
        return
    
    if args.validate:
        _validate_workflow_inputs(args.output_dir)
        return
    
    if args.check_dependencies and args.steps:
        _check_step_dependencies(args.steps)
        return
    
    # Validate arguments
    if not _validate_arguments(args):
        sys.exit(1)
    
    # Run the workflow
    if args.interactive:
        _run_interactive_mode(args.output_dir)
    elif args.steps:
        _run_workflow_from_args(args.steps, args.output_dir, args.dry_run)
    else:
        print("Error: Must specify --steps or --interactive mode")
        sys.exit(1)


if __name__ == "__main__":
    main()
