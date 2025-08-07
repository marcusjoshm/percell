#!/usr/bin/env python3
"""
Microscopy Single-Cell Analysis Pipeline - Main Entry Point

Streamlined main script using the refactored architecture.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.python.core.config import Config, ConfigError
from src.python.core.logger import PipelineLogger
from src.python.core.cli import parse_arguments, CLIError, show_header, create_cli
from src.python.core.pipeline import Pipeline
from src.python.core.config import create_default_config


def main():
    """Main entry point for the microscopy single-cell analysis pipeline."""
    try:
        # Register all available stages
        from src.python.modules.stage_registry import register_all_stages
        register_all_stages()
        
        # Load configuration
        config_path = "config/config.json"
        if not Path(config_path).exists():
            print(f"Configuration file not found: {config_path}")
            print("Creating default configuration...")
            config = create_default_config(config_path)
        else:
            config = Config(config_path)
        
        # Validate configuration (but don't exit on missing software paths)
        try:
            config.validate()
        except ConfigError as e:
            print(f"Configuration warning: {e}")
            print("Some features may not work without proper software paths.")
            print("You can set software paths in the configuration file.")
            print()
        
        while True:
            try:
                # Parse command line arguments each iteration
                cli = create_cli()
                args = cli.parser.parse_args()
                
                # Handle interactive mode or show menu if no processing options selected
                if args.interactive or not any([args.data_selection, args.segmentation, args.process_single_cell,
                                              args.threshold_grouped_cells, args.analysis, args.complete_workflow]):
                    args = cli.show_interactive_menu(args)
                    if args is None:  # User chose to exit
                        print("Goodbye!")
                        return 0
                
                # Now validate arguments after menu processing
                try:
                    cli._validate_args(args)
                except CLIError as e:
                    print(f"CLI Error: {e}")
                    print("Press Enter to return to main menu...")
                    try:
                        input()
                    except EOFError:
                        print("\nEOF detected. Exiting gracefully.")
                        return 1
                    continue  # Return to menu
                
                # Check if any stages are selected
                stages_selected = any([args.data_selection, args.segmentation, args.process_single_cell,
                                     args.threshold_grouped_cells, args.measure_roi_area, args.analysis, args.complete_workflow])
                
                if not stages_selected:
                    # No stages selected, just return to menu (e.g., after setting directories)
                    continue
                
                # Create logger
                log_level = "DEBUG" if args.verbose else "INFO"
                logger = PipelineLogger(args.output, log_level=log_level)
                
                # Create and run pipeline
                pipeline = Pipeline(config, logger, args)
                success = pipeline.run()
                
                if success:
                    print("\n" + "="*60)
                    print("Pipeline completed successfully!")
                    print("="*60)
                    
                    # Automatically save the most recently used directories as defaults
                    try:
                        from src.python.modules.directory_setup import save_recent_directories_automatically, load_config
                        config_path = "config/config.json"
                        config = load_config(config_path)
                        save_recent_directories_automatically(config, args.input, args.output, config_path)
                    except Exception as e:
                        print(f"Note: Could not save directory defaults: {e}")
                else:
                    print("\n" + "="*60)
                    print("Pipeline completed with errors. Check logs for details.")
                    print("="*60)
                
                # Check if this was an interactive module
                interactive_modules = ['segmentation', 'threshold_grouped_cells']
                is_interactive = any(getattr(args, module, False) for module in interactive_modules)
                
                if is_interactive:
                    # For interactive modules, show completion message
                    print("\n" + "="*60)
                    print("Interactive module completed. Returning to main menu...")
                    print("="*60 + "\n")
                    
                    # Small delay to let user read the completion message
                    import time
                    time.sleep(1)
                else:
                    # For non-interactive modules, show completion message
                    print("\n" + "="*60)
                    print("Pipeline completed. Returning to main menu...")
                    print("="*60 + "\n")
                    
                    # Small delay to let user read the output
                    import time
                    time.sleep(2)
                
            except KeyboardInterrupt:
                print("\nPipeline interrupted by user")
                return 1
            except Exception as e:
                print(f"Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                print("\nPress Enter to return to main menu...")
                try:
                    input()
                except EOFError:
                    print("\nEOF detected. Exiting gracefully.")
                    return 1
                continue  # Return to menu
            
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main()) 