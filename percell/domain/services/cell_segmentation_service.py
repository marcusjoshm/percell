"""Segmentation business logic and parameter handling."""

from __future__ import annotations

from ..models import ChannelConfig


class CellSegmentationService:
    """Defines segmentation-related business rules independent of tools."""

    def determine_segmentation_parameters(self, channel_config: ChannelConfig) -> dict[str, object]:
        """Derive segmentation parameters from channel configuration.

        Args:
            channel_config: Configuration describing the target channel.

        Returns:
            Mapping of parameter names to values.
        """

        raise NotImplementedError

    def postprocess_masks(self, mask_paths: list[str]) -> list[str]:
        """Post-process segmentation masks according to business rules.

        Args:
            mask_paths: Paths to segmentation mask files.

        Returns:
            Paths to post-processed mask files.
        """

        raise NotImplementedError


