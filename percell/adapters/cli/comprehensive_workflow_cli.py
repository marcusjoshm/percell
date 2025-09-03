#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Workflow CLI

This module provides a command-line interface for the ComprehensiveWorkflowService,
allowing users to execute complex workflows from the command line.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional
from percell.domain.exceptions import DomainError


class ComprehensiveWorkflowCLI:
    """
    Command-line interface for comprehensive workflow execution.
    
    This CLI provides access to the ComprehensiveWorkflowService for executing
    complex analysis workflows from the command line.
    """
    
    def __init__(self, composition_root):
        """
        Initialize the comprehensive workflow CLI.
        
        Args:
            composition_root: The composition root containing all services
        """
        self.composition_root = composition_root
        self.service = composition_root.get_service('comprehensive_workflow_service')
    
    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create the argument parser for the comprehensive workflow CLI.
        
        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description='Execute comprehensive workflows using hexagonal architecture',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Execute complete analysis workflow
  comprehensive-workflow --complete --input /path/to/data --output /path/to/results --channels ch00 ch01 ch02
  
  # Execute segmentation-only workflow
  comprehensive-workflow --segmentation --input /path/to/data --output /path/to/results --conditions cond1 cond2
  
  # Execute analysis-only workflow
  comprehensive-workflow --analysis --output /path/to/results --channels ch00 ch01 --imagej /path/to/imagej
  
  # Execute single-cell processing workflow
  comprehensive-workflow --single-cell --output /path/to/results --channels ch00 ch01 --timepoints t0 t1 t2
            """
        )
        
        # Workflow type selection (mutually exclusive)
        workflow_group = parser.add_mutually_exclusive_group(required=True)
        workflow_group.add_argument(
            '--complete',
            action='store_true',
            help='Execute complete end-to-end analysis workflow'
        )
        workflow_group.add_argument(
            '--segmentation',
            action='store_true',
            help='Execute segmentation-only workflow'
        )
        workflow_group.add_argument(
            '--analysis',
            action='store_true',
            help='Execute analysis-only workflow on existing segmentation data'
        )
        workflow_group.add_argument(
            '--single-cell',
            action='store_true',
            help='Execute single-cell processing workflow'
        )
        
        # Common arguments
        parser.add_argument(
            '--input', '-i',
            type=str,
            help='Input directory containing raw data (required for complete and segmentation workflows)'
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            required=True,
            help='Output directory for results'
        )
        parser.add_argument(
            '--channels',
            nargs='+',
            help='Analysis channels to process (e.g., ch00 ch01 ch02)'
        )
        parser.add_argument(
            '--imagej',
            type=str,
            help='Path to ImageJ executable (required for complete and analysis workflows)'
        )
        
        # Workflow-specific arguments
        parser.add_argument(
            '--conditions',
            nargs='+',
            help='Conditions to process (e.g., control treatment)'
        )
        parser.add_argument(
            '--regions',
            nargs='+',
            help='Regions to process (e.g., region1 region2)'
        )
        parser.add_argument(
            '--timepoints',
            nargs='+',
            help='Timepoints to process (e.g., t0 t1 t2)'
        )
        parser.add_argument(
            '--segmentation-channel',
            type=str,
            help='Channel to use for segmentation'
        )
        parser.add_argument(
            '--bins',
            type=int,
            default=5,
            help='Number of bins for cell grouping (default: 5)'
        )
        
        # Output options
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be executed without actually running'
        )
        
        return parser
    
    def execute_workflow(self, args) -> int:
        """
        Execute the selected workflow based on command line arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Validate required arguments based on workflow type
            if not self._validate_arguments(args):
                return 1
            
            if args.dry_run:
                return self._show_dry_run(args)
            
            # Execute the selected workflow
            if args.complete:
                return self._execute_complete_workflow(args)
            elif args.segmentation:
                return self._execute_segmentation_workflow(args)
            elif args.analysis:
                return self._execute_analysis_workflow(args)
            elif args.single_cell:
                return self._execute_single_cell_workflow(args)
            else:
                print("Error: No workflow type selected")
                return 1
                
        except Exception as e:
            print(f"Error executing workflow: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _validate_arguments(self, args) -> bool:
        """
        Validate that all required arguments are provided for the selected workflow.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            True if validation passes, False otherwise
        """
        errors = []
        
        # Check input directory for workflows that need it
        if args.complete or args.segmentation:
            if not args.input:
                errors.append("--input is required for complete and segmentation workflows")
            elif not Path(args.input).exists():
                errors.append(f"Input directory does not exist: {args.input}")
        
        # Check ImageJ path for workflows that need it
        if args.complete or args.analysis:
            if not args.imagej:
                errors.append("--imagej is required for complete and analysis workflows")
            elif not Path(args.imagej).exists():
                errors.append(f"ImageJ executable does not exist: {args.imagej}")
        
        # Check channels for workflows that need them
        if args.complete or args.analysis or args.single_cell:
            if not args.channels:
                errors.append("--channels is required for complete, analysis, and single-cell workflows")
        
        # Check output directory
        if not args.output:
            errors.append("--output is required")
        
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def _show_dry_run(self, args) -> int:
        """
        Show what would be executed without actually running.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success)
        """
        print("DRY RUN - No actual execution will occur")
        print("=" * 50)
        
        if args.complete:
            print("Workflow: Complete Analysis")
            print(f"Input: {args.input}")
            print(f"Output: {args.output}")
            print(f"Channels: {args.channels}")
            print(f"ImageJ: {args.imagej}")
            print(f"Bins: {args.bins}")
            if args.conditions:
                print(f"Conditions: {args.conditions}")
            if args.regions:
                print(f"Regions: {args.regions}")
            if args.timepoints:
                print(f"Timepoints: {args.timepoints}")
                
        elif args.segmentation:
            print("Workflow: Segmentation Only")
            print(f"Input: {args.input}")
            print(f"Output: {args.output}")
            if args.conditions:
                print(f"Conditions: {args.conditions}")
            if args.regions:
                print(f"Regions: {args.regions}")
            if args.timepoints:
                print(f"Timepoints: {args.timepoints}")
            if args.channels:
                print(f"Channels: {args.channels}")
                
        elif args.analysis:
            print("Workflow: Analysis Only")
            print(f"Output: {args.output}")
            print(f"Channels: {args.channels}")
            print(f"ImageJ: {args.imagej}")
            if args.regions:
                print(f"Regions: {args.regions}")
            if args.timepoints:
                print(f"Timepoints: {args.timepoints}")
                
        elif args.single_cell:
            print("Workflow: Single Cell Processing")
            print(f"Output: {args.output}")
            print(f"Channels: {args.channels}")
            if args.timepoints:
                print(f"Timepoints: {args.timepoints}")
        
        print("=" * 50)
        return 0
    
    def _execute_complete_workflow(self, args) -> int:
        """
        Execute the complete analysis workflow.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        print("Executing complete analysis workflow...")
        
        result = self.service.execute_complete_workflow(
            input_dir=args.input,
            output_dir=args.output,
            analysis_channels=args.channels,
            imagej_path=args.imagej,
            conditions=args.conditions,
            regions=args.regions,
            timepoints=args.timepoints,
            segmentation_channel=args.segmentation_channel,
            bins=args.bins
        )
        
        if result['success']:
            print(f"✅ Workflow completed successfully in {result['total_duration']:.2f} seconds")
            return 0
        else:
            print(f"❌ Workflow failed after {result['total_duration']:.2f} seconds")
            for error in result['errors']:
                print(f"  - {error}")
            return 1
    
    def _execute_segmentation_workflow(self, args) -> int:
        """
        Execute the segmentation-only workflow.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        print("Executing segmentation workflow...")
        
        result = self.service.execute_segmentation_workflow(
            input_dir=args.input,
            output_dir=args.output,
            conditions=args.conditions,
            regions=args.regions,
            timepoints=args.timepoints,
            channels=args.channels
        )
        
        if result['success']:
            print(f"✅ Workflow completed successfully in {result['total_duration']:.2f} seconds")
            return 0
        else:
            print(f"❌ Workflow failed after {result['total_duration']:.2f} seconds")
            for error in result['errors']:
                print(f"  - {error}")
            return 1
    
    def _execute_analysis_workflow(self, args) -> int:
        """
        Execute the analysis-only workflow.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        print("Executing analysis workflow...")
        
        result = self.service.execute_analysis_workflow(
            output_dir=args.output,
            analysis_channels=args.channels,
            imagej_path=args.imagej,
            regions=args.regions,
            timepoints=args.timepoints
        )
        
        if result['success']:
            print(f"✅ Workflow completed successfully in {result['total_duration']:.2f} seconds")
            return 0
        else:
            print(f"❌ Workflow failed after {result['total_duration']:.2f} seconds")
            for error in result['errors']:
                print(f"  - {error}")
            return 1
    
    def _execute_single_cell_workflow(self, args) -> int:
        """
        Execute the single-cell processing workflow.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        print("Executing single-cell processing workflow...")
        
        result = self.service.execute_single_cell_workflow(
            output_dir=args.output,
            analysis_channels=args.channels,
            timepoints=args.timepoints
        )
        
        if result['success']:
            print(f"✅ Workflow completed successfully in {result['total_duration']:.2f} seconds")
            return 0
        else:
            print(f"❌ Workflow failed after {result['total_duration']:.2f} seconds")
            for error in result['errors']:
                print(f"  - {error}")
            return 1


def main():
    """Main entry point for the comprehensive workflow CLI."""
    try:
        from percell.main.composition_root import get_composition_root
        
        # Get the composition root
        composition_root = get_composition_root()
        
        # Create and run the CLI
        cli = ComprehensiveWorkflowCLI(composition_root)
        parser = cli.create_parser()
        args = parser.parse_args()
        
        # Execute the workflow
        exit_code = cli.execute_workflow(args)
        sys.exit(exit_code)
        
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
