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
from percell.core.config import Config, ConfigError, create_default_config
from percell.core.logger import PipelineLogger
from percell.core.cli import parse_arguments, CLIError, show_header, create_cli
from percell.core.pipeline import Pipeline
from percell.infrastructure.dependencies.container import Container, AppConfig
from percell.application.use_cases.run_complete_workflow import RunCompleteWorkflow


def main():
    """Main entry point for the microscopy per cell analysis pipeline."""
    try:
        # Register all available stages
        from percell.modules.stage_registry import register_all_stages
        register_all_stages()
        
        # Load configuration
        from percell.core.paths import get_path_str, path_exists
        try:
            config_path = get_path_str("config_default")
            if path_exists("config_default"):
                config = Config(config_path)
            else:
                print(f"Configuration file not found: {config_path}")
                print("Creating default configuration...")
                config = create_default_config(config_path)
        except KeyError:
            # Fallback to relative path if path system fails
            config_path = "percell/config/config.json"
            print(f"Configuration file not found: {config_path}")
            print("Creating default configuration...")
            config = create_default_config(config_path)
        
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
                                              args.threshold_grouped_cells, args.measure_roi_area, args.analysis,
                                              args.cleanup, args.complete_workflow, getattr(args, 'advanced_workflow', False)]):
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
                
                # Create and run pipeline (legacy path)
                pipeline = Pipeline(config, logger, args)
                success = pipeline.run()

                # Additionally demonstrate ports/adapters flow on request
                if getattr(args, 'advanced_workflow', False):
                    container = Container(
                        AppConfig(
                            storage_base_path=None,
                            cellpose_path=None,
                            imagej_path=None,
                        )
                    )
                    use_case = RunCompleteWorkflow(container.workflow_orchestrator())
                    try:
                        _summary = use_case.execute(workflow_id="standard_analysis")
                        # Not printed to avoid cluttering legacy output
                    except Exception:
                        # Ignore demonstration failures for now
                        pass

                # Ports & Adapters DI demo: lightweight, non-invasive
                if getattr(args, 'ports_adapters_demo', False):
                    try:
                        from pathlib import Path
                        from percell.infrastructure.dependencies.container import Container as DIContainer, AppConfig as DIAppConfig
                        from percell.domain.entities.image import Image as DomainImage
                        from percell.domain.value_objects.file_path import FilePath as VOFilePath

                        imagej_path = config.get('imagej_path')
                        cellpose_py = config.get('directories.cellpose_path') or config.get('cellpose_path')
                        di = DIContainer(DIAppConfig(
                            storage_base_path=args.input,
                            cellpose_path=cellpose_py,
                            imagej_path=imagej_path,
                        ))
                        storage = di.storage_adapter
                        # find first tif
                        base = Path(args.input)
                        img_path = None
                        for ext in ('*.tif', '*.tiff'):
                            found = list(base.rglob(ext))
                            if found:
                                img_path = found[0]
                                break
                        if img_path is None:
                            print("[DI demo] No .tif images found in input")
                        else:
                            np_img = storage.read_image(VOFilePath(img_path))
                            demo_image = DomainImage(image_id=img_path.stem, data=np_img, file_path=img_path)
                            print(f"[DI demo] Image stats: {demo_image.get_statistics()}")
                            rois = di.cellpose_adapter.segment_cells(demo_image, {"model": "cyto"})
                            print(f"[DI demo] ROIs returned: {len(rois)}")
                            if rois:
                                roi = rois[0]
                                if roi.bounding_box is None and roi.coordinates:
                                    roi.calculate_bounding_box()
                                if roi.bounding_box is not None and not roi.coordinates:
                                    x, y, w, h = roi.bounding_box
                                    roi.coordinates = [
                                        (x, y), (x + max(0, w - 1), y),
                                        (x + max(0, w - 1), y + max(0, h - 1)), (x, y + max(0, h - 1))
                                    ]
                                try:
                                    ip = di.imagej_adapter
                                    stats = ip.measure_roi_intensity(demo_image, roi)
                                    print(f"[DI demo] ROI intensity stats: {stats}")
                                    thr = ip.threshold_image(demo_image, method="otsu")
                                    print(f"[DI demo] Thresholded image shape: {None if thr.data is None else thr.data.shape}")
                                except Exception as e:
                                    print(f"[DI demo] Extra metrics error: {e}")
                    except Exception as e:
                        print(f"[DI demo] Error: {e}")
                
                if success:
                    print("\n" + "="*80)
                    print("Pipeline completed successfully!")
                    print("="*80)
                    
                    # Automatically save the most recently used directories as defaults
                    try:
                        from percell.modules.directory_setup import save_recent_directories_automatically
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
                
                # Check if this was an interactive module
                interactive_modules = ['segmentation', 'threshold_grouped_cells']
                is_interactive = any(getattr(args, module, False) for module in interactive_modules)
                
                if is_interactive:
                    # For interactive modules, show completion message
                    print("\n" + "="*80)
                    print("Interactive module completed. Returning to main menu...")
                    print("="*80 + "\n")
                    
                    # Small delay to let user read the completion message
                    import time
                    time.sleep(1)
                else:
                    # For non-interactive modules, show completion message
                    print("\n" + "="*80)
                    print("Pipeline completed. Returning to main menu...")
                    print("="*80 + "\n")
                    
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