"""
Command Line Interface for Microscopy Single-Cell Analysis Pipeline

Handles argument parsing, user interaction, and menu systems.
"""

import argparse
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path

# ANSI color codes for rainbow effect
class Colors:
    red = '\033[31m'
    orange = '\033[38;5;208m'
    yellow = '\033[33m'
    green = '\033[32m'
    blue = '\033[34m'
    indigo = '\033[38;5;54m'
    violet = '\033[35m'
    magenta = '\033[95m'
    reset = '\033[0m'
    bold = '\033[1m'

def colorize(text: str, color: str) -> str:
    """Apply color to text"""
    return f"{Colors.bold}{color}{text}{Colors.reset}"

def show_header() -> None:
    """Display colorful Per Cell ASCII art header"""
    header = [
        "         ███████╗ ████████╗███████╗ ███████╗████████╗██╗      ██╗               ",
        "         ██╔═══██╗██╔═════╝██╔═══██╗██╔════╝██╔═════╝██║      ██║               ",
        "         ███████╔╝███████╗ ███████╔╝██║     ███████╗ ██║      ██║               ",
        "         ██╔════╝ ██╔════╝ ██╔═══██╗██║     ██╔════╝ ██║      ██║               ",
        "         ██║      ████████╗██║   ██║███████╗████████╗████████╗████████╗         ",
        "         ╚═╝      ╚═══════╝╚═╝   ╚═╝╚══════╝╚═══════╝╚═══════╝╚═══════╝         "
    ]

    rainbow_colors = [
        Colors.red,
        Colors.orange, 
        Colors.yellow,
        Colors.green,
        Colors.blue,
        Colors.indigo,
        Colors.violet
    ]

    print('')  # Empty line at start
    
    for i, line in enumerate(header):
        if i < 0 or i > 20:  # Empty lines
            print(line)
        else:
            # Color the line with specific colors for PER and CELL
            colored_line = ""
            for j, char in enumerate(line):
                # Color based on column position
                if 1 <= j <= 35:  # PER section (columns 11-38)
                    colored_line += colorize(char, Colors.green)
                elif 36 <= j <= 80:  # CELL section (columns 39-80)
                    colored_line += colorize(char, Colors.magenta)
                else:  # Other characters
                    colored_line += char
            print(colored_line)


class CLIError(Exception):
    """Custom exception for CLI-related errors."""
    pass


class PipelineCLI:
    """
    Command line interface for the microscopy single-cell analysis pipeline.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
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
            """
        )
        
        # Input/Output arguments
        parser.add_argument(
            '--input', '-i',
            type=str,
            help='Input directory containing microscopy data'
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            help='Output directory for results'
        )
        parser.add_argument(
            '--config',
            type=str,
            default='src/config/config.json',
            help='Path to configuration file (default: src/config/config.json)'
        )
        
        # Processing options
        parser.add_argument(
            '--data-selection',
            action='store_true',
            help='Run data selection (conditions, regions, timepoints, channels)'
        )
        parser.add_argument(
            '--segmentation',
            action='store_true',
            help='Run single-cell segmentation (bin images and launch Cellpose)'
        )
        parser.add_argument(
            '--process-single-cell',
            action='store_true',
            help='Run single-cell data processing (tracking, resizing, extraction, grouping)'
        )
        parser.add_argument(
            '--threshold-grouped-cells',
            action='store_true',
            help='Run threshold grouped cells (interactive ImageJ thresholding)'
        )
        parser.add_argument(
            '--measure-roi-area',
            action='store_true',
            help='Run ROI area measurement (measure areas of ROIs in raw images)'
        )
        parser.add_argument(
            '--analysis',
            action='store_true',
            help='Run analysis (combine masks, create cell masks, export results)'
        )
        parser.add_argument(
            '--complete-workflow',
            action='store_true',
            help='Run complete analysis workflow (all 6 modules)'
        )
        
        # Data selection arguments
        parser.add_argument(
            '--datatype',
            choices=['single_timepoint', 'multi_timepoint'],
            help='Data type to analyze'
        )
        parser.add_argument(
            '--conditions',
            nargs='+',
            help='Specific conditions to analyze'
        )
        parser.add_argument(
            '--timepoints',
            nargs='+',
            help='Specific timepoints to analyze'
        )
        parser.add_argument(
            '--regions',
            nargs='+',
            help='Specific regions to analyze'
        )
        parser.add_argument(
            '--segmentation-channel',
            help='Channel to use for segmentation'
        )
        parser.add_argument(
            '--analysis-channels',
            nargs='+',
            help='Channels to analyze'
        )
        parser.add_argument(
            '--bins',
            type=int,
            default=5,
            help='Number of bins for cell grouping (default: 5)'
        )
        
        # Control arguments
        parser.add_argument(
            '--skip-steps',
            nargs='+',
            help='Steps to skip in the workflow'
        )
        parser.add_argument(
            '--start-from',
            help='Step to start the workflow from'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        parser.add_argument(
            '--interactive', '-I',
            action='store_true',
            help='Run in interactive mode'
        )
        
        return parser
    
    def parse_args(self, args: Optional[list] = None) -> argparse.Namespace:
        """
        Parse command line arguments.
        
        Args:
            args: Arguments to parse (default: sys.argv[1:])
            
        Returns:
            Parsed arguments
        """
        parsed_args = self.parser.parse_args(args)
        self._validate_args(parsed_args)
        return parsed_args
    
    def _validate_args(self, args: argparse.Namespace) -> None:
        """
        Validate parsed arguments.
        
        Args:
            args: Parsed arguments
            
        Raises:
            CLIError: If arguments are invalid
        """
        # Check if at least one processing option is selected (but allow menu to be shown)
        processing_options = ['complete', 'preprocess', 'segment', 'analyze', 
                            'data_exploration', 'roi_management', 'path_detection']
        selected_options = [opt for opt in processing_options if getattr(args, opt, False)]
        
        # Only validate if we're not in interactive mode and no options are selected
        if not selected_options and not args.interactive:
            # Don't raise error here - let the menu handle it
            pass
        
        # Load config to get default directories
        try:
            from ..modules.directory_setup import load_config
            config_path = getattr(args, 'config', 'src/config/config.json')
            config = load_config(config_path)
            default_input = config.get('directories', {}).get('input', '')
            default_output = config.get('directories', {}).get('output', '')
        except Exception:
            default_input = ''
            default_output = ''
        
        # Check if input/output directories are provided (only after menu processing)
        if not args.input and not args.interactive:
            if default_input:
                args.input = default_input
                print(f"Using default input directory: {default_input}")
            else:
                raise CLIError("Input directory is required unless using --interactive")
        
        if not args.output and not args.interactive:
            if default_output:
                args.output = default_output
                print(f"Using default output directory: {default_output}")
            else:
                raise CLIError("Output directory is required unless using --interactive")
    
    def show_interactive_menu(self, args: argparse.Namespace) -> argparse.Namespace:
        """
        Show interactive menu if no specific stages are selected.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Updated arguments with user selection
        """
        # Check if any stage is already selected
        stage_flags = [
            args.data_selection, args.segmentation, args.process_single_cell,
            args.threshold_grouped_cells, args.measure_roi_area, args.analysis, args.complete_workflow
        ]
        
        if any(stage_flags):
            return args  # Stage already selected, no need for menu
        
        # Show menu
        show_header()
        print("")
        print(colorize("🔬 Welcome single-cell microscopy analysis user! 🔬", Colors.bold))
        print("")
        print(colorize("MENU:", Colors.bold))
        print(colorize("1. Set Input/Output Directories", Colors.green))
        print(colorize("2. Run Complete Workflow", Colors.yellow))
        print(colorize("3. Data Selection (conditions, regions, timepoints, channels)", Colors.orange))
        print(colorize("4. Single-cell Segmentation (Cellpose)", Colors.orange))
        print(colorize("5. Process Single-cell Data (tracking, resizing, extraction, grouping)", Colors.orange))
        print(colorize("6. Threshold Grouped Cells (interactive ImageJ thresholding)", Colors.orange))
        print(colorize("7. Measure Cell Area (measure areas from single-cell ROIs)", Colors.orange))
        print(colorize("8. Analysis (combine masks, create cell masks, export results)", Colors.orange))
        print(colorize("9. Exit", Colors.red))
        
        # Get user choice
        try:
            choice = input("Select an option (1-9): ").strip().lower()
        except EOFError:
            print("\nEOF detected. Exiting gracefully.")
            return None
        
        # Update args based on choice
        if choice == "1":
            # Set directories only (no directory creation)
            try:
                from ..modules.set_directories import set_default_directories
                from ..modules.directory_setup import load_config, save_config
                
                # Load current config
                config_path = args.config if hasattr(args, 'config') else 'src/config/config.json'
                config = load_config(config_path)
                
                # Set default directories
                input_path, output_path = set_default_directories(config, config_path)
                
                # Update args with the new paths
                args.input = input_path
                args.output = output_path
                
                print(f"\n✅ Directories set successfully!")
                print(f"  Input: {input_path}")
                print(f"  Output: {output_path}")
                print(f"  Note: Directory structure will be created when running workflow modules")
                
            except ImportError as e:
                print(f"Error: Could not import set_directories module: {e}")
                # Fallback to simple input
                if not args.input:
                    args.input = self._get_directory_input("Enter input directory path: ")
                if not args.output:
                    args.output = self._get_directory_input("Enter output directory path: ")
        elif choice == "2":
            # Run complete workflow sequentially
            print("\n" + "="*60)
            print("Running Complete Workflow")
            print("This will execute all steps in sequence:")
            print("1. Data Selection (Option 3)")
            print("2. Single-cell Segmentation (Option 4)")
            print("3. Process Single-cell Data (Option 5)")
            print("4. Threshold Grouped Cells (Option 6)")
            print("5. Measure ROI Areas (Option 7)")
            print("6. Analysis (Option 8)")
            print("="*60 + "\n")
            
            # Set all stages to run sequentially
            args.data_selection = True
            args.segmentation = True
            args.process_single_cell = True
            args.threshold_grouped_cells = True
            args.measure_roi_area = True
            args.analysis = True
            args.complete_workflow = True  # Flag to indicate sequential execution
        elif choice == "3":
            args.data_selection = True
        elif choice == "4":
            args.segmentation = True
        elif choice == "5":
            args.process_single_cell = True
        elif choice == "6":
            args.threshold_grouped_cells = True
        elif choice == "7":
            args.measure_roi_area = True
        elif choice == "8":
            args.analysis = True
        elif choice == "9" or choice == "q" or choice == "quit":
            print("Exiting.")
            return None  # Signal to exit
        else:
            print("Invalid choice. Please enter a number between 1-9 or 'q' to quit.")
            return args  # Return current args to continue loop
        
        return args
    
    def _get_directory_input(self, prompt: str) -> str:
        """
        Get directory input from user.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Directory path
        """
        while True:
            try:
                directory = input(prompt).strip()
                if directory:
                    return directory
                print("Please enter a valid directory path.")
            except EOFError:
                print("\nEOF detected. Exiting gracefully.")
                raise
    
    def _setup_output_structure(self, input_dir: str, output_dir: str) -> bool:
        """
        Set up the output directory structure using the setup_output_structure.sh script.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess
            from pathlib import Path
            
            # Use the setup_output_structure.sh script
            script_path = Path("src/bash/setup_output_structure.sh")
            if not script_path.exists():
                print(f"Error: setup_output_structure.sh script not found: {script_path}")
                return False
            
            # Make sure the script is executable
            script_path.chmod(0o755)
            
            # Run the script
            result = subprocess.run([str(script_path), input_dir, output_dir], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error: setup_output_structure.sh failed: {result.stderr}")
                return False
            
            print(f"Script output: {result.stdout}")
            return True
            
        except Exception as e:
            print(f"Error setting up output structure: {e}")
            return False
    
    def get_choice(self, prompt: str, choices: list, default: int = 1) -> int:
        """
        Get user choice from a list of options.
        
        Args:
            prompt: Input prompt
            choices: List of valid choices
            default: Default choice
            
        Returns:
            Selected choice
        """
        while True:
            try:
                choice = input(prompt).strip()
                if not choice:
                    return default
                
                choice_num = int(choice)
                if choice_num in choices:
                    return choice_num
                else:
                    print(f"Please enter a number between {min(choices)} and {max(choices)}")
            except ValueError:
                print("Please enter a valid number.")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    cli = PipelineCLI()
    return cli.parse_args()


def create_cli() -> PipelineCLI:
    """
    Create CLI instance.
    
    Returns:
        CLI instance
    """
    return PipelineCLI() 