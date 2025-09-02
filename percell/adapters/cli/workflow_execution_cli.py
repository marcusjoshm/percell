#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Adapter for Workflow Execution Service

This module provides a command-line interface for the WorkflowExecutionService,
allowing users to execute workflows and manage workflow execution.
"""

import argparse
import sys
from pathlib import Path
from percell.main.composition_root import get_composition_root


def _create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the workflow execution CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Execute workflows and manage workflow execution'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Execute workflow command
    execute_parser = subparsers.add_parser('execute', help='Execute a workflow')
    execute_parser.add_argument('workflow_id', help='ID of the workflow to execute')
    execute_parser.add_argument('--input', required=True, help='Input directory path')
    execute_parser.add_argument('--output', required=True, help='Output directory path')
    execute_parser.add_argument('--imagej-path', help='Path to ImageJ executable')
    execute_parser.add_argument('--conditions', nargs='+', help='Conditions to analyze')
    execute_parser.add_argument('--timepoints', nargs='+', help='Timepoints to analyze')
    execute_parser.add_argument('--regions', nargs='+', help='Regions to analyze')
    execute_parser.add_argument('--segmentation-channel', help='Segmentation channel')
    execute_parser.add_argument('--analysis-channels', nargs='+', help='Analysis channels')
    execute_parser.add_argument('--bins', type=int, default=5, help='Number of bins for cell grouping')
    
    # Execute step command
    step_parser = subparsers.add_parser('step', help='Execute a single workflow step')
    step_parser.add_argument('step_id', help='ID of the step to execute')
    step_parser.add_argument('--input', required=True, help='Input directory path')
    step_parser.add_argument('--output', required=True, help='Output directory path')
    step_parser.add_argument('--imagej-path', help='Path to ImageJ executable')
    step_parser.add_argument('--conditions', nargs='+', help='Conditions to analyze')
    step_parser.add_argument('--timepoints', nargs='+', help='Timepoints to analyze')
    step_parser.add_argument('--regions', nargs='+', help='Regions to analyze')
    step_parser.add_argument('--segmentation-channel', help='Segmentation channel')
    step_parser.add_argument('--analysis-channels', nargs='+', help='Analysis channels')
    step_parser.add_argument('--bins', type=int, default=5, help='Number of bins for cell grouping')
    
    # Execute sequence command
    sequence_parser = subparsers.add_parser('sequence', help='Execute a sequence of workflow steps')
    sequence_parser.add_argument('workflow_id', help='ID of the workflow')
    sequence_parser.add_argument('--steps', nargs='+', required=True, help='Step IDs to execute in order')
    sequence_parser.add_argument('--input', required=True, help='Input directory path')
    sequence_parser.add_argument('--output', required=True, help='Output directory path')
    sequence_parser.add_argument('--imagej-path', help='Path to ImageJ executable')
    sequence_parser.add_argument('--conditions', nargs='+', help='Conditions to analyze')
    sequence_parser.add_argument('--timepoints', nargs='+', help='Timepoints to analyze')
    sequence_parser.add_argument('--regions', nargs='+', help='Regions to analyze')
    sequence_parser.add_argument('--segmentation-channel', help='Segmentation channel')
    sequence_parser.add_argument('--analysis-channels', nargs='+', help='Analysis channels')
    sequence_parser.add_argument('--bins', type=int, default=5, help='Number of bins for cell grouping')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get current execution status')
    
    # Cancel command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel currently running execution')
    
    # List steps command
    list_steps_parser = subparsers.add_parser('list-steps', help='List available workflow steps')
    
    # Register handler command
    register_parser = subparsers.add_parser('register', help='Register a custom step handler')
    register_parser.add_argument('step_id', help='ID of the step to register')
    register_parser.add_argument('--handler', required=True, help='Python function to handle step execution')
    
    # Test step command
    test_parser = subparsers.add_parser('test', help='Test a workflow step without full execution')
    test_parser.add_argument('step_id', help='ID of the step to test')
    test_parser.add_argument('--input', required=True, help='Input directory path')
    test_parser.add_argument('--output', required=True, help='Output directory path')
    test_parser.add_argument('--dry-run', action='store_true', help='Perform dry run without actual execution')
    
    return parser


def _execute_workflow(args) -> None:
    """
    Execute a complete workflow.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_execution_service')
        
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
        
        print(f"🚀 Executing workflow: {args.workflow_id}")
        print(f"   Input: {args.input}")
        print(f"   Output: {args.output}")
        if workflow_params:
            print(f"   Parameters: {workflow_params}")
        print()
        
        # Execute the workflow
        result = service.execute_workflow_with_dependencies(
            workflow_id=args.workflow_id,
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
                    print(f"   • {step['step_id']}: {step['message']} ({step['duration']:.2f}s)")
            
            sys.exit(0)
        else:
            print(f"❌ Workflow execution failed!")
            print(f"   Error: {result['error']}")
            
            if result['steps_failed']:
                print("\n❌ Failed steps:")
                for step in result['steps_failed']:
                    print(f"   • {step['step_id']}: {step['error']} ({step['duration']:.2f}s)")
            
            sys.exit(1)
            
    except Exception as e:
        print(f"Error executing workflow: {e}")
        sys.exit(1)


def _execute_workflow_step(args) -> None:
    """
    Execute a single workflow step.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_execution_service')
        
        # Prepare step parameters
        step_params = {
            'imagej_path': args.imagej_path,
            'conditions': args.conditions,
            'timepoints': args.timepoints,
            'regions': args.regions,
            'segmentation_channel': args.segmentation_channel,
            'analysis_channels': args.analysis_channels,
            'bins': args.bins
        }
        
        # Remove None values
        step_params = {k: v for k, v in step_params.items() if v is not None}
        
        print(f"🚀 Executing workflow step: {args.step_id}")
        print(f"   Input: {args.input}")
        print(f"   Output: {args.output}")
        if step_params:
            print(f"   Parameters: {step_params}")
        print()
        
        # Execute the step
        result = service.execute_workflow_step(
            step_id=args.step_id,
            input_dir=args.input,
            output_dir=args.output,
            **step_params
        )
        
        if result['success']:
            print("✅ Workflow step executed successfully!")
            print(f"   Duration: {result['duration']:.2f} seconds")
            print(f"   Message: {result['message']}")
            
            if 'output' in result:
                print(f"   Output: {result['output']}")
            
            sys.exit(0)
        else:
            print(f"❌ Workflow step execution failed!")
            print(f"   Error: {result['error']}")
            print(f"   Duration: {result['duration']:.2f} seconds")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error executing workflow step: {e}")
        sys.exit(1)


def _execute_workflow_sequence(args) -> None:
    """
    Execute a sequence of workflow steps.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_execution_service')
        
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
        
        print(f"🚀 Executing workflow sequence: {args.workflow_id}")
        print(f"   Steps: {', '.join(args.steps)}")
        print(f"   Input: {args.input}")
        print(f"   Output: {args.output}")
        if workflow_params:
            print(f"   Parameters: {workflow_params}")
        print()
        
        # Execute the sequence
        result = service.execute_workflow_sequence(
            workflow_id=args.workflow_id,
            step_sequence=args.steps,
            input_dir=args.input,
            output_dir=args.output,
            **workflow_params
        )
        
        if result['success']:
            print("✅ Workflow sequence executed successfully!")
            print(f"   Duration: {result['total_duration']:.2f} seconds")
            print(f"   Steps completed: {len(result['steps_completed'])}")
            print(f"   Steps failed: {len(result['steps_failed'])}")
            
            if result['steps_completed']:
                print("\n📋 Completed steps:")
                for step in result['steps_completed']:
                    print(f"   • {step['step_id']}: {step['message']} ({step['duration']:.2f}s)")
            
            sys.exit(0)
        else:
            print(f"❌ Workflow sequence execution failed!")
            print(f"   Error: {result['error']}")
            
            if result['steps_failed']:
                print("\n❌ Failed steps:")
                for step in result['steps_failed']:
                    print(f"   • {step['step_id']}: {step['error']} ({step['duration']:.2f}s)")
            
            sys.exit(1)
            
    except Exception as e:
        print(f"Error executing workflow sequence: {e}")
        sys.exit(1)


def _get_execution_status() -> None:
    """
    Get the current execution status.
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_execution_service')
        
        status = service.get_execution_status()
        
        if not status:
            print("📊 No workflow execution is currently running.")
            sys.exit(0)
        
        print("📊 Current Workflow Execution Status")
        print("=" * 60)
        print(f"Execution ID: {status['id']}")
        print(f"Workflow ID: {status['workflow_id']}")
        print(f"Status: {status['status']}")
        print(f"Start Time: {status['start_time']}")
        
        if status['current_step']:
            print(f"Current Step: {status['current_step']}")
        
        if status['status'] == 'running':
            print("🔄 Execution is currently running...")
        elif status['status'] == 'completed':
            print("✅ Execution completed successfully!")
        elif status['status'] == 'failed':
            print("❌ Execution failed!")
        elif status['status'] == 'cancelled':
            print("🛑 Execution was cancelled!")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error getting execution status: {e}")
        sys.exit(1)


def _cancel_execution() -> None:
    """
    Cancel the currently running execution.
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_execution_service')
        
        print("🛑 Cancelling currently running workflow execution...")
        print()
        
        result = service.cancel_current_execution()
        
        if result['success']:
            print(f"✅ {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to cancel execution: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error cancelling execution: {e}")
        sys.exit(1)


def _list_available_steps() -> None:
    """
    List available workflow steps.
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_execution_service')
        
        steps = service.get_available_steps()
        
        if not steps:
            print("❌ No workflow steps are available.")
            sys.exit(1)
        
        print("📋 Available Workflow Steps")
        print("=" * 40)
        
        for step_id in steps:
            print(f"   • {step_id}")
        
        print("=" * 40)
        print(f"Total steps: {len(steps)}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error listing available steps: {e}")
        sys.exit(1)


def _register_step_handler(args) -> None:
    """
    Register a custom step handler.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        print(f"⚠️  Custom step handler registration is not yet implemented.")
        print(f"   Step ID: {args.step_id}")
        print(f"   Handler: {args.handler}")
        print(f"   This feature will be available in future versions.")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error registering step handler: {e}")
        sys.exit(1)


def _test_workflow_step(args) -> None:
    """
    Test a workflow step without full execution.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_execution_service')
        
        # Prepare step parameters
        step_params = {
            'imagej_path': args.imagej_path,
            'conditions': args.conditions,
            'timepoints': args.timepoints,
            'regions': args.regions,
            'segmentation_channel': args.segmentation_channel,
            'analysis_channels': args.analysis_channels,
            'bins': args.bins,
            'dry_run': args.dry_run
        }
        
        # Remove None values
        step_params = {k: v for k, v in step_params.items() if v is not None}
        
        print(f"🧪 Testing workflow step: {args.step_id}")
        print(f"   Input: {args.input}")
        print(f"   Output: {args.output}")
        if args.dry_run:
            print(f"   Mode: DRY RUN (no actual execution)")
        if step_params:
            print(f"   Parameters: {step_params}")
        print()
        
        if args.dry_run:
            print("✅ Dry run completed successfully!")
            print("   No actual execution performed.")
            print("   Step would execute with the provided parameters.")
            sys.exit(0)
        else:
            # Execute the step in test mode
            result = service.execute_workflow_step(
                step_id=args.step_id,
                input_dir=args.input,
                output_dir=args.output,
                **step_params
            )
            
            if result['success']:
                print("✅ Workflow step test completed successfully!")
                print(f"   Duration: {result['duration']:.2f} seconds")
                print(f"   Message: {result['message']}")
                
                if 'output' in result:
                    print(f"   Output: {result['output']}")
                
                sys.exit(0)
            else:
                print(f"❌ Workflow step test failed!")
                print(f"   Error: {result['error']}")
                print(f"   Duration: {result['duration']:.2f} seconds")
                sys.exit(1)
            
    except Exception as e:
        print(f"Error testing workflow step: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the workflow execution CLI.
    """
    parser = _create_parser()
    args = parser.parse_args()
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command handler
    if args.command == 'execute':
        _execute_workflow(args)
    elif args.command == 'step':
        _execute_workflow_step(args)
    elif args.command == 'sequence':
        _execute_workflow_sequence(args)
    elif args.command == 'status':
        _get_execution_status()
    elif args.command == 'cancel':
        _cancel_execution()
    elif args.command == 'list-steps':
        _list_available_steps()
    elif args.command == 'register':
        _register_step_handler(args)
    elif args.command == 'test':
        _test_workflow_step(args)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
