#!/usr/bin/env python3
"""
Microscopy Per Cell Analysis Pipeline - Main Entry Point

Streamlined main script using the refactored architecture.
"""

import sys
import os
import argparse
from pathlib import Path

# Import from the package (no sys.path manipulation needed!)
from percell.domain.services.configuration_service import (
    ConfigurationService,
    create_configuration_service
)
from percell.domain.exceptions import ConfigurationError
from percell.application.logger_api import PipelineLogger
from percell.application.pipeline_api import Pipeline
from percell.main.bootstrap import bootstrap
from percell.adapters.cli_user_interface_adapter import CLIUserInterfaceAdapter
from percell.application.cli_services import show_menu, validate_args
from percell.application.cli_parser import build_parser


def _populate_default_config(config: ConfigurationService) -> None:
    """Populate configuration with default values if empty."""
    defaults = {
        "imagej_path": "",
        "cellpose_path": "",
        "python_path": sys.executable,
        "fiji_path": "",
        "analysis.default_bins": 5,
        "analysis.segmentation_model": "cyto",
        "analysis.cell_diameter": 100,
        "analysis.niter_dynamics": 250,
        "analysis.flow_threshold": 0.4,
        "analysis.cellprob_threshold": 0,
        "output.create_subdirectories": True,
        "output.save_intermediate": True,
        "output.compression": "lzw",
        "output.overwrite": False,
        "directories.input": "",
        "directories.output": "",
        "data_selection.selected_datatype": None,
        "data_selection.selected_conditions": [],
        "data_selection.selected_timepoints": [],
        "data_selection.selected_regions": [],
        "data_selection.segmentation_channel": None,
        "data_selection.analysis_channels": [],
    }

    for key, value in defaults.items():
        if not config.has(key):
            config.set(key, value)

    # Initialize nested structures that might not exist
    if not config.has("directories.recent_inputs"):
        config.set("directories.recent_inputs", [])
    if not config.has("directories.recent_outputs"):
        config.set("directories.recent_outputs", [])
    if not config.has("data_selection.experiment_metadata"):
        config.set("data_selection.experiment_metadata", {
            "conditions": [],
            "regions": [],
            "timepoints": [],
            "channels": [],
            "region_to_channels": {},
            "datatype_inferred": None,
            "directory_timepoints": [],
        })

    config.save()


def main():
    """Main entry point for the microscopy per cell analysis pipeline."""
    try:
        # Register all available stages
        from percell.application.stage_registry import register_all_stages
        register_all_stages()
        
        # Load configuration
        from percell.application.paths_api import get_path_str, path_exists
        try:
            config_path = get_path_str("config_default")
        except KeyError:
            # Fallback to relative path if path system fails
            config_path = "percell/config/config.json"

        # Create/load configuration using new service
        config = create_configuration_service(config_path, create_if_missing=True)

        # Populate with defaults if new/empty
        if not config.has("python_path"):
            print(f"Configuration file not found or empty: {config_path}")
            print("Creating default configuration...")
            _populate_default_config(config)

        # Initialize DI container (adapters/services)
        try:
            container = bootstrap(config_path)
        except Exception as e:
            print(f"Warning: Failed to initialize DI container: {e}")
            container = None

        # Validate configuration (but don't exit on missing software paths)
        required_keys = ["python_path"]
        missing = [k for k in required_keys if not config.has(k)]
        if missing:
            print(f"Configuration warning: Missing required keys: {missing}")
            print("Some features may not work without proper software paths.")
            print("You can set software paths in the configuration file.")
            print()
        
        # Parse command line arguments once
        parser = build_parser()
        args = parser.parse_args()

        while True:
            try:
                # Initialize UI adapter
                ui = CLIUserInterfaceAdapter()
                # Show menu if needed
                args = show_menu(ui, args)
                if args is None:
                    return 0
                
                # If still no stages selected and not interactive, continue loop
                if not any([
                    args.data_selection, args.segmentation, args.process_single_cell,
                    args.threshold_grouped_cells, args.measure_roi_area, args.analysis,
                    args.cleanup, args.complete_workflow, getattr(args, 'advanced_workflow', False)
                ]):
                    continue
                
                # Now validate arguments after menu processing
                try:
                    validate_args(args, ui)
                except Exception as e:
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
                                     args.threshold_grouped_cells, args.measure_roi_area, args.analysis,
                                     args.cleanup, args.complete_workflow, getattr(args, 'advanced_workflow', False)])
                
                if not stages_selected:
                    # No stages selected, just return to menu (e.g., after setting directories)
                    continue
                
                # Ensure output directory is set
                if not args.output:
                    print("Error: Output directory is required for pipeline execution.")
                    print("Please set the output directory using --output or through the interactive menu.")
                    continue
                
                # Create logger
                log_level = "DEBUG" if args.verbose else "INFO"
                logger = PipelineLogger(args.output, log_level=log_level)
                
                # Create and run pipeline
                ports = {}
                if container is not None:
                    try:
                        ports = {
                            "imagej": getattr(container, "imagej", None),
                            "fs": getattr(container, "fs", None),
                            "imgproc": getattr(container, "imgproc", None),
                            "cellpose": getattr(container, "cellpose", None),
                        }
                    except Exception:
                        ports = {}
                pipeline = Pipeline(config, logger, args, ports=ports)
                success = pipeline.run()
                
                if success:
                    print("\n" + "="*80)
                    print("Pipeline completed successfully!")
                    print("="*80)
                    
                    # Automatically save the most recently used directories as defaults
                    try:
                        from percell.application.directory_setup import save_recent_directories_automatically
                        # Reload the config to get the latest data
                        config.load()
                        # Convert config to dict for the directory setup functions
                        config_dict = config.to_dict()
                        save_recent_directories_automatically(config_dict, args.input, args.output, config_path)
                        # Reload the updated config
                        config.load()
                    except Exception as e:
                        print(f"Note: Could not save directory defaults: {e}")
                else:
                    print("\n" + "="*80)
                    print("Pipeline completed with errors. Check logs for details.")
                    print("="*80)
                
                # Check if this was an interactive stage
                interactive_stages = ['segmentation', 'threshold_grouped_cells']
                is_interactive = any(getattr(args, stage, False) for stage in interactive_stages)
                
                if is_interactive:
                    # For interactive stages, show completion message
                    print("\n" + "="*80)
                    print("Interactive stage completed. Returning to main menu...")
                    print("="*80 + "\n")
                    
                    # Small delay to let user read the completion message
                    import time
                    time.sleep(1)
                else:
                    # For non-interactive stages, show completion message
                    print("\n" + "="*80)
                    if getattr(args, 'return_to_config', False):
                        print("Process completed. Returning to menu...")
                    else:
                        print("Pipeline completed. Returning to main menu...")
                    print("="*80 + "\n")

                    # Small delay to let user read the output
                    import time
                    time.sleep(2)

                # Reset workflow flags for next menu interaction
                args.data_selection = False
                args.segmentation = False
                args.process_single_cell = False
                args.threshold_grouped_cells = False
                args.measure_roi_area = False
                args.analysis = False
                args.cleanup = False
                args.complete_workflow = False
                if hasattr(args, 'advanced_workflow'):
                    delattr(args, 'advanced_workflow')

                # Check if we should return to configuration menu
                if getattr(args, 'return_to_config', False):
                    # Clear the flags and show configuration menu
                    delattr(args, 'return_to_config')
                    args.data_selection = False
                    args = show_menu(ui, args)
                    if args is None:
                        return 0
                    continue

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