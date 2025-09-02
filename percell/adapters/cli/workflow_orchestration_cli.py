#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Adapter for Workflow Orchestration Service

This module provides a command-line interface for the WorkflowOrchestrationService,
allowing users to execute and manage analysis workflows.
"""

import argparse
import sys
from pathlib import Path
from percell.main.composition_root import get_composition_root


def _create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the workflow orchestration CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Orchestrate single-cell analysis workflows using hexagonal architecture services'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List workflows command
    list_parser = subparsers.add_parser('list', help='List available workflows')
    
    # Execute workflow command
    execute_parser = subparsers.add_parser('execute', help='Execute a workflow')
    execute_parser.add_argument('workflow', help='Name of the workflow to execute')
    execute_parser.add_argument('--input', required=True, help='Input directory path')
    execute_parser.add_argument('--output', required=True, help='Output directory path')
    execute_parser.add_argument('--imagej-path', help='Path to ImageJ executable')
    execute_parser.add_argument('--conditions', nargs='+', help='Conditions to analyze')
    execute_parser.add_argument('--timepoints', nargs='+', help='Timepoints to analyze')
    execute_parser.add_argument('--regions', nargs='+', help='Regions to analyze')
    execute_parser.add_argument('--segmentation-channel', help='Segmentation channel')
    execute_parser.add_argument('--analysis-channels', nargs='+', help='Analysis channels')
    execute_parser.add_argument('--bins', type=int, default=5, help='Number of bins for cell grouping')
    
    # Validate workflow command
    validate_parser = subparsers.add_parser('validate', help='Validate workflow requirements')
    validate_parser.add_argument('workflow', help='Name of the workflow to validate')
    validate_parser.add_argument('--input', required=True, help='Input directory path')
    validate_parser.add_argument('--output', required=True, help='Output directory path')
    validate_parser.add_argument('--imagej-path', help='Path to ImageJ executable')
    
    # Setup directories command
    setup_parser = subparsers.add_parser('setup', help='Setup workflow directories')
    setup_parser.add_argument('workflow', help='Name of the workflow')
    setup_parser.add_argument('--output', required=True, help='Output directory path')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get workflow status')
    status_parser.add_argument('workflow', help='Name of the workflow')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show workflow execution history')
    
    # Cancel command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel currently running workflow')
    
    return parser


def _list_workflows() -> None:
    """
    List all available workflows.
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_orchestration_service')
        
        workflows = service.get_available_workflows()
        
        print("🚀 Available Workflows")
        print("=" * 80)
        
        for workflow_id, workflow in workflows.items():
            print(f"\n📋 {workflow['name']}")
            print(f"   ID: {workflow_id}")
            print(f"   Description: {workflow['description']}")
            print(f"   Steps: {', '.join(workflow['steps'])}")
            print(f"   Estimated Duration: {workflow['estimated_duration']}")
            print(f"   Requirements: {', '.join(workflow['requirements'])}")
        
        print(f"\n✅ Total workflows available: {len(workflows)}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error listing workflows: {e}")
        sys.exit(1)


def _execute_workflow(args) -> None:
    """
    Execute a workflow.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_orchestration_service')
        
        # Prepare workflow parameters
        workflow_params = {
            'imagej_path': args.imagej_path,
            'conditions': args.conditions,
            'timepoints': args.timepoints,
            'regions': args.regions,
            'segmentation_channel': args.segmentation_channel,
            'analysis_channels': args.analysis_channels,
            'bins': args.bins
        }
        
        # Remove None values
        workflow_params = {k: v for k, v in workflow_params.items() if v is not None}
        
        print(f"🚀 Executing workflow: {args.workflow}")
        print(f"   Input: {args.input}")
        print(f"   Output: {args.output}")
        if workflow_params:
            print(f"   Parameters: {workflow_params}")
        print()
        
        # Execute the workflow
        result = service.execute_workflow(
            workflow_name=args.workflow,
            input_dir=args.input,
            output_dir=args.output,
            **workflow_params
        )
        
        if result['success']:
            print("✅ Workflow executed successfully!")
            print(f"   Duration: {result['total_duration']:.2f} seconds")
            print(f"   Steps completed: {len(result['steps_completed'])}")
            print(f"   Steps failed: {len(result['steps_failed'])}")
            
            if result['steps_completed']:
                print("\n📋 Completed steps:")
                for step in result['steps_completed']:
                    print(f"   • {step['step']}: {step['message']} ({step['duration']:.2f}s)")
            
            sys.exit(0)
        else:
            print(f"❌ Workflow execution failed!")
            print(f"   Error: {result['error']}")
            
            if result['steps_failed']:
                print("\n❌ Failed steps:")
                for step in result['steps_failed']:
                    print(f"   • {step['step']}: {step['error']} ({step['duration']:.2f}s)")
            
            sys.exit(1)
            
    except Exception as e:
        print(f"Error executing workflow: {e}")
        sys.exit(1)


def _validate_workflow(args) -> None:
    """
    Validate workflow requirements.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_orchestration_service')
        
        # Prepare validation parameters
        validation_params = {}
        if args.imagej_path:
            validation_params['imagej_path'] = args.imagej_path
        
        print(f"🔍 Validating workflow: {args.workflow}")
        print(f"   Input: {args.input}")
        print(f"   Output: {args.output}")
        print()
        
        # Validate the workflow
        result = service.validate_workflow_requirements(
            workflow_name=args.workflow,
            input_dir=args.input,
            output_dir=args.output,
            **validation_params
        )
        
        if result['valid']:
            print("✅ Workflow validation passed!")
            print(f"   Workflow: {result['workflow']['name']}")
            print(f"   Steps: {', '.join(result['workflow']['steps'])}")
            
            if result['warnings']:
                print("\n⚠️  Warnings:")
                for warning in result['warnings']:
                    print(f"   • {warning}")
            
            sys.exit(0)
        else:
            print(f"❌ Workflow validation failed!")
            print("\n❌ Errors:")
            for error in result['errors']:
                print(f"   • {error}")
            
            if result['warnings']:
                print("\n⚠️  Warnings:")
                for warning in result['warnings']:
                    print(f"   • {warning}")
            
            sys.exit(1)
            
    except Exception as e:
        print(f"Error validating workflow: {e}")
        sys.exit(1)


def _setup_workflow_directories(args) -> None:
    """
    Setup workflow directories.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_orchestration_service')
        
        print(f"📁 Setting up directories for workflow: {args.workflow}")
        print(f"   Output: {args.output}")
        print()
        
        # Setup the directories
        result = service.setup_workflow_directories(
            output_dir=args.output,
            workflow_name=args.workflow
        )
        
        if result['success']:
            print("✅ Workflow directories setup completed!")
            print(f"   Created {len(result['created_directories'])} directories:")
            for directory in result['created_directories']:
                print(f"   • {directory}")
            
            sys.exit(0)
        else:
            print(f"❌ Directory setup failed!")
            print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error setting up workflow directories: {e}")
        sys.exit(1)


def _get_workflow_status(args) -> None:
    """
    Get workflow status.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_orchestration_service')
        
        print(f"📊 Getting status for workflow: {args.workflow}")
        print()
        
        # Get the workflow status
        result = service.get_workflow_status(args.workflow)
        
        if result['status'] == 'not_found':
            print(f"❌ Workflow '{args.workflow}' not found in execution history")
            sys.exit(1)
        elif result['status'] == 'error':
            print(f"❌ Error getting workflow status: {result['error']}")
            sys.exit(1)
        else:
            print(f"📋 Workflow: {args.workflow}")
            print(f"   Status: {result['status']}")
            
            if result['status'] == 'running':
                print(f"   Start Time: {result['start_time']}")
                print(f"   Is Running: {result['is_running']}")
            elif result['status'] in ['completed', 'failed']:
                print(f"   Total Duration: {result['total_duration']:.2f}s")
                print(f"   Steps Completed: {result['steps_completed']}")
                print(f"   Steps Failed: {result['steps_failed']}")
            
            sys.exit(0)
            
    except Exception as e:
        print(f"Error getting workflow status: {e}")
        sys.exit(1)


def _show_execution_history() -> None:
    """
    Show workflow execution history.
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_orchestration_service')
        
        print("📚 Workflow Execution History")
        print("=" * 80)
        
        # Get the execution history
        history = service.get_execution_history()
        
        if not history:
            print("No workflows have been executed yet.")
            sys.exit(0)
        
        for i, execution in enumerate(history, 1):
            print(f"\n📋 {i}. {execution['workflow_name']}")
            print(f"   Status: {'✅ Completed' if execution['success'] else '❌ Failed'}")
            print(f"   Duration: {execution['total_duration']:.2f}s")
            print(f"   Steps: {len(execution['steps_completed'])} completed, {len(execution['steps_failed'])} failed")
            print(f"   Start Time: {execution['start_time']}")
        
        print(f"\n✅ Total workflows executed: {len(history)}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error showing execution history: {e}")
        sys.exit(1)


def _cancel_current_workflow() -> None:
    """
    Cancel the currently running workflow.
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_orchestration_service')
        
        print("🛑 Cancelling currently running workflow...")
        print()
        
        # Cancel the current workflow
        result = service.cancel_current_workflow()
        
        if result['success']:
            print(f"✅ {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to cancel workflow: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error cancelling workflow: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the workflow orchestration CLI.
    """
    parser = _create_parser()
    args = parser.parse_args()
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command handler
    if args.command == 'list':
        _list_workflows()
    elif args.command == 'execute':
        _execute_workflow(args)
    elif args.command == 'validate':
        _validate_workflow(args)
    elif args.command == 'setup':
        _setup_workflow_directories(args)
    elif args.command == 'status':
        _get_workflow_status(args)
    elif args.command == 'history':
        _show_execution_history()
    elif args.command == 'cancel':
        _cancel_current_workflow()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
