from __future__ import annotations

"""CLI application layer. Implements PipelineCLI and argument parsing.

Moved from percell.core.cli to decouple CLI from core orchestration.
"""

import argparse
from typing import Optional


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
    return f"{Colors.bold}{color}{text}{Colors.reset}"


def show_header() -> None:
    header = [
        "         ███████╗ ████████╗███████╗ ███████╗████████╗██╗      ██╗               ",
        "         ██╔═══██╗██╔═════╝██╔═══██╗██╔════╝██╔═════╝██║      ██║               ",
        "         ███████╔╝███████╗ ███████╔╝██║     ███████╗ ██║      ██║               ",
        "         ██╔════╝ ██╔════╝ ██╔═══██╗██║     ██╔════╝ ██║      ██║               ",
        "         ██║      ████████╗██║   ██║███████╗████████╗████████╗████████╗         ",
        "         ╚═╝      ╚═══════╝╚═╝   ╚═╝╚══════╝╚═══════╝╚═══════╝╚═══════╝         ",
    ]

    print('')
    for i, line in enumerate(header):
        if i < 0 or i > 20:
            print(line)
        else:
            colored_line = ""
            for j, char in enumerate(line):
                if 1 <= j <= 35:
                    colored_line += colorize(char, Colors.green)
                elif 36 <= j <= 80:
                    colored_line += colorize(char, Colors.magenta)
                else:
                    colored_line += char
            print(colored_line)


class CLIError(Exception):
    pass


class PipelineCLI:
    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
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

        # Input/Output
        parser.add_argument('--input', '-i', type=str, help='Input directory containing microscopy data')
        parser.add_argument('--output', '-o', type=str, help='Output directory for results')
        parser.add_argument('--config', type=str, help='Path to configuration file (default: uses package config)')

        # Processing options
        parser.add_argument('--data-selection', action='store_true', help='Run data selection')
        parser.add_argument('--segmentation', action='store_true', help='Run single-cell segmentation')
        parser.add_argument('--process-single-cell', action='store_true', help='Run single-cell data processing')
        parser.add_argument('--threshold-grouped-cells', action='store_true', help='Run threshold grouped cells')
        parser.add_argument('--measure-roi-area', action='store_true', help='Run ROI area measurement')
        parser.add_argument('--analysis', action='store_true', help='Run analysis')
        parser.add_argument('--cleanup', action='store_true', help='Clean up directories')
        parser.add_argument('--complete-workflow', action='store_true', help='Run complete workflow')
        parser.add_argument('--advanced-workflow', action='store_true', help='Run advanced workflow builder')

        # Data selection args
        parser.add_argument('--datatype', choices=['single_timepoint', 'multi_timepoint'], help='Data type to analyze')
        parser.add_argument('--conditions', nargs='+', help='Specific conditions to analyze')
        parser.add_argument('--timepoints', nargs='+', help='Specific timepoints to analyze')
        parser.add_argument('--regions', nargs='+', help='Specific regions to analyze')
        parser.add_argument('--segmentation-channel', help='Channel to use for segmentation')
        parser.add_argument('--analysis-channels', nargs='+', help='Channels to analyze')
        parser.add_argument('--bins', type=int, default=5, help='Bins for grouping')

        # Control
        parser.add_argument('--skip-steps', nargs='+', help='Steps to skip in the workflow')
        parser.add_argument('--start-from', help='Step to start the workflow from')
        parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
        parser.add_argument('--interactive', '-I', action='store_true', help='Run in interactive mode')

        return parser

    def parse_args(self, args: Optional[list] = None) -> argparse.Namespace:
        parsed_args = self.parser.parse_args(args)
        self._validate_args(parsed_args)
        return parsed_args

    def _validate_args(self, args: argparse.Namespace) -> None:
        # Load config defaults
        try:
            from percell.modules.directory_setup import load_config
            from percell.infrastructure.filesystem.paths import get_path

            if args.config:
                config_path = args.config
            else:
                try:
                    config_path = str(get_path('config_default'))
                except Exception:
                    config_path = 'percell/config/config.json'

            config = load_config(config_path)
            default_input = config.get('directories', {}).get('input', '')
            default_output = config.get('directories', {}).get('output', '')
        except Exception:
            default_input = ''
            default_output = ''

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

    def show_interactive_menu(self, args: argparse.Namespace) -> Optional[argparse.Namespace]:
        stage_flags = [
            args.data_selection, args.segmentation, args.process_single_cell,
            args.threshold_grouped_cells, args.measure_roi_area, args.analysis, args.cleanup,
            args.complete_workflow, args.advanced_workflow,
        ]
        if any(stage_flags):
            return args

        show_header()
        print("")
        print(colorize("  🔬 Welcome single-cell microscopy analysis user! 🔬", Colors.bold))
        print("")
        print(colorize("MENU:", Colors.bold))
        print(colorize("1. Set Input/Output Directories", Colors.yellow))
        print(colorize("2. Run Complete Workflow", Colors.magenta))
        print(colorize("3. Data Selection (conditions, regions, timepoints, channels)", Colors.reset))
        print(colorize("4. Single-cell Segmentation (Cellpose)", Colors.green))
        print(colorize("5. Process Single-cell Data (tracking, resizing, extraction, grouping)", Colors.green))
        print(colorize("6. Threshold Grouped Cells (interactive ImageJ thresholding)", Colors.green))
        print(colorize("7. Measure Cell Area (measure areas from single-cell ROIs)", Colors.green))
        print(colorize("8. Analysis (combine masks, create cell masks, export results)", Colors.green))
        print(colorize("9. Cleanup (empty cells and masks directories, preserves grouped/combined data)", Colors.reset))
        print(colorize("10. Advanced Workflow Builder (custom sequence of steps)", Colors.magenta))
        print(colorize("11. Exit", Colors.red))
        print("")

        try:
            choice = input("Select an option (1-11): ").strip().lower()
        except EOFError:
            print("\nEOF detected. Exiting gracefully.")
            return None

        if choice == "1":
            try:
                from percell.modules.set_directories import set_default_directories
                from percell.modules.directory_setup import load_config
                from percell.infrastructure.filesystem.paths import get_path
                config_path = args.config or str(get_path('config_default'))
                config = load_config(config_path)
                input_path, output_path = set_default_directories(config, config_path)
                args.input = input_path
                args.output = output_path
                print(f"\n✅ Directories set successfully!")
                print(f"  Input: {input_path}")
                print(f"  Output: {output_path}")
                print(f"  Note: Directory structure will be created when running workflow modules")
            except Exception:
                if not args.input:
                    args.input = self._get_directory_input("Enter input directory path: ")
                if not args.output:
                    args.output = self._get_directory_input("Enter output directory path: ")
        elif choice == "2":
            print("\n" + "="*80)
            print("Running Complete Workflow")
            print("This will execute all steps in sequence:")
            print("1. Data Selection (Option 3)")
            print("2. Single-cell Segmentation (Option 4)")
            print("3. Process Single-cell Data (Option 5)")
            print("4. Threshold Grouped Cells (Option 6)")
            print("5. Measure ROI Areas (Option 7)")
            print("6. Analysis (Option 8)")
            print("7. Cleanup (Option 9) - Optional")
            print("="*80 + "\n")
            args.data_selection = True
            args.segmentation = True
            args.process_single_cell = True
            args.threshold_grouped_cells = True
            args.measure_roi_area = True
            args.analysis = True
            args.complete_workflow = True
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
        elif choice == "9":
            args.cleanup = True
        elif choice == "10":
            args.advanced_workflow = True
        elif choice in {"11", "q", "quit"}:
            print("Exiting.")
            return None
        else:
            print("Invalid choice. Please enter a number between 1-11 or 'q' to quit.")
            return args

        return args

    def _get_directory_input(self, prompt: str) -> str:
        while True:
            try:
                directory = input(prompt).strip()
                if directory:
                    return directory
                print("Please enter a valid directory path.")
            except EOFError:
                print("\nEOF detected. Exiting gracefully.")
                raise


def parse_arguments() -> argparse.Namespace:
    cli = PipelineCLI()
    return cli.parse_args()


def create_cli() -> PipelineCLI:
    return PipelineCLI()


__all__ = [
    "PipelineCLI",
    "CLIError",
    "show_header",
    "create_cli",
    "parse_arguments",
]

