"""
Intensity Analysis with Background Subtraction Plugin for PerCell

Analyzes intensity measurements in ROIs using per-ROI local background subtraction.
Converts the standalone analyze_intensity_with_bs.py script into a PerCell plugin.
"""

from __future__ import annotations

import argparse
import csv
import zipfile
from pathlib import Path
from typing import Optional, Dict, List

import numpy as np
# Lazy imports for optional dependencies
# These will be imported when needed in methods

from percell.plugins.base import PerCellPlugin, PluginMetadata
from percell.ports.driving.user_interface_port import UserInterfacePort


# Base metadata for inheritance (not registered as standalone plugin)
# This class is only used as a base for IntensityAnalysisBSAutoPlugin
BASE_METADATA = PluginMetadata(
    name="intensity_analysis_bs",
    version="1.0.0",
    description="Analyzes intensity measurements in ROIs using per-ROI local background subtraction",
    author="PerCell Team",
    dependencies=["numpy", "scipy", "matplotlib", "roifile", "pillow", "tifffile", "scikit-image"],
    requires_input_dir=True,
    requires_output_dir=False,  # Uses input directory for output
    requires_config=False,
    category="analysis",
    menu_title="Intensity Analysis with Background Subtraction",
    menu_description="Analyze ROI intensities with local background subtraction using Gaussian peak detection"
)


class IntensityAnalysisBSPlugin(PerCellPlugin):
    """Intensity analysis plugin with background subtraction.

    This is a base class for other plugins and should not be registered directly.
    """

    # Marker to prevent plugin registry from auto-discovering this base class
    _INTERNAL_BASE_CLASS = True

    def __init__(self, metadata: Optional[PluginMetadata] = None):
        """Initialize plugin."""
        super().__init__(metadata or BASE_METADATA)

    def _is_dot_file(self, path: Path) -> bool:
        """Check if a file or directory is a dot file (hidden file starting with .)."""
        return path.name.startswith('.')
    
    def execute(
        self,
        ui: UserInterfacePort,
        args: argparse.Namespace
    ) -> Optional[argparse.Namespace]:
        """Execute the intensity analysis workflow."""
        try:
            ui.info("🔬 Intensity Analysis with Background Subtraction")
            ui.info("=" * 60)
            
            # Get base directory from args or prompt
            base_dir = getattr(args, 'input', None)
            if not base_dir:
                base_dir = ui.prompt("Enter base directory containing microscopy data: ").strip()
            
            base_path = Path(base_dir)
            if not base_path.exists():
                ui.error(f"Error: Base directory '{base_dir}' does not exist")
                ui.prompt("Press Enter to continue...")
                return args

            # Find all subdirectories, excluding dot files/directories
            subdirs = [d for d in base_path.iterdir()
                       if d.is_dir() and not self._is_dot_file(d)]
            
            if len(subdirs) == 0:
                ui.error(f"Error: No subdirectories found in '{base_dir}'")
                ui.prompt("Press Enter to continue...")
                return args
            
            ui.info(f"Found {len(subdirs)} subdirectories to analyze")
            
            # Get analysis configurations and prompt for parameters
            analysis_configs = self._get_analysis_configurations()
            analysis_configs = self._prompt_for_config_parameters(ui, analysis_configs)
            
            # Process each subdirectory
            for data_dir in subdirs:
                dataset_name = data_dir.name
                method = "gaussian_peaks"  # Default method
                
                ui.info("=" * 60)
                ui.info(f"Analyzing {dataset_name} Dataset")
                ui.info("=" * 60)
                
                # Get all available files in the directory, excluding dot files
                tif_files = [f for f in data_dir.glob("*.tif")
                            if not self._is_dot_file(f)]
                zip_files = [f for f in data_dir.glob("*.zip")
                            if not self._is_dot_file(f)]
                
                # Process each analysis configuration
                for config in analysis_configs:
                    ui.info(f"\n--- Processing {config['name']} analysis ---")
                    ui.info(f"  ROI enlargement: {config['enlarge_rois']} pixels")
                    ui.info(f"  Maximum background constraint: {config['max_background']}")
                    
                    # Find matching files for this configuration
                    intensity_file = self._find_file_matching_keywords(
                        tif_files, config['intensity_keywords']
                    )
                    mask_file = self._find_file_matching_keywords(
                        zip_files, config['mask_keywords'],
                        exclude_keywords=config.get('mask_exclude_keywords')
                    )
                    dilated_file = self._find_file_matching_keywords(
                        zip_files, config['dilated_keywords']
                    )
                    
                    # Check if all required files were found
                    if intensity_file is None:
                        ui.info(f"  ⚠️  Skipping {config['name']}: No intensity file found matching {config['intensity_keywords']}")
                        continue
                    
                    if mask_file is None:
                        ui.info(f"  ⚠️  Skipping {config['name']}: No mask file found matching {config['mask_keywords']}")
                        continue
                    
                    if dilated_file is None:
                        ui.info(f"  ⚠️  Skipping {config['name']}: No dilated mask file found matching {config['dilated_keywords']}")
                        continue
                    
                    # Verify that mask and dilated files are different
                    if mask_file == dilated_file:
                        ui.info(f"  ⚠️  Skipping {config['name']}: Mask and dilated mask files are the same")
                        continue
                    
                    ui.info(f"  Intensity image: {intensity_file.name}")
                    ui.info(f"  Mask ROIs: {mask_file.name}")
                    ui.info(f"  Dilated mask ROIs: {dilated_file.name}")
                    
                    # Load intensity image
                    intensity_image = self._load_image(str(intensity_file))
                    image_shape = intensity_image.shape
                    
                    # Load ROI files
                    mask_rois = self._load_imagej_rois(str(mask_file))
                    dilated_rois = self._load_imagej_rois(str(dilated_file))
                    
                    # Optionally further enlarge the dilated ROIs
                    if config['enlarge_rois'] > 0:
                        background_rois = self._enlarge_rois_with_imagej(
                            dilated_rois, pixels=config['enlarge_rois']
                        )
                    else:
                        background_rois = dilated_rois
                    
                    # Analyze intensity using ROIs
                    results = self._analyze_roi_intensity_from_rois(
                        mask_rois, background_rois, intensity_image,
                        image_shape, method=method,
                        max_background=config['max_background']
                    )
                    
                    # Print summary
                    ui.info("\n  Summary Statistics (Intensity measurements):")
                    backgrounds = [r['background'] for r in results['rois']]
                    bg_subtracted = [r['mean_bg_subtracted'] for r in results['rois']]
                    if len(backgrounds) > 0:
                        ui.info(f"    Mean background: {np.mean(backgrounds):.2f}")
                        ui.info(f"    Median background: {np.median(backgrounds):.2f}")
                        ui.info(f"    ROIs with positive signal (>0): {np.sum(np.array(bg_subtracted) > 0)}/{len(bg_subtracted)}")
                    
                    # Create output filename
                    output_name = f"{dataset_name}_{config['output_name']}"
                    
                    # Save results
                    self._save_summary_statistics(results, data_dir, output_name, ui)
                    self._visualize_roi_histograms(results, data_dir, output_name, ui)
                
                ui.info("")
            
            ui.info("✅ Intensity analysis completed successfully!")
            ui.prompt("Press Enter to return to main menu...")
            
            return args
            
        except Exception as e:
            ui.error(f"Error executing plugin: {e}")
            import traceback
            ui.error(traceback.format_exc())
            ui.prompt("Press Enter to continue...")
            return args
    
    # Helper methods from original script (adapted for plugin)
    
    def _load_image(self, filepath: str) -> np.ndarray:
        """Load an image file and convert to numpy array."""
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("Pillow package is required. Install with: pip install pillow")
        
        img = Image.open(filepath)
        return np.array(img)
    
    def _load_imagej_rois(self, roi_zip_path: str) -> List[Dict]:
        """Load ROIs from ImageJ ROI zip file."""
        try:
            from roifile import ImagejRoi
        except ImportError:
            raise ImportError("roifile package is required. Install with: pip install roifile")
        
        rois = []
        with zipfile.ZipFile(roi_zip_path, 'r') as zf:
            for name in sorted(zf.namelist()):
                with zf.open(name) as roi_file:
                    roi_bytes = roi_file.read()
                    roi = ImagejRoi.frombytes(roi_bytes)
                    rois.append({
                        'name': name,
                        'roi': roi,
                        'coordinates': roi.coordinates(),
                        'bytes': roi_bytes
                    })
        return rois
    
    def _enlarge_rois_with_imagej(self, rois: List[Dict], pixels: int) -> List[Dict]:
        """Enlarge ROIs using binary dilation."""
        try:
            from scipy import ndimage
            from skimage.measure import find_contours
        except ImportError:
            raise ImportError("scipy and scikit-image packages are required")
        
        max_x = max_y = 0
        for roi_dict in rois:
            coords = roi_dict['coordinates']
            if len(coords) > 0:
                max_x = max(max_x, int(np.max(coords[:, 0])))
                max_y = max(max_y, int(np.max(coords[:, 1])))
        
        image_shape = (max_y + 100, max_x + 100)
        enlarged_rois = []
        
        for roi_dict in rois:
            mask = self._roi_to_mask(roi_dict['coordinates'], image_shape)
            from scipy import ndimage
            structure = ndimage.generate_binary_structure(2, 1)
            
            if pixels > 0:
                enlarged_mask = ndimage.binary_dilation(
                    mask, structure=structure, iterations=pixels
                ).astype(np.uint8)
            elif pixels < 0:
                enlarged_mask = ndimage.binary_erosion(
                    mask, structure=structure, iterations=abs(pixels)
                ).astype(np.uint8)
            else:
                enlarged_mask = mask
            
            contours = find_contours(enlarged_mask, 0.5)
            if len(contours) > 0:
                largest_contour = max(contours, key=len)
                new_coords = np.column_stack((largest_contour[:, 1], largest_contour[:, 0]))
            else:
                new_coords = roi_dict['coordinates']
            
            enlarged_rois.append({
                'name': roi_dict['name'],
                'roi': roi_dict['roi'],
                'coordinates': new_coords,
                'bytes': roi_dict.get('bytes', b'')
            })
        
        return enlarged_rois
    
    def _roi_to_mask(self, roi_coords: np.ndarray, image_shape: tuple) -> np.ndarray:
        """Convert ROI coordinates to a binary mask."""
        try:
            from skimage.draw import polygon
        except ImportError:
            raise ImportError("scikit-image package is required. Install with: pip install scikit-image")
        
        mask = np.zeros(image_shape, dtype=np.uint8)
        if len(roi_coords) > 0:
            rr, cc = polygon(roi_coords[:, 1], roi_coords[:, 0], image_shape)
            mask[rr, cc] = 1
        return mask
    
    def _find_gaussian_peaks(self, data: np.ndarray, n_bins: int = 50, max_background: Optional[float] = None) -> Optional[Dict]:
        """Find Gaussian peaks in a histogram of the data."""
        try:
            from scipy.ndimage import gaussian_filter1d
            from scipy.signal import find_peaks
        except ImportError:
            raise ImportError("scipy package is required. Install with: pip install scipy")
        
        if len(data) == 0:
            return None
        
        data_max = float(np.max(data))
        hist, bin_edges = np.histogram(data, bins=n_bins, range=(0, data_max))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        hist_smooth = gaussian_filter1d(hist.astype(float), sigma=2)
        
        min_prominence = np.max(hist_smooth) * 0.15
        peaks, properties = find_peaks(hist_smooth, prominence=min_prominence)
        
        if len(peaks) == 0:
            peak_idx = np.argmax(hist_smooth)
            background_value = bin_centers[peak_idx]
            return {
                'n_peaks': 1,
                'peaks': [background_value],
                'hist': hist,
                'bin_centers': bin_centers,
                'hist_smooth': hist_smooth,
                'background_value': background_value
            }
        
        peak_positions = bin_centers[peaks]
        peak_prominences = properties['prominences']
        
        if max_background is not None:
            peaks_below_threshold = peak_positions < max_background
            if np.any(peaks_below_threshold):
                prominences_below = peak_prominences[peaks_below_threshold]
                positions_below = peak_positions[peaks_below_threshold]
                most_prominent_idx = np.argmax(prominences_below)
                background_value = positions_below[most_prominent_idx]
            else:
                bins_below_threshold = bin_centers < max_background
                if np.any(bins_below_threshold):
                    hist_below = hist[bins_below_threshold]
                    bin_centers_below = bin_centers[bins_below_threshold]
                    max_count_idx = np.argmax(hist_below)
                    background_value = bin_centers_below[max_count_idx]
                else:
                    sorted_by_position = np.argsort(peak_positions)
                    background_value = peak_positions[sorted_by_position[0]]
        else:
            sorted_by_position = np.argsort(peak_positions)
            background_value = peak_positions[sorted_by_position[0]]
        
        peak_prominences = properties['prominences']
        sorted_indices = np.argsort(peak_prominences)[::-1]
        peaks_sorted_by_prominence = peaks[sorted_indices]
        peak_positions_for_report = bin_centers[peaks_sorted_by_prominence]
        
        return {
            'n_peaks': len(peaks),
            'peaks': peak_positions_for_report[:2] if len(peaks) >= 2 else peak_positions_for_report,
            'hist': hist,
            'bin_centers': bin_centers,
            'hist_smooth': hist_smooth,
            'peak_indices': peaks_sorted_by_prominence[:2] if len(peaks) >= 2 else peaks_sorted_by_prominence,
            'background_value': background_value
        }
    
    def _analyze_roi_intensity_from_rois(
        self,
        mask_rois: List[Dict],
        perimeter_rois: List[Dict],
        intensity_image: np.ndarray,
        image_shape: tuple,
        method: str = 'gaussian_peaks',
        max_background: Optional[float] = None
    ) -> Dict:
        """Analyze intensity measurements for each ROI using local background subtraction."""
        n_rois = len(mask_rois)
        
        results = []
        
        for i in range(n_rois):
            roi_mask = self._roi_to_mask(mask_rois[i]['coordinates'], image_shape)
            background_mask = self._roi_to_mask(perimeter_rois[i]['coordinates'], image_shape)
            
            roi_intensities = intensity_image[roi_mask > 0]
            background_intensities = intensity_image[background_mask > 0]
            
            if len(roi_intensities) == 0 or len(background_intensities) == 0:
                continue
            
            if method == 'minimum':
                background = np.min(background_intensities)
                peak_info = None
            elif method == 'gaussian_peaks':
                peak_info = self._find_gaussian_peaks(background_intensities, max_background=max_background)
                background = peak_info['background_value'] if peak_info else np.mean(background_intensities)
            else:
                raise ValueError(f"Unknown method: {method}")

            bg_subtracted = roi_intensities - background
            
            roi_result = {
                'roi_id': i + 1,
                'roi_name': mask_rois[i]['name'],
                'n_pixels': len(roi_intensities),
                'n_background_pixels': len(background_intensities),
                'mean_raw': np.mean(roi_intensities),
                'median_raw': np.median(roi_intensities),
                'background': background,
                'mean_bg_subtracted': np.mean(bg_subtracted),
                'median_bg_subtracted': np.median(bg_subtracted),
                'background_mean': np.mean(background_intensities),
                'background_std': np.std(background_intensities),
                'peak_info': peak_info,
            }
            
            results.append(roi_result)
        
        return {
            'rois': results,
            'n_rois': n_rois,
            'method': method
        }
    
    def _visualize_roi_histograms(
        self,
        analysis_results: Dict,
        data_dir: Path,
        dataset_name: str,
        ui: UserInterfacePort,
        max_plots: int = 9
    ) -> None:
        """Create histogram visualizations for ROIs."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            ui.warning("matplotlib not available, skipping visualization")
            return
        
        rois = analysis_results['rois']
        n_to_plot = min(max_plots, len(rois))
        
        if n_to_plot == 0:
            return
        
        n_cols = 3
        n_rows = (n_to_plot + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        
        for idx in range(n_to_plot):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col]
            
            roi = rois[idx]
            peak_info = roi['peak_info']
            
            if peak_info is None:
                ax.text(0.5, 0.5, f"ROI {roi['roi_id']}\nNo data", ha='center', va='center')
                ax.axis('off')
                continue
            
            ax.bar(peak_info['bin_centers'], peak_info['hist'],
                   width=np.diff(peak_info['bin_centers'])[0] * 0.8, alpha=0.6, label='Histogram')
            
            if 'hist_smooth' in peak_info:
                ax.plot(peak_info['bin_centers'], peak_info['hist_smooth'],
                       'r-', linewidth=2, label='Smoothed')
            
            if len(peak_info['peaks']) > 0:
                for peak_val in peak_info['peaks']:
                    ax.axvline(peak_val, color='green', linestyle='--', linewidth=2)
            
            ax.axvline(peak_info['background_value'], color='blue',
                      linestyle='-', linewidth=2, label=f"BG={peak_info['background_value']:.1f}")
            
            ax.set_title(f"ROI {roi['roi_id']}\n{peak_info['n_peaks']} peak(s), {roi['n_background_pixels']} px")
            ax.set_xlabel('Intensity')
            ax.set_ylabel('Count')
            ax.legend(fontsize=8)
        
        for idx in range(n_to_plot, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            axes[row, col].axis('off')
        
        plt.tight_layout()
        output_path = data_dir / f"{dataset_name}_background_histograms.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        ui.info(f"  ✅ Saved: {output_path.name}")
    
    def _save_summary_statistics(
        self,
        analysis_results: Dict,
        data_dir: Path,
        dataset_name: str,
        ui: UserInterfacePort
    ) -> None:
        """Save summary statistics to a CSV file."""
        rois = analysis_results['rois']
        output_path = data_dir / f"{dataset_name}_intensity_analysis.csv"
        
        with open(output_path, 'w', newline='') as f:
            if len(rois) == 0:
                return
            
            fieldnames = [k for k in rois[0].keys() if 'peak_info' not in k]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for roi in rois:
                row = {}
                for k, v in roi.items():
                    if 'peak_info' not in k:
                        if isinstance(v, (int, float, np.integer, np.floating)) and v < 0:
                            row[k] = ''
                        else:
                            row[k] = v
                writer.writerow(row)
        
        ui.info(f"  ✅ Saved: {output_path.name}")
    
    def _find_file_matching_keywords(
        self,
        files: List[Path],
        keywords: List[str],
        exclude_keywords: Optional[List[str]] = None
    ) -> Optional[Path]:
        """Find a file that contains all specified keywords."""
        keywords_lower = [k.lower() for k in keywords]
        exclude_lower = [k.lower() for k in exclude_keywords] if exclude_keywords else []
        
        for f in files:
            filename_lower = f.name.lower()
            if all(kw in filename_lower for kw in keywords_lower):
                if any(kw in filename_lower for kw in exclude_lower):
                    continue
                return f
        return None
    
    def _get_analysis_configurations(self) -> List[Dict]:
        """Define analysis configurations."""
        return [
            {
                'name': 'PB_Cap',
                'intensity_keywords': ['Cap', 'Intensity'],
                'mask_keywords': ['PB', 'Mask'],
                'mask_exclude_keywords': ['Dilated'],
                'dilated_keywords': ['PB', 'Dilated', 'Mask'],
                'output_name': 'PB_Cap',
                'enlarge_rois': None,
                'max_background': None
            },
            {
                'name': 'DDX6',
                'intensity_keywords': ['DDX6', 'Intensity'],
                'mask_keywords': ['PB', 'Mask'],
                'mask_exclude_keywords': ['Dilated'],
                'dilated_keywords': ['PB', 'Dilated', 'Mask'],
                'output_name': 'DDX6',
                'enlarge_rois': None,
                'max_background': None
            },
            {
                'name': 'SG_Cap',
                'intensity_keywords': ['Cap', 'Intensity'],
                'mask_keywords': ['SG', 'Mask'],
                'mask_exclude_keywords': ['Dilated'],
                'dilated_keywords': ['SG', 'Dilated', 'Mask'],
                'output_name': 'SG_Cap',
                'enlarge_rois': None,
                'max_background': None
            },
            {
                'name': 'G3BP1',
                'intensity_keywords': ['G3BP1', 'Intensity'],
                'mask_keywords': ['SG', 'Mask'],
                'mask_exclude_keywords': ['Dilated'],
                'dilated_keywords': ['SG', 'Dilated', 'Mask'],
                'output_name': 'G3BP1',
                'enlarge_rois': None,
                'max_background': None
            }
        ]
    
    def _prompt_for_config_parameters(self, ui: UserInterfacePort, configs: List[Dict]) -> List[Dict]:
        """Prompt user to enter parameters for each analysis configuration."""
        ui.info("\n" + "=" * 60)
        ui.info("CONFIGURATION PARAMETERS")
        ui.info("=" * 60)
        ui.info("Please enter parameters for each analysis configuration.")
        ui.info("Press Enter to use default values shown in brackets.\n")

        for config in configs:
            ui.info(f"\n--- {config['name']} Configuration ---")

            # ROI enlargement
            while True:
                try:
                    enlarge_input = ui.prompt("  ROI enlargement pixels [0]: ").strip()
                    if enlarge_input == "":
                        config['enlarge_rois'] = 0
                        break
                    enlarge_val = int(enlarge_input)
                    config['enlarge_rois'] = enlarge_val
                    break
                except ValueError:
                    ui.error("    Error: Please enter a valid integer.")

            # Max background
            while True:
                try:
                    max_bg_input = ui.prompt("  Maximum background threshold [None]: ").strip()
                    if max_bg_input == "" or max_bg_input.lower() == "none":
                        config['max_background'] = None
                        break
                    max_bg_val = float(max_bg_input)
                    if max_bg_val < 0:
                        ui.error("    Error: Maximum background must be non-negative. Please try again.")
                        continue
                    config['max_background'] = max_bg_val
                    break
                except ValueError:
                    ui.error("    Error: Please enter a valid number or 'None'.")

        ui.info("\n" + "=" * 60)
        ui.info("CONFIGURATION SUMMARY")
        ui.info("=" * 60)
        for config in configs:
            ui.info(f"\n{config['name']}:")
            ui.info(f"  ROI enlargement: {config['enlarge_rois']} pixels")
            ui.info(f"  Max background: {config['max_background']}")
        ui.info("=" * 60 + "\n")

        return configs

