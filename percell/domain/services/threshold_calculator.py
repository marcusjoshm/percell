"""
ThresholdCalculator

Pure domain service implementing common thresholding algorithms over numpy arrays.
This module contains no file I/O or external tool invocations.
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np


class ThresholdCalculator:
    """Thresholding algorithms implemented in pure numpy."""

    def calculate_otsu_threshold(self, image: np.ndarray) -> float:
        """
        Compute Otsu's threshold for a grayscale image.

        - Accepts uint8/uint16/float arrays. Floats are assumed in [0, 1] or will be
          scaled to that range based on min/max.
        - Returns the threshold value in the same numeric scale as the input image.
        """
        if image is None:
            raise ValueError("image must not be None")

        img = np.asarray(image)
        if img.ndim > 2:
            # Convert to grayscale by averaging channels
            img = np.mean(img, axis=-1)

        # Flatten and drop NaNs/Infs
        values = img.astype(np.float64).ravel()
        values = values[np.isfinite(values)]
        if values.size == 0:
            return 0.0

        # Normalize to [0, 1] for robust histogramming
        v_min = float(np.min(values))
        v_max = float(np.max(values))
        if v_max <= v_min:
            return v_min
        norm = (values - v_min) / (v_max - v_min)

        # Histogram with fixed bins
        num_bins = 256
        hist, bin_edges = np.histogram(norm, bins=num_bins, range=(0.0, 1.0))
        hist = hist.astype(np.float64)

        # Probabilities
        total = hist.sum()
        if total == 0:
            return v_min
        prob = hist / total

        # Cumulative sums of class probabilities and class means
        omega = np.cumsum(prob)
        mu = np.cumsum(prob * (np.arange(num_bins)))
        mu_t = mu[-1]

        # Between-class variance for each threshold
        numerator = (mu_t * omega - mu) ** 2
        denominator = omega * (1.0 - omega)
        with np.errstate(divide="ignore", invalid="ignore"):
            sigma_b2 = np.where(denominator > 0, numerator / denominator, 0.0)

        # Maximize between-class variance
        k_star = int(np.argmax(sigma_b2))

        # Convert back to original scale: pick threshold between bin edges
        # Use the right edge of the selected bin as the threshold in normalized space
        thr_norm = (bin_edges[k_star] + bin_edges[k_star + 1]) * 0.5
        threshold = v_min + thr_norm * (v_max - v_min)
        return float(threshold)

    def apply_threshold(self, image: np.ndarray, threshold: float, high_value: float = 1.0) -> np.ndarray:
        """
        Apply a fixed threshold to produce a binary mask.

        Returns a mask with the same shape as the input (single channel), with
        values in {0, high_value} (default high_value=1.0).
        """
        if image is None:
            raise ValueError("image must not be None")
        img = np.asarray(image)
        if img.ndim > 2:
            img = np.mean(img, axis=-1)
        mask = (img >= threshold).astype(img.dtype if np.issubdtype(img.dtype, np.integer) else np.float32)
        if high_value != 1.0:
            mask = mask * high_value
        return mask

    def generate_binary_mask(self, image: np.ndarray) -> Tuple[float, np.ndarray]:
        """
        Convenience: compute Otsu threshold and return (threshold, mask).
        Mask is float32 in {0.0, 1.0}.
        """
        thr = self.calculate_otsu_threshold(image)
        mask = self.apply_threshold(image, thr, high_value=1.0).astype(np.float32)
        return thr, mask


