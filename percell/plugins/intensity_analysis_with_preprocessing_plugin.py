"""
Enhanced Intensity Analysis Plugin with Automatic Preprocessing

This plugin integrates the 4-script preprocessing workflow into the intensity analysis:
1. Copies percell analysis outputs to BS directory structure
2. Runs ImageJ macros for P-body and stress granule processing
3. Copies ch0 files
4. Runs intensity analysis on the prepared data
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from percell.plugins.intensity_analysis_plugin import IntensityAnalysisBSPlugin, METADATA as BASE_METADATA
from percell.plugins.base import PluginMetadata
from percell.ports.driving.user_interface_port import UserInterfacePort
from percell.domain.services.bs_preprocessing_service import BSPreprocessingService
from percell.application.bs_workflow import BSWorkflow
from percell.domain.services.package_resource_service import PackageResourceService

# Enhanced plugin metadata
METADATA = PluginMetadata(
    name="intensity_analysis_bs_auto",
    version="2.0.0",
    description="Analyzes intensity with automatic preprocessing from percell outputs",
    author="PerCell Team",
    dependencies=BASE_METADATA.dependencies,
    requires_input_dir=True,
    requires_output_dir=False,
    requires_config=True,  # Needs ImageJ path
    category="analysis",
    menu_title="Intensity Analysis BS (Auto-Prep)",
    menu_description="Automatically preprocess percell outputs and run intensity analysis"
)


class IntensityAnalysisBSAutoPlugin(IntensityAnalysisBSPlugin):
    """Enhanced intensity analysis plugin with automatic preprocessing."""

    def __init__(self, metadata: Optional[PluginMetadata] = None):
        """Initialize plugin."""
        super().__init__(metadata or METADATA)
        self._preprocessing_service = BSPreprocessingService()

        # Initialize resource service with percell package root
        import percell
        from pathlib import Path
        package_root = Path(percell.__file__).parent
        self._resource_service = PackageResourceService(package_root=package_root)

    def execute(
        self,
        ui: UserInterfacePort,
        args: argparse.Namespace
    ) -> Optional[argparse.Namespace]:
        """Execute the full preprocessing and analysis workflow."""
        try:
            ui.info("🔬 Intensity Analysis with Automatic Preprocessing")
            ui.info("=" * 60)
            ui.info("This plugin will:")
            ui.info("  1. Copy percell analysis outputs to BS directory")
            ui.info("  2. Run ImageJ macros for P-body and SG processing")
            ui.info("  3. Copy ch0 intensity files")
            ui.info("  4. Run intensity analysis")
            ui.info("=" * 60)

            # Get percell analysis directory - prefer output over input
            # The output directory is where combined_masks/ and raw_data/ are created
            percell_dir = getattr(args, 'output', None) or getattr(args, 'input', None)

            if not percell_dir:
                ui.info("\n📁 Select percell analysis OUTPUT directory")
                ui.info("This is the directory where percell analysis was saved")
                ui.info("(It should contain combined_masks/ and raw_data/ subdirectories)")
                percell_dir = ui.prompt("Enter percell analysis output directory path: ").strip()

            percell_path = Path(percell_dir)
            if not percell_path.exists():
                ui.error(f"Error: Directory '{percell_dir}' does not exist")
                ui.prompt("Press Enter to continue...")
                return args

            # Validate percell directory structure
            if not (percell_path / "combined_masks").exists():
                ui.error(f"Error: {percell_path} does not contain combined_masks/ directory")
                ui.error("This should be the percell OUTPUT directory (where analysis results are saved)")
                ui.error("Not the INPUT directory (where raw images are located)")
                ui.prompt("Press Enter to continue...")
                return args

            if not (percell_path / "raw_data").exists():
                ui.error(f"Error: {percell_path} does not contain raw_data/ directory")
                ui.error("This should be the percell OUTPUT directory (where analysis results are saved)")
                ui.error("Not the INPUT directory (where raw images are located)")
                ui.prompt("Press Enter to continue...")
                return args

            # Get ImageJ adapter from container
            try:
                imagej_adapter = self.container.imagej
            except (RuntimeError, AttributeError) as e:
                ui.error("Error: ImageJ adapter not available")
                ui.error("Please ensure ImageJ is configured in your settings")
                ui.error(f"Details: {e}")
                ui.prompt("Press Enter to continue...")
                return args

            # Create BS workflow orchestrator
            workflow = BSWorkflow(
                self._preprocessing_service,
                imagej_adapter,
                self._resource_service
            )

            # Ask about condition mapping for ch0 files
            ui.info("\n⚙️  Ch0 File Configuration")
            ui.info("Default condition detection: '1Hr_NaAsO2' and 'Untreated'")
            use_default = ui.prompt("Use default condition mapping? (Y/n): ").strip().lower()

            condition_map = None
            if use_default not in ['', 'y', 'yes']:
                ui.info("Custom condition mapping not yet implemented")
                ui.info("Using default mapping")
                condition_map = {
                    "1Hr_NaAsO2": "1Hr_NaAsO2",
                    "Untreated": "Untreated"
                }
            else:
                condition_map = {
                    "1Hr_NaAsO2": "1Hr_NaAsO2",
                    "Untreated": "Untreated"
                }

            # Ask about output directory
            default_output = percell_path.parent / f"{percell_path.name}_BS"
            ui.info(f"\n📂 Output directory: {default_output}")
            use_default_out = ui.prompt("Use this output directory? (Y/n): ").strip().lower()

            output_dir = None
            if use_default_out not in ['', 'y', 'yes']:
                output_path = ui.prompt("Enter custom output directory path: ").strip()
                output_dir = Path(output_path)

            # Run preprocessing workflow
            ui.info("\n🔄 Starting preprocessing workflow...")
            try:
                bs_dir = workflow.run_full_preprocessing(
                    percell_path,
                    output_dir=output_dir,
                    condition_map=condition_map
                )
                ui.info(f"✅ Preprocessing complete! Output: {bs_dir}")
            except Exception as e:
                ui.error(f"❌ Preprocessing failed: {e}")
                import traceback
                ui.error(traceback.format_exc())
                ui.prompt("Press Enter to continue...")
                return args

            # Now run intensity analysis on the processed directory
            ui.info("\n🔬 Running intensity analysis on processed data...")
            ui.info("=" * 60)

            # Create new args with the processed directory
            analysis_args = argparse.Namespace()
            analysis_args.input = str(bs_dir / "Processed")

            # Run the parent class's execute method for intensity analysis
            result = super().execute(ui, analysis_args)

            ui.info("\n✅ Complete workflow finished successfully!")
            ui.prompt("Press Enter to return to main menu...")

            return args

        except Exception as e:
            ui.error(f"Error executing plugin: {e}")
            import traceback
            ui.error(traceback.format_exc())
            ui.prompt("Press Enter to continue...")
            return args
