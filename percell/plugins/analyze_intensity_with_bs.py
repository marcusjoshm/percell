#!/usr/bin/env python3
"""
Microscopy Intensity Analysis
Analyzes intensity measurements in ROIs using per-ROI local background subtraction.
"""

import numpy as np
from pathlib import Path
from PIL import Image
import tifffile
import matplotlib.pyplot as plt
from scipy import ndimage
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
from roifile import ImagejRoi
import zipfile


def load_image(filepath):
    """Load an image file and convert to numpy array."""
    img = Image.open(filepath)
    return np.array(img)


def load_imagej_rois(roi_zip_path):
    """
    Load ROIs from ImageJ ROI zip file.

    Args:
        roi_zip_path: Path to ImageJ ROI zip file

    Returns:
        List of ROI dictionaries with coordinates and properties
    """
    rois = []
    with zipfile.ZipFile(roi_zip_path, 'r') as zf:
        for name in sorted(zf.namelist()):  # Sort to ensure consistent ordering
            with zf.open(name) as roi_file:
                roi_bytes = roi_file.read()
                roi = ImagejRoi.frombytes(roi_bytes)
                rois.append({
                    'name': name,
                    'roi': roi,
                    'coordinates': roi.coordinates(),
                    'bytes': roi_bytes  # Store original bytes for ImageJ processing
                })
    return rois


def enlarge_rois_with_imagej(rois, pixels):
    """
    Enlarge ROIs using binary dilation (equivalent to ImageJ's RoiEnlarger).

    Args:
        rois: List of ROI dictionaries from load_imagej_rois
        pixels: Number of pixels to enlarge (positive) or shrink (negative)

    Returns:
        List of enlarged ROI dictionaries with updated coordinates

    Note: This uses scipy's binary dilation which produces similar results to
    ImageJ's RoiEnlarger but is faster and doesn't require Java/ImageJ initialization.
    """
    print(f"  Enlarging ROIs by {pixels} pixels using binary dilation...")

    # We need image_shape to create masks. Get it from the first successful coordinate conversion
    # For now, we'll determine it from the max coordinates
    max_x = max_y = 0
    for roi_dict in rois:
        coords = roi_dict['coordinates']
        if len(coords) > 0:
            max_x = max(max_x, int(np.max(coords[:, 0])))
            max_y = max(max_y, int(np.max(coords[:, 1])))

    # Add some padding to ensure ROIs fit
    image_shape = (max_y + 100, max_x + 100)

    enlarged_rois = []

    for roi_dict in rois:
        # Convert ROI to mask
        mask = roi_to_mask(roi_dict['coordinates'], image_shape)

        # Create structuring element for dilation
        structure = ndimage.generate_binary_structure(2, 1)  # 4-connected

        # Enlarge (dilate) or shrink (erode) the mask
        if pixels > 0:
            enlarged_mask = ndimage.binary_dilation(mask, structure=structure,
                                                   iterations=pixels).astype(np.uint8)
        elif pixels < 0:
            enlarged_mask = ndimage.binary_erosion(mask, structure=structure,
                                                  iterations=abs(pixels)).astype(np.uint8)
        else:
            enlarged_mask = mask

        # Extract new coordinates from the enlarged mask boundary
        from skimage.measure import find_contours
        contours = find_contours(enlarged_mask, 0.5)

        if len(contours) > 0:
            # Use the largest contour
            largest_contour = max(contours, key=len)
            # Convert from (row, col) to (x, y)
            new_coords = np.column_stack((largest_contour[:, 1], largest_contour[:, 0]))
        else:
            # If no contour found, use original coordinates
            new_coords = roi_dict['coordinates']

        enlarged_rois.append({
            'name': roi_dict['name'],
            'roi': roi_dict['roi'],  # Keep original roi object
            'coordinates': new_coords,
            'bytes': roi_dict.get('bytes', b'')
        })

    print(f"  Successfully enlarged {len(enlarged_rois)} ROIs by {pixels} pixels")
    return enlarged_rois


def roi_to_mask(roi_coords, image_shape):
    """
    Convert ROI coordinates to a binary mask.

    Args:
        roi_coords: ROI coordinates array (N x 2)
        image_shape: Shape of the output mask

    Returns:
        Binary mask with ROI pixels set to 1
    """
    from skimage.draw import polygon

    mask = np.zeros(image_shape, dtype=np.uint8)
    if len(roi_coords) > 0:
        # ROI coordinates are (x, y), but polygon needs (row, col) = (y, x)
        rr, cc = polygon(roi_coords[:, 1], roi_coords[:, 0], image_shape)
        mask[rr, cc] = 1
    return mask


def gaussian(x, amp, mean, std):
    """Gaussian function for peak fitting."""
    return amp * np.exp(-((x - mean) ** 2) / (2 * std ** 2))


def find_gaussian_peaks(data, n_bins=50, max_background=None):
    """
    Find Gaussian peaks in a histogram of the data.

    Args:
        data: Array of intensity values
        n_bins: Number of bins for histogram
        max_background: If specified, only consider peaks below this value for background

    Returns:
        Dictionary with peak information and histogram data
    """
    if len(data) == 0:
        return None

    # Create histogram with range starting at 0 to capture near-zero peaks
    data_max = float(np.max(data))
    hist, bin_edges = np.histogram(data, bins=n_bins, range=(0, data_max))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Smooth the histogram slightly to reduce noise
    from scipy.ndimage import gaussian_filter1d
    hist_smooth = gaussian_filter1d(hist.astype(float), sigma=2)

    # Find peaks with reasonable prominence to focus on significant features
    # Using 15% of max as minimum prominence to avoid noise
    min_prominence = np.max(hist_smooth) * 0.15
    peaks, properties = find_peaks(hist_smooth, prominence=min_prominence)

    if len(peaks) == 0:
        # If no prominent peaks found, use the bin with maximum count as the peak
        # This is more robust than lowering the prominence threshold
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

    # Get the peak positions (intensity values)
    peak_positions = bin_centers[peaks]
    peak_prominences = properties['prominences']

    # Determine background value
    if max_background is not None:
        # Constrained mode: Only consider peaks below max_background threshold
        peaks_below_threshold = peak_positions < max_background

        if np.any(peaks_below_threshold):
            # Select the most prominent peak below threshold
            prominences_below = peak_prominences[peaks_below_threshold]
            positions_below = peak_positions[peaks_below_threshold]
            most_prominent_idx = np.argmax(prominences_below)
            background_value = positions_below[most_prominent_idx]
        else:
            # No peaks below threshold, find bin with highest count below threshold
            bins_below_threshold = bin_centers < max_background
            if np.any(bins_below_threshold):
                # Get histogram counts for bins below threshold
                hist_below = hist[bins_below_threshold]
                bin_centers_below = bin_centers[bins_below_threshold]
                max_count_idx = np.argmax(hist_below)
                background_value = bin_centers_below[max_count_idx]
            else:
                # Fallback: use the leftmost peak
                sorted_by_position = np.argsort(peak_positions)
                background_value = peak_positions[sorted_by_position[0]]
    else:
        # Default mode: Use the leftmost (lowest intensity) peak
        sorted_by_position = np.argsort(peak_positions)
        background_value = peak_positions[sorted_by_position[0]]

    # For reporting, also sort by prominence to return the most prominent peaks
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


def analyze_roi_intensity_from_rois(mask_rois, perimeter_rois, intensity_image,
                                    image_shape, method='gaussian_peaks',
                                    bg_multiplication_factor=1.0, max_background=None):
    """
    Analyze intensity measurements for each ROI using local background subtraction.

    Args:
        mask_rois: List of ROI dictionaries for regions of interest
        perimeter_rois: List of ROI dictionaries for local background regions
        intensity_image: Intensity image
        image_shape: Shape of the images
        method: 'minimum' or 'gaussian_peaks'
        bg_multiplication_factor: Multiplication factor for background value (default 1.0)

    Returns:
        Dictionary with per-ROI analysis results
    """
    n_rois = len(mask_rois)
    print(f"  Found {n_rois} ROIs from ROI files")

    results = []

    for i in range(n_rois):
        # Create masks from ROIs
        roi_mask = roi_to_mask(mask_rois[i]['coordinates'], image_shape)
        background_mask = roi_to_mask(perimeter_rois[i]['coordinates'], image_shape)

        # Extract intensities
        roi_intensities = intensity_image[roi_mask > 0]
        background_intensities = intensity_image[background_mask > 0]

        # Skip if no pixels found
        if len(roi_intensities) == 0 or len(background_intensities) == 0:
            continue

        # Determine background value based on method
        if method == 'minimum':
            background_raw = np.min(background_intensities)
            peak_info = None
        elif method == 'gaussian_peaks':
            peak_info = find_gaussian_peaks(background_intensities, max_background=max_background)
            background_raw = peak_info['background_value'] if peak_info else np.mean(background_intensities)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Apply multiplication factor to background value
        background = background_raw * bg_multiplication_factor

        # Background-subtracted intensities
        bg_subtracted = roi_intensities - background

        # Calculate statistics
        roi_result = {
            'roi_id': i + 1,  # 1-indexed ROI ID
            'roi_name': mask_rois[i]['name'],
            'n_pixels': len(roi_intensities),
            'n_background_pixels': len(background_intensities),

            # Intensity statistics
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


def visualize_roi_histograms(analysis_results, data_dir, dataset_name, max_plots=9):
    """
    Create histogram visualizations for the first few ROIs showing
    background intensity distributions and detected peaks.
    """
    rois = analysis_results['rois']
    n_to_plot = min(max_plots, len(rois))

    if n_to_plot == 0:
        return

    # Create subplots
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
            ax.text(0.5, 0.5, f"ROI {roi['roi_id']}\nNo data",
                   ha='center', va='center')
            ax.axis('off')
            continue

        # Plot histogram
        ax.bar(peak_info['bin_centers'], peak_info['hist'],
               width=np.diff(peak_info['bin_centers'])[0] * 0.8,
               alpha=0.6, label='Histogram')

        # Plot smoothed histogram
        if 'hist_smooth' in peak_info:
            ax.plot(peak_info['bin_centers'], peak_info['hist_smooth'],
                   'r-', linewidth=2, label='Smoothed')

        # Mark detected peaks
        if len(peak_info['peaks']) > 0:
            for peak_val in peak_info['peaks']:
                ax.axvline(peak_val, color='green', linestyle='--', linewidth=2)

        # Mark background value
        ax.axvline(peak_info['background_value'], color='blue',
                  linestyle='-', linewidth=2, label=f"BG={peak_info['background_value']:.1f}")

        ax.set_title(f"ROI {roi['roi_id']}\n"
                    f"{peak_info['n_peaks']} peak(s), {roi['n_background_pixels']} px")
        ax.set_xlabel('Intensity')
        ax.set_ylabel('Count')
        ax.legend(fontsize=8)

    # Hide unused subplots
    for idx in range(n_to_plot, n_rows * n_cols):
        row = idx // n_cols
        col = idx % n_cols
        axes[row, col].axis('off')

    plt.tight_layout()
    output_path = Path(data_dir) / f"{dataset_name}_background_histograms.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path.name}")


def save_summary_statistics(analysis_results, data_dir, dataset_name):
    """Save summary statistics to a CSV file."""
    import csv

    rois = analysis_results['rois']
    output_path = Path(data_dir) / f"{dataset_name}_intensity_analysis.csv"

    with open(output_path, 'w', newline='') as f:
        if len(rois) == 0:
            return

        # Get fieldnames from first ROI (exclude peak_info objects)
        fieldnames = [k for k in rois[0].keys() if 'peak_info' not in k]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for roi in rois:
            # Filter out peak_info and convert negative values to empty strings
            row = {}
            for k, v in roi.items():
                if 'peak_info' not in k:
                    # If the value is numeric and negative, use empty string
                    if isinstance(v, (int, float, np.integer, np.floating)) and v < 0:
                        row[k] = ''
                    else:
                        row[k] = v
            writer.writerow(row)

    print(f"  Saved: {output_path.name}")


def find_file_matching_keywords(files, keywords, exclude_keywords=None):
    """
    Find a file that contains all specified keywords in its name (case-insensitive).

    Args:
        files: List of Path objects
        keywords: List of keywords that must all be present in the filename
        exclude_keywords: List of keywords that must NOT be present in the filename

    Returns:
        First matching file or None if no match found
    """
    keywords_lower = [k.lower() for k in keywords]
    exclude_lower = [k.lower() for k in exclude_keywords] if exclude_keywords else []

    for f in files:
        filename_lower = f.name.lower()
        # Check if all required keywords are present
        if all(kw in filename_lower for kw in keywords_lower):
            # Check if any excluded keywords are present
            if any(kw in filename_lower for kw in exclude_lower):
                continue
            return f
    return None


def get_analysis_configurations():
    """
    Define analysis configurations specifying which intensity images to analyze
    with which ROI masks and what to name the output files.

    Returns:
        List of configuration dictionaries
    """
    return [
        {
            'name': 'PB_Cap',
            'intensity_keywords': ['Cap', 'Intensity'],
            'mask_keywords': ['PB', 'Mask'],
            'mask_exclude_keywords': ['Dilated'],  # Exclude dilated masks
            'dilated_keywords': ['PB', 'Dilated', 'Mask'],
            'output_name': 'PB_Cap',
            'bg_factor': None,  # To be filled by user input
            'enlarge_rois': None,  # To be filled by user input
            'max_background': None  # To be filled by user input
        },
        {
            'name': 'DDX6',
            'intensity_keywords': ['DDX6', 'Intensity'],
            'mask_keywords': ['PB', 'Mask'],
            'mask_exclude_keywords': ['Dilated'],  # Exclude dilated masks
            'dilated_keywords': ['PB', 'Dilated', 'Mask'],
            'output_name': 'DDX6',
            'bg_factor': None,
            'enlarge_rois': None,
            'max_background': None
        },
        {
            'name': 'SG_Cap',
            'intensity_keywords': ['Cap', 'Intensity'],
            'mask_keywords': ['SG', 'Mask'],
            'mask_exclude_keywords': ['Dilated'],  # Exclude dilated masks
            'dilated_keywords': ['SG', 'Dilated', 'Mask'],
            'output_name': 'SG_Cap',
            'bg_factor': None,
            'enlarge_rois': None,
            'max_background': None
        },
        {
            'name': 'G3BP1',
            'intensity_keywords': ['G3BP1', 'Intensity'],
            'mask_keywords': ['SG', 'Mask'],
            'mask_exclude_keywords': ['Dilated'],  # Exclude dilated masks
            'dilated_keywords': ['SG', 'Dilated', 'Mask'],
            'output_name': 'G3BP1',
            'bg_factor': None,
            'enlarge_rois': None,
            'max_background': None
        }
    ]


def prompt_for_config_parameters(configs):
    """
    Prompt user to enter parameters for each analysis configuration.

    Args:
        configs: List of configuration dictionaries

    Returns:
        Updated list of configuration dictionaries with user-provided parameters
    """
    print("\n" + "=" * 60)
    print("CONFIGURATION PARAMETERS")
    print("=" * 60)
    print("Please enter parameters for each analysis configuration.")
    print("Press Enter to use default values shown in brackets.\n")

    for config in configs:
        print(f"\n--- {config['name']} Configuration ---")

        # Background factor
        while True:
            try:
                bg_input = input("  Background multiplication factor [1.0]: ").strip()
                if bg_input == "":
                    config['bg_factor'] = 1.0
                    break
                bg_val = float(bg_input)
                if bg_val < 0:
                    print("    Error: Background factor must be non-negative. Please try again.")
                    continue
                config['bg_factor'] = bg_val
                break
            except ValueError:
                print("    Error: Please enter a valid number.")

        # ROI enlargement
        while True:
            try:
                enlarge_input = input("  ROI enlargement pixels [0]: ").strip()
                if enlarge_input == "":
                    config['enlarge_rois'] = 0
                    break
                enlarge_val = int(enlarge_input)
                config['enlarge_rois'] = enlarge_val
                break
            except ValueError:
                print("    Error: Please enter a valid integer.")

        # Max background
        while True:
            try:
                max_bg_input = input("  Maximum background threshold [None]: ").strip()
                if max_bg_input == "" or max_bg_input.lower() == "none":
                    config['max_background'] = None
                    break
                max_bg_val = float(max_bg_input)
                if max_bg_val < 0:
                    print("    Error: Maximum background must be non-negative. Please try again.")
                    continue
                config['max_background'] = max_bg_val
                break
            except ValueError:
                print("    Error: Please enter a valid number or 'None'.")

    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    for config in configs:
        print(f"\n{config['name']}:")
        print(f"  Background factor: {config['bg_factor']}")
        print(f"  ROI enlargement: {config['enlarge_rois']} pixels")
        print(f"  Max background: {config['max_background']}")
    print("=" * 60 + "\n")

    return configs


def main():
    """Main analysis function."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Microscopy Intensity Analysis')
    parser.add_argument('base_dir', nargs='?', default="/Volumes/NX-01-A/2025-10-08_test_data",
                       help='Base directory containing subdirectories with microscopy data')

    args = parser.parse_args()

    base_dir = args.base_dir
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"Error: Base directory '{base_dir}' does not exist")
        return

    # Find all subdirectories containing .tif files
    subdirs = [d for d in base_path.iterdir() if d.is_dir()]

    if len(subdirs) == 0:
        print(f"Error: No subdirectories found in '{base_dir}'")
        return

    print(f"Found {len(subdirs)} subdirectories to analyze")

    # Get analysis configurations and prompt for parameters
    analysis_configs = get_analysis_configurations()
    analysis_configs = prompt_for_config_parameters(analysis_configs)

    # Process each subdirectory
    for data_dir in subdirs:
        dataset_name = data_dir.name
        method = "gaussian_peaks"  # Default method

        print("=" * 60)
        print(f"Analyzing {dataset_name} Dataset")
        print("=" * 60)

        # Get all available files in the directory
        tif_files = list(data_dir.glob("*.tif"))
        zip_files = list(data_dir.glob("*.zip"))

        # Process each analysis configuration
        for config in analysis_configs:
            print(f"\n--- Processing {config['name']} analysis ---")
            print(f"  Background multiplication factor: {config['bg_factor']}")
            print(f"  ROI enlargement: {config['enlarge_rois']} pixels")
            print(f"  Maximum background constraint: {config['max_background']}")

            # Find matching files for this configuration
            intensity_file = find_file_matching_keywords(tif_files, config['intensity_keywords'])
            mask_file = find_file_matching_keywords(zip_files, config['mask_keywords'],
                                                    exclude_keywords=config.get('mask_exclude_keywords'))
            dilated_file = find_file_matching_keywords(zip_files, config['dilated_keywords'])

            # Check if all required files were found
            if intensity_file is None:
                print(f"  Skipping {config['name']}: No intensity file found matching {config['intensity_keywords']}")
                continue

            if mask_file is None:
                print(f"  Skipping {config['name']}: No mask file found matching {config['mask_keywords']}")
                continue

            if dilated_file is None:
                print(f"  Skipping {config['name']}: No dilated mask file found matching {config['dilated_keywords']}")
                continue

            # Verify that mask and dilated files are different
            if mask_file == dilated_file:
                print(f"  Skipping {config['name']}: Mask and dilated mask files are the same")
                continue

            print(f"  Intensity image: {intensity_file.name}")
            print(f"  Mask ROIs: {mask_file.name}")
            print(f"  Dilated mask ROIs: {dilated_file.name}")

            # Load intensity image
            intensity_image = load_image(str(intensity_file))
            image_shape = intensity_image.shape

            # Load ROI files
            mask_rois = load_imagej_rois(str(mask_file))
            dilated_rois = load_imagej_rois(str(dilated_file))

            # Optionally further enlarge the dilated ROIs using config-specific parameter
            if config['enlarge_rois'] > 0:
                background_rois = enlarge_rois_with_imagej(dilated_rois, pixels=config['enlarge_rois'])
            else:
                background_rois = dilated_rois

            # Analyze intensity using ROIs with config-specific parameters
            results = analyze_roi_intensity_from_rois(
                mask_rois, background_rois, intensity_image,
                image_shape, method=method, bg_multiplication_factor=config['bg_factor'],
                max_background=config['max_background']
            )

            # Print summary
            print("\n  Summary Statistics (Intensity measurements):")
            backgrounds = [r['background'] for r in results['rois']]
            bg_subtracted = [r['mean_bg_subtracted'] for r in results['rois']]
            if len(backgrounds) > 0:
                print(f"    Mean background: {np.mean(backgrounds):.2f}")
                print(f"    Median background: {np.median(backgrounds):.2f}")
                print(f"    ROIs with positive signal (>0): {np.sum(np.array(bg_subtracted) > 0)}/{len(bg_subtracted)}")

            # Create output filename using dataset name and config output name
            output_name = f"{dataset_name}_{config['output_name']}"

            # Save results
            save_summary_statistics(results, data_dir, output_name)
            visualize_roi_histograms(results, data_dir, output_name)

        print()


if __name__ == "__main__":
    main()
