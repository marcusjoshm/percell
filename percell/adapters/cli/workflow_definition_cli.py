#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI Adapter for Workflow Definition Service

This module provides a command-line interface for the WorkflowDefinitionService,
allowing users to manage workflow definitions, configurations, and metadata.
"""

import argparse
import sys
from pathlib import Path
from percell.main.composition_root import get_composition_root


def _create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the workflow definition CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Manage workflow definitions, configurations, and metadata'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List workflows command
    list_parser = subparsers.add_parser('list', help='List all workflow definitions')
    list_parser.add_argument('--category', help='Filter by workflow category')
    list_parser.add_argument('--tag', help='Filter by workflow tag')
    list_parser.add_argument('--format', choices=['table', 'json', 'yaml'], default='table', help='Output format')
    
    # Show workflow command
    show_parser = subparsers.add_parser('show', help='Show detailed workflow definition')
    show_parser.add_argument('workflow_id', help='ID of the workflow to show')
    show_parser.add_argument('--format', choices=['table', 'json', 'yaml'], default='table', help='Output format')
    
    # Create workflow command
    create_parser = subparsers.add_parser('create', help='Create a custom workflow definition')
    create_parser.add_argument('--file', required=True, help='JSON file containing workflow definition')
    
    # Update workflow command
    update_parser = subparsers.add_parser('update', help='Update an existing workflow definition')
    update_parser.add_argument('workflow_id', help='ID of the workflow to update')
    update_parser.add_argument('--file', required=True, help='JSON file containing workflow updates')
    
    # Delete workflow command
    delete_parser = subparsers.add_parser('delete', help='Delete a custom workflow definition')
    delete_parser.add_argument('workflow_id', help='ID of the workflow to delete')
    delete_parser.add_argument('--force', action='store_true', help='Force deletion without confirmation')
    
    # Validate workflow command
    validate_parser = subparsers.add_parser('validate', help='Validate workflow definition')
    validate_parser.add_argument('--file', required=True, help='JSON file containing workflow definition to validate')
    
    # Export workflow command
    export_parser = subparsers.add_parser('export', help='Export workflow definition to file')
    export_parser.add_argument('workflow_id', help='ID of the workflow to export')
    export_parser.add_argument('--format', choices=['json', 'yaml'], default='json', help='Export format')
    export_parser.add_argument('--output', help='Output file path (default: stdout)')
    
    # Get steps command
    steps_parser = subparsers.add_parser('steps', help='Get workflow steps')
    steps_parser.add_argument('workflow_id', help='ID of the workflow')
    
    # Get dependencies command
    deps_parser = subparsers.add_parser('dependencies', help='Get workflow dependencies')
    deps_parser.add_argument('workflow_id', help='ID of the workflow')
    
    # Validate execution order command
    order_parser = subparsers.add_parser('validate-order', help='Validate workflow execution order')
    order_parser.add_argument('workflow_id', help='ID of the workflow to validate')
    
    return parser


def _list_workflows(args) -> None:
    """
    List all workflow definitions.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        # Get workflows based on filters
        if args.category:
            workflows = service.get_workflows_by_category(args.category)
            workflows_dict = {w['id']: w for w in workflows}
        elif args.tag:
            workflows = service.get_workflows_by_tag(args.tag)
            workflows_dict = {w['id']: w for w in workflows}
        else:
            workflows_dict = service.get_all_workflow_definitions()
        
        if not workflows_dict:
            print("No workflows found.")
            sys.exit(0)
        
        # Format output
        if args.format == 'json':
            import json
            print(json.dumps(workflows_dict, indent=2))
        elif args.format == 'yaml':
            try:
                import yaml
                print(yaml.dump(workflows_dict, default_flow_style=False, indent=2))
            except ImportError:
                print("YAML output requires PyYAML package. Falling back to table format.")
                _print_workflows_table(workflows_dict)
        else:
            _print_workflows_table(workflows_dict)
        
        print(f"\n✅ Total workflows: {len(workflows_dict)}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error listing workflows: {e}")
        sys.exit(1)


def _print_workflows_table(workflows: dict) -> None:
    """
    Print workflows in table format.
    
    Args:
        workflows: Dictionary of workflow definitions
    """
    print("📋 Available Workflows")
    print("=" * 100)
    print(f"{'ID':<20} {'Name':<30} {'Category':<15} {'Steps':<8} {'Duration':<15}")
    print("-" * 100)
    
    for workflow_id, workflow in workflows.items():
        name = workflow.get('name', 'Unknown')[:29]
        category = workflow.get('category', 'Unknown')[:14]
        steps_count = len(workflow.get('steps', []))
        duration = workflow.get('estimated_total_duration', 'Unknown')[:14]
        
        print(f"{workflow_id:<20} {name:<30} {category:<15} {steps_count:<8} {duration:<15}")
    
    print("-" * 100)


def _show_workflow(args) -> None:
    """
    Show detailed workflow definition.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        workflow = service.get_workflow_definition(args.workflow_id)
        if not workflow:
            print(f"❌ Workflow '{args.workflow_id}' not found")
            sys.exit(1)
        
        # Format output
        if args.format == 'json':
            import json
            print(json.dumps(workflow, indent=2))
        elif args.format == 'yaml':
            try:
                import yaml
                print(yaml.dump(workflow, default_flow_style=False, indent=2))
            except ImportError:
                print("YAML output requires PyYAML package. Falling back to table format.")
                _print_workflow_details(workflow)
        else:
            _print_workflow_details(workflow)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error showing workflow: {e}")
        sys.exit(1)


def _print_workflow_details(workflow: dict) -> None:
    """
    Print workflow details in table format.
    
    Args:
        workflow: Workflow definition dictionary
    """
    print(f"📋 Workflow: {workflow['name']}")
    print("=" * 80)
    print(f"ID: {workflow['id']}")
    print(f"Description: {workflow['description']}")
    print(f"Category: {workflow.get('category', 'Unknown')}")
    print(f"Version: {workflow.get('version', 'Unknown')}")
    print(f"Estimated Duration: {workflow.get('estimated_total_duration', 'Unknown')}")
    print(f"Requirements: {', '.join(workflow.get('requirements', []))}")
    print(f"Tags: {', '.join(workflow.get('tags', []))}")
    print(f"Created: {workflow.get('created_date', 'Unknown')}")
    print(f"Modified: {workflow.get('last_modified', 'Unknown')}")
    
    print(f"\n📋 Steps ({len(workflow.get('steps', []))} total):")
    print("-" * 80)
    print(f"{'Order':<6} {'ID':<20} {'Name':<25} {'Duration':<15} {'Required':<10}")
    print("-" * 80)
    
    for step in workflow.get('steps', []):
        order = step.get('order', 0)
        step_id = step.get('id', 'Unknown')[:19]
        name = step.get('name', 'Unknown')[:24]
        duration = step.get('estimated_duration', 'Unknown')[:14]
        required = 'Yes' if step.get('required', False) else 'No'
        
        print(f"{order:<6} {step_id:<20} {name:<25} {duration:<15} {required:<10}")
    
    print("-" * 80)


def _create_workflow(args) -> None:
    """
    Create a custom workflow definition.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        # Read workflow definition from file
        if not Path(args.file).exists():
            print(f"❌ Workflow definition file not found: {args.file}")
            sys.exit(1)
        
        with open(args.file, 'r') as f:
            import json
            workflow_definition = json.load(f)
        
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        result = service.create_custom_workflow(workflow_definition)
        
        if result['success']:
            print(f"✅ Custom workflow '{result['workflow_id']}' created successfully!")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to create workflow: {result['error']}")
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in workflow definition file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating workflow: {e}")
        sys.exit(1)


def _update_workflow(args) -> None:
    """
    Update an existing workflow definition.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        # Read workflow updates from file
        if not Path(args.file).exists():
            print(f"❌ Workflow updates file not found: {args.file}")
            sys.exit(1)
        
        with open(args.file, 'r') as f:
            import json
            updates = json.load(f)
        
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        result = service.update_workflow_definition(args.workflow_id, updates)
        
        if result['success']:
            print(f"✅ Workflow '{result['workflow_id']}' updated successfully!")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to update workflow: {result['error']}")
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in workflow updates file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error updating workflow: {e}")
        sys.exit(1)


def _delete_workflow(args) -> None:
    """
    Delete a custom workflow definition.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        # Check if workflow exists
        workflow = service.get_workflow_definition(args.workflow_id)
        if not workflow:
            print(f"❌ Workflow '{args.workflow_id}' not found")
            sys.exit(1)
        
        # Check if it's a default workflow
        if workflow.get('created_date') == '2024-01-01':  # Default workflows
            print(f"❌ Cannot delete default workflow '{args.workflow_id}'")
            sys.exit(1)
        
        # Confirm deletion
        if not args.force:
            confirm = input(f"Are you sure you want to delete workflow '{args.workflow_id}'? (y/N): ")
            if confirm.lower() != 'y':
                print("Deletion cancelled.")
                sys.exit(0)
        
        result = service.delete_custom_workflow(args.workflow_id)
        
        if result['success']:
            print(f"✅ Workflow '{result['workflow_id']}' deleted successfully!")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to delete workflow: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error deleting workflow: {e}")
        sys.exit(1)


def _validate_workflow(args) -> None:
    """
    Validate workflow definition.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        # Read workflow definition from file
        if not Path(args.file).exists():
            print(f"❌ Workflow definition file not found: {args.file}")
            sys.exit(1)
        
        with open(args.file, 'r') as f:
            import json
            workflow_definition = json.load(f)
        
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        # Validate the workflow definition
        validation_result = service._validate_workflow_definition(workflow_definition)
        
        if validation_result['valid']:
            print("✅ Workflow definition is valid!")
            print("   All required fields are present and properly formatted.")
            sys.exit(0)
        else:
            print("❌ Workflow definition validation failed!")
            print("\nErrors:")
            for error in validation_result['errors']:
                print(f"   • {error}")
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in workflow definition file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error validating workflow: {e}")
        sys.exit(1)


def _export_workflow(args) -> None:
    """
    Export workflow definition to file.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        result = service.export_workflow_definition(args.workflow_id, args.format)
        
        if result['success']:
            if args.output:
                # Write to file
                with open(args.output, 'w') as f:
                    f.write(result['content'])
                print(f"✅ Workflow '{args.workflow_id}' exported to {args.output}")
            else:
                # Write to stdout
                print(result['content'])
            
            print(f"   Format: {result['format']}")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ Failed to export workflow: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error exporting workflow: {e}")
        sys.exit(1)


def _get_workflow_steps(args) -> None:
    """
    Get workflow steps.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        steps = service.get_workflow_steps(args.workflow_id)
        
        if not steps:
            print(f"❌ No steps found for workflow '{args.workflow_id}'")
            sys.exit(1)
        
        print(f"📋 Steps for workflow '{args.workflow_id}':")
        print("=" * 80)
        print(f"{'Order':<6} {'ID':<20} {'Name':<25} {'Duration':<15} {'Required':<10}")
        print("-" * 80)
        
        for step in steps:
            order = step.get('order', 0)
            step_id = step.get('id', 'Unknown')[:19]
            name = step.get('name', 'Unknown')[:24]
            duration = step.get('estimated_duration', 'Unknown')[:14]
            required = 'Yes' if step.get('required', False) else 'No'
            
            print(f"{order:<6} {step_id:<20} {name:<25} {duration:<15} {required:<10}")
        
        print("-" * 80)
        print(f"Total steps: {len(steps)}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error getting workflow steps: {e}")
        sys.exit(1)


def _get_workflow_dependencies(args) -> None:
    """
    Get workflow dependencies.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        dependencies = service.get_workflow_dependencies(args.workflow_id)
        
        if not dependencies:
            print(f"❌ No dependencies found for workflow '{args.workflow_id}'")
            sys.exit(1)
        
        print(f"🔗 Dependencies for workflow '{args.workflow_id}':")
        print("=" * 60)
        
        for step_id, deps in dependencies.items():
            if deps:
                print(f"{step_id}: {', '.join(deps)}")
            else:
                print(f"{step_id}: (no dependencies)")
        
        print("=" * 60)
        sys.exit(0)
        
    except Exception as e:
        print(f"Error getting workflow dependencies: {e}")
        sys.exit(1)


def _validate_execution_order(args) -> None:
    """
    Validate workflow execution order.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        composition_root = get_composition_root()
        service = composition_root.get_service('workflow_definition_service')
        
        result = service.validate_workflow_execution_order(args.workflow_id)
        
        if result['valid']:
            print("✅ Workflow execution order is valid!")
            print(f"   {result['message']}")
            sys.exit(0)
        else:
            print("❌ Workflow execution order validation failed!")
            print(f"   {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error validating workflow execution order: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the workflow definition CLI.
    """
    parser = _create_parser()
    args = parser.parse_args()
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command handler
    if args.command == 'list':
        _list_workflows(args)
    elif args.command == 'show':
        _show_workflow(args)
    elif args.command == 'create':
        _create_workflow(args)
    elif args.command == 'update':
        _update_workflow(args)
    elif args.command == 'delete':
        _delete_workflow(args)
    elif args.command == 'validate':
        _validate_workflow(args)
    elif args.command == 'export':
        _export_workflow(args)
    elif args.command == 'steps':
        _get_workflow_steps(args)
    elif args.command == 'dependencies':
        _get_workflow_dependencies(args)
    elif args.command == 'validate-order':
        _validate_execution_order(args)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
