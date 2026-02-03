from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Microscopy Per Cell Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete analysis workflow
  percell --input /path/to/data --output /path/to/output --complete-workflow
  
  # Run data selection
  percell --input /path/to/data --output /path/to/output --data-selection
  
  # Run segmentation
  percell --input /path/to/data --output /path/to/output --segmentation
  
  # Run analysis
  percell --input /path/to/data --output /path/to/output --analysis
  
  # Run cleanup
  percell --output /path/to/output --cleanup
        """
    )

    # Input/Output arguments
    parser.add_argument('--input', '-i', type=str, help='Input directory containing microscopy data')
    parser.add_argument('--output', '-o', type=str, help='Output directory for results')
    parser.add_argument('--config', type=str, help='Path to configuration file (default: uses package config)')

    # Processing options
    parser.add_argument('--data-selection', action='store_true', help='Run data selection (conditions, regions, timepoints, channels)')
    parser.add_argument('--cellpose-segmentation', action='store_true', help='Run single-cell segmentation (bin images and launch Cellpose)')
    parser.add_argument('--process-cellpose-single-cell', action='store_true', help='Run single-cell data processing (tracking, resizing, extraction, grouping)')
    parser.add_argument('--semi-auto-threshold-grouped-cells', action='store_true', help='Run threshold grouped cells (interactive ImageJ thresholding)')
    parser.add_argument('--full-auto-threshold-grouped-cells', action='store_true', help='Run threshold grouped cells (automatic Otsu thresholding)')
    parser.add_argument('--measure-roi-area', action='store_true', help='Run ROI area measurement (measure areas of ROIs in raw images)')
    parser.add_argument('--analysis', action='store_true', help='Run analysis (combine masks, create cell masks, export results)')
    parser.add_argument('--cleanup', action='store_true', help='Clean up directories (empty cells and masks directories to free space, preserves grouped/combined data)')
    parser.add_argument('--complete-workflow', action='store_true', help='Run complete analysis workflow (all 6 stages)')
    parser.add_argument('--advanced-workflow', action='store_true', help='Run advanced workflow builder (custom sequence of steps)')

    # Data selection arguments
    parser.add_argument('--datatype', choices=['single_timepoint', 'multi_timepoint'], help='Data type to analyze')
    parser.add_argument('--conditions', nargs='+', help='Specific conditions to analyze')
    parser.add_argument('--timepoints', nargs='+', help='Specific timepoints to analyze')
    parser.add_argument('--regions', nargs='+', help='Specific regions to analyze')
    parser.add_argument('--segmentation-channel', help='Channel to use for segmentation')
    parser.add_argument('--analysis-channels', nargs='+', help='Channels to analyze')
    parser.add_argument('--bins', type=int, default=5, help='Number of bins for cell grouping (default: 5)')

    # Control arguments
    parser.add_argument('--skip-steps', nargs='+', help='Steps to skip in the workflow')
    parser.add_argument('--start-from', help='Step to start the workflow from')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--interactive', '-I', action='store_true', help='Run in interactive mode')

    return parser


