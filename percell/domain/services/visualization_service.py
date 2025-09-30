"""Visualization service for displaying combined masks, raw images, and overlays."""

from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict
import logging

from percell.domain.models import DatasetSelection
from percell.domain.services.data_selection_service import DataSelectionService
from percell.ports.driven.image_processing_port import ImageProcessingPort
from percell.domain.exceptions import VisualizationError


class VisualizationService:
    """Domain service for creating visualizations of masks, raw images, and overlays.

    This service contains pure domain logic for visualization and relies on
    injected dependencies for UI and image processing operations.
    """

    def __init__(self, image_processor: ImageProcessingPort, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.data_service = DataSelectionService()
        self.image_processor = image_processor

    def create_visualization_data(
        self,
        raw_data_dir: Path,
        masks_dir: Path,
        selection: DatasetSelection,
        overlay_alpha: float = 0.5
    ) -> bool:
        """Display combined visualization of raw data, masks, and overlay with interactive LUT controls.

        Args:
            raw_data_dir: Directory containing raw microscopy images
            masks_dir: Directory containing segmentation masks
            selection: Data selection configuration
            overlay_alpha: Alpha transparency for overlay (0.0-1.0)

        Returns:
            True if visualization was successfully created
        """
        try:
            # Get file lists based on selection
            raw_files = self._get_files_from_selection(raw_data_dir, selection)
            mask_files = self._find_corresponding_masks(raw_files, masks_dir)

            if not raw_files:
                self.logger.error("No raw data files found matching selection criteria")
                return False

            # Display images one at a time in sequence
            for idx, raw_file in enumerate(raw_files):
                mask_file = mask_files.get(idx)

                # Load raw image
                raw_img = self.image_processor.read_image(raw_file)

                # Load mask image if available
                mask_img = None
                if mask_file and mask_file.exists():
                    mask_img = self.image_processor.read_image(mask_file)

                # Display current image and wait for window close
                continue_viewing = self._create_single_image_visualization(
                    raw_img, mask_img, raw_file.name, overlay_alpha, idx + 1, len(raw_files)
                )

                # If user closed the window or pressed escape, stop viewing
                if not continue_viewing:
                    break

            return True

        except Exception as e:
            self.logger.error(f"Error creating visualization: {e}")
            return False

    def _create_single_image_visualization(
        self,
        raw_image: np.ndarray,
        mask_image: Optional[np.ndarray],
        file_name: str,
        overlay_alpha: float,
        current_index: int,
        total_count: int
    ) -> bool:
        """Create interactive visualization for a single image with LUT sliders.

        Args:
            raw_image: Raw microscopy image
            mask_image: Segmentation mask (optional)
            file_name: Name of the image file
            overlay_alpha: Alpha transparency for overlay
            current_index: Current image index (1-based)
            total_count: Total number of images

        Returns:
            True if user wants to continue viewing next image, False to stop
        """
        try:
            # Calculate intensity range for sliders
            raw_min = float(np.min(raw_image))
            raw_max = float(np.max(raw_image))

            # Initialize display range
            initial_min = raw_min
            initial_max = raw_max

            # Create figure with fixed size
            fig = plt.figure(figsize=(12, 8))

            # Create subplot layout (1 row, 3 columns)
            # Leave bottom space for sliders
            gs = fig.add_gridspec(1, 3,
                                 left=0.1, right=0.95,
                                 top=0.85, bottom=0.2,
                                 hspace=0.3, wspace=0.2)

            # Create image axes
            ax_raw = fig.add_subplot(gs[0, 0])
            ax_mask = fig.add_subplot(gs[0, 1])
            ax_overlay = fig.add_subplot(gs[0, 2])

            # Initialize with current LUT settings
            raw_display = self._apply_lut(raw_image, initial_min, initial_max)

            # Display raw image
            im_raw = ax_raw.imshow(raw_display, cmap='gray', vmin=0, vmax=1)
            ax_raw.set_title(f'Raw Image\n{file_name}', fontsize=10)
            ax_raw.axis('off')

            # Display mask
            if mask_image is not None:
                mask_display = self._normalize_for_display(mask_image)
                im_mask = ax_mask.imshow(mask_display, cmap='hot')
                ax_mask.set_title('Segmentation Mask', fontsize=10)
            else:
                ax_mask.text(0.5, 0.5, 'No mask\nfound',
                           ha='center', va='center', transform=ax_mask.transAxes,
                           fontsize=12)
                ax_mask.set_title('Mask: Not Available', fontsize=10)
                im_mask = None
            ax_mask.axis('off')

            # Display overlay
            if mask_image is not None:
                overlay = self._create_overlay(raw_display, mask_display, overlay_alpha)
                im_overlay = ax_overlay.imshow(overlay)
                ax_overlay.set_title('Overlay', fontsize=10)
            else:
                im_overlay = ax_overlay.imshow(raw_display, cmap='gray', vmin=0, vmax=1)
                ax_overlay.set_title('Overlay: No mask', fontsize=10)
            ax_overlay.axis('off')

            # Create slider axes
            slider_bottom = 0.05
            slider_height = 0.03
            slider_spacing = 0.05

            ax_min_slider = plt.axes([0.2, slider_bottom + slider_spacing, 0.6, slider_height])
            ax_max_slider = plt.axes([0.2, slider_bottom, 0.6, slider_height])

            # Create sliders
            min_slider = widgets.Slider(
                ax_min_slider, 'Min Intensity',
                raw_min, raw_max,
                valinit=initial_min,
                valfmt='%.0f'
            )

            max_slider = widgets.Slider(
                ax_max_slider, 'Max Intensity',
                raw_min, raw_max,
                valinit=initial_max,
                valfmt='%.0f'
            )

            # Update function for sliders
            def update_display(val):
                min_val = min_slider.val
                max_val = max_slider.val

                # Ensure min < max
                if min_val >= max_val:
                    if val == min_val:  # min slider moved
                        max_val = min_val + 1
                        max_slider.set_val(max_val)
                    else:  # max slider moved
                        min_val = max_val - 1
                        min_slider.set_val(min_val)

                # Update raw image with new LUT
                raw_display = self._apply_lut(raw_image, min_val, max_val)
                im_raw.set_array(raw_display)

                # Update overlay if mask exists
                if mask_image is not None:
                    mask_display = self._normalize_for_display(mask_image)
                    overlay = self._create_overlay(raw_display, mask_display, overlay_alpha)
                    im_overlay.set_array(overlay)
                else:
                    im_overlay.set_array(raw_display)

                fig.canvas.draw()

            # Connect sliders to update function
            min_slider.on_changed(update_display)
            max_slider.on_changed(update_display)

            # Add title and instructions
            next_text = "Close window to view next image" if current_index < total_count else "Close window to finish"
            fig.suptitle(f'Image {current_index} of {total_count}: {file_name}\n'
                        f'Use sliders to adjust intensity range. {next_text}',
                        fontsize=12)

            # Show the plot and wait for it to be closed
            plt.show()

            # Return True to continue to next image (unless this was the last one)
            return current_index < total_count

        except Exception as e:
            self.logger.error(f"Error creating single image visualization: {e}")
            return False

    def _apply_lut(self, image: np.ndarray, min_val: float, max_val: float) -> np.ndarray:
        """Apply Look-Up Table (LUT) transformation to image.

        Args:
            image: Input image
            min_val: Minimum intensity value to map to 0
            max_val: Maximum intensity value to map to 1

        Returns:
            LUT-adjusted image normalized to 0-1 range
        """
        if max_val <= min_val:
            max_val = min_val + 1

        # Apply LUT: map [min_val, max_val] to [0, 1]
        adjusted = (image.astype(np.float32) - min_val) / (max_val - min_val)

        # Clip to valid range
        return np.clip(adjusted, 0, 1)

    def _get_files_from_selection(self, root_dir: Path, selection: DatasetSelection) -> List[Path]:
        """Get list of files matching the data selection criteria."""
        # Update selection root to the provided directory
        selection_copy = DatasetSelection(
            root=root_dir,
            conditions=selection.conditions,
            timepoints=selection.timepoints,
            regions=selection.regions,
            channels=selection.channels
        )

        return self.data_service.generate_file_lists(selection_copy)

    def _find_corresponding_masks(
        self,
        raw_files: List[Path],
        masks_dir: Path
    ) -> Dict[int, Optional[Path]]:
        """Find corresponding mask files for raw image files.

        Args:
            raw_files: List of raw image file paths
            masks_dir: Directory containing mask files

        Returns:
            Dictionary mapping raw file index to corresponding mask file path
        """
        mask_mapping: Dict[int, Optional[Path]] = {}

        if not masks_dir.exists():
            return mask_mapping

        for i, raw_file in enumerate(raw_files):
            # Try to find mask file with similar name structure
            mask_candidates = []

            # Common mask naming patterns
            base_name = raw_file.stem
            patterns = [
                f"MASK_{base_name}.tif",  # Your naming pattern: MASK_filename.tif
                f"mask_{base_name}.tif",
                f"masks_{base_name}.tif",
                f"{base_name}_mask.tif",
                f"{base_name}_masks.tif",
                f"{base_name}.tif",  # Same name in mask directory
                f"{base_name}_cp_masks.tif",  # Cellpose naming
            ]

            # Search in masks directory recursively
            for pattern in patterns:
                candidates = list(masks_dir.rglob(pattern))
                if candidates:
                    mask_candidates.extend(candidates)

            # Also try to match by preserving directory structure
            try:
                rel_path = raw_file.relative_to(raw_file.parents[2])  # Relative to input root
                potential_mask = masks_dir / rel_path
                if potential_mask.exists():
                    mask_candidates.append(potential_mask)
            except (ValueError, IndexError):
                pass

            # Take the first valid candidate
            if mask_candidates:
                mask_mapping[i] = mask_candidates[0]
            else:
                mask_mapping[i] = None

        return mask_mapping

    def _normalize_for_display(self, image: np.ndarray) -> np.ndarray:
        """Normalize image data for display (0-1 range)."""
        if image.dtype == np.bool_:
            return image.astype(np.float32)

        img_min = np.min(image)
        img_max = np.max(image)

        if img_max > img_min:
            return (image.astype(np.float32) - img_min) / (img_max - img_min)
        else:
            return np.zeros_like(image, dtype=np.float32)

    def _create_overlay(
        self,
        raw_img: np.ndarray,
        mask_img: np.ndarray,
        alpha: float
    ) -> np.ndarray:
        """Create overlay of raw image and mask, only combining non-zero mask values.

        Args:
            raw_img: Normalized raw image (0-1 range)
            mask_img: Normalized mask image (0-1 range)
            alpha: Alpha blending factor for mask

        Returns:
            RGB overlay image
        """
        # Ensure both images are the same size
        if raw_img.shape != mask_img.shape:
            # Resize mask to match raw image
            from PIL import Image
            mask_pil = Image.fromarray((mask_img * 255).astype(np.uint8))
            mask_pil = mask_pil.resize((raw_img.shape[1], raw_img.shape[0]), Image.NEAREST)
            mask_img = np.array(mask_pil) / 255.0

        # Create RGB overlay starting with raw image as grayscale background
        overlay = np.stack([raw_img, raw_img, raw_img], axis=-1)

        # Create mask for non-zero values only
        mask_nonzero = mask_img > 0

        # Only apply green overlay where mask has non-zero values
        if np.any(mask_nonzero):
            # Create green overlay only for non-zero mask pixels
            green_overlay = np.zeros_like(overlay)
            green_overlay[:, :, 1] = mask_img  # Green channel

            # Apply alpha blending only to non-zero mask areas
            # Use broadcasting to apply mask to all channels
            mask_3d = np.stack([mask_nonzero, mask_nonzero, mask_nonzero], axis=-1)

            # Blend only where mask is non-zero
            overlay = np.where(mask_3d,
                             (1 - alpha) * overlay + alpha * green_overlay,
                             overlay)

        # Ensure values are in valid range
        return np.clip(overlay, 0, 1)
