"""
Cell entity for Percell domain.

Represents a biological cell with its measurements and properties.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from .roi import ROI
from .metadata import Metadata


@dataclass
class Cell:
    """
    Represents a biological cell with its measurements and analysis results.
    
    This entity encapsulates all information about a segmented cell,
    including its ROI, measurements across channels, and analysis results.
    """
    
    # Identification
    cell_id: str
    name: Optional[str] = None
    
    # Associated ROI
    roi: Optional[ROI] = None
    
    # Cell properties
    cell_type: Optional[str] = None
    group: Optional[str] = None
    condition: Optional[str] = None
    timepoint: Optional[str] = None
    region: Optional[str] = None
    
    # Measurements across channels
    channel_measurements: Dict[str, Dict[str, float]] = None
    
    # Analysis results
    is_positive: Dict[str, bool] = None  # Positive/negative for each channel
    intensity_ratios: Dict[str, float] = None  # Ratios between channels
    
    # Quality metrics
    segmentation_quality: Optional[float] = None
    analysis_quality: Optional[float] = None
    
    # Metadata
    metadata: Optional[Metadata] = None
    
    # Additional properties
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.channel_measurements is None:
            self.channel_measurements = {}
        if self.is_positive is None:
            self.is_positive = {}
        if self.intensity_ratios is None:
            self.intensity_ratios = {}
        if self.properties is None:
            self.properties = {}
    
    def add_channel_measurement(self, channel: str, measurement_name: str, value: float) -> None:
        """
        Add a measurement for a specific channel.
        
        Args:
            channel: Channel identifier
            measurement_name: Name of the measurement
            value: Measurement value
        """
        if channel not in self.channel_measurements:
            self.channel_measurements[channel] = {}
        
        self.channel_measurements[channel][measurement_name] = value
    
    def get_channel_measurement(self, channel: str, measurement_name: str) -> Optional[float]:
        """
        Get a measurement value for a specific channel.
        
        Args:
            channel: Channel identifier
            measurement_name: Name of the measurement
            
        Returns:
            Measurement value or None if not found
        """
        return self.channel_measurements.get(channel, {}).get(measurement_name)
    
    def set_positive_status(self, channel: str, is_positive: bool) -> None:
        """
        Set the positive/negative status for a channel.
        
        Args:
            channel: Channel identifier
            is_positive: True if positive, False if negative
        """
        self.is_positive[channel] = is_positive
    
    def get_positive_status(self, channel: str) -> Optional[bool]:
        """
        Get the positive/negative status for a channel.
        
        Args:
            channel: Channel identifier
            
        Returns:
            True if positive, False if negative, None if not determined
        """
        return self.is_positive.get(channel)
    
    def calculate_intensity_ratio(self, numerator_channel: str, denominator_channel: str) -> Optional[float]:
        """
        Calculate intensity ratio between two channels.
        
        Args:
            numerator_channel: Channel for numerator
            denominator_channel: Channel for denominator
            
        Returns:
            Intensity ratio or None if measurements not available
        """
        num_intensity = self.get_channel_measurement(numerator_channel, 'mean_intensity')
        denom_intensity = self.get_channel_measurement(denominator_channel, 'mean_intensity')
        
        if num_intensity is None or denom_intensity is None or denom_intensity == 0:
            return None
        
        ratio = num_intensity / denom_intensity
        ratio_key = f"{numerator_channel}_{denominator_channel}_ratio"
        self.intensity_ratios[ratio_key] = ratio
        
        return ratio
    
    def get_intensity_ratio(self, numerator_channel: str, denominator_channel: str) -> Optional[float]:
        """
        Get pre-calculated intensity ratio between two channels.
        
        Args:
            numerator_channel: Channel for numerator
            denominator_channel: Channel for denominator
            
        Returns:
            Intensity ratio or None if not calculated
        """
        ratio_key = f"{numerator_channel}_{denominator_channel}_ratio"
        return self.intensity_ratios.get(ratio_key)
    
    def get_area(self) -> Optional[float]:
        """
        Get the cell area from its ROI.
        
        Returns:
            Cell area in pixels or None if ROI not available
        """
        if self.roi is None:
            return None
        
        if self.roi.area is not None:
            return self.roi.area
        
        # Calculate area if not already computed
        return self.roi.calculate_area()
    
    def get_centroid(self) -> Optional[tuple]:
        """
        Get the cell centroid from its ROI.
        
        Returns:
            Centroid coordinates (x, y) or None if ROI not available
        """
        if self.roi is None:
            return None
        
        if self.roi.centroid is not None:
            return self.roi.centroid
        
        # Calculate centroid if not already computed
        return self.roi.calculate_centroid()
    
    def is_valid(self) -> bool:
        """
        Check if the cell has valid data for analysis.
        
        Returns:
            True if cell has required data
        """
        return (
            self.cell_id is not None and
            self.roi is not None and
            len(self.channel_measurements) > 0
        )
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for this cell.
        
        Returns:
            Dictionary with cell statistics
        """
        stats = {
            'cell_id': self.cell_id,
            'cell_type': self.cell_type,
            'group': self.group,
            'condition': self.condition,
            'timepoint': self.timepoint,
            'region': self.region,
            'area': self.get_area(),
            'centroid': self.get_centroid(),
            'num_channels_measured': len(self.channel_measurements),
            'num_positive_channels': sum(1 for status in self.is_positive.values() if status),
            'segmentation_quality': self.segmentation_quality,
            'analysis_quality': self.analysis_quality
        }
        
        # Add channel-specific measurements
        for channel, measurements in self.channel_measurements.items():
            for measurement, value in measurements.items():
                stats[f"{channel}_{measurement}"] = value
        
        # Add positive/negative status
        for channel, status in self.is_positive.items():
            stats[f"{channel}_positive"] = status
        
        # Add intensity ratios
        for ratio_name, ratio_value in self.intensity_ratios.items():
            stats[f"ratio_{ratio_name}"] = ratio_value
        
        return stats
    
    def clone(self) -> 'Cell':
        """
        Create a deep copy of this cell.
        
        Returns:
            New Cell instance with copied data
        """
        return Cell(
            cell_id=f"{self.cell_id}_copy",
            name=f"{self.name}_copy" if self.name else None,
            roi=self.roi,  # ROI is immutable enough to share
            cell_type=self.cell_type,
            group=self.group,
            condition=self.condition,
            timepoint=self.timepoint,
            region=self.region,
            channel_measurements={k: v.copy() for k, v in self.channel_measurements.items()},
            is_positive=self.is_positive.copy(),
            intensity_ratios=self.intensity_ratios.copy(),
            segmentation_quality=self.segmentation_quality,
            analysis_quality=self.analysis_quality,
            metadata=self.metadata,
            properties=self.properties.copy()
        )
