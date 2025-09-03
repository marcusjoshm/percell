"""
Metadata adapter for Percell.

Skeleton implementation of MetadataPort that can be extended to parse
filenames and read image headers as needed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
import re

from percell.ports.outbound.metadata_port import MetadataPort, MetadataError
from percell.domain.entities.metadata import Metadata
from percell.domain.entities.image import Image
from percell.domain.value_objects.file_path import FilePath


class FileNameMetadataAdapter(MetadataPort):
    def extract_metadata_from_filename(self, file_path: FilePath) -> Metadata:
        # Minimal parser: cond_<cond>_t<time>_reg<region>_ch<channel>.*
        # e.g., cond_A_t01_reg3_chGFP.tif
        name = file_path.get_name()
        stem = file_path.get_stem()
        m = re.search(
            r"cond_(?P<cond>[^_]+).*?t(?P<time>\d+).*?reg(?P<region>\d+).*?ch(?P<channel>[^_.]+)",
            stem,
            flags=re.IGNORECASE,
        )
        metadata = Metadata(
            filename=name,
            file_path=file_path.path,
            file_extension=file_path.get_suffix(),
        )
        if m:
            metadata.condition = m.group("cond")
            metadata.timepoint = m.group("time")
            metadata.region = m.group("region")
            metadata.channel = m.group("channel")
        return metadata

    def extract_metadata_from_image(self, image_path: FilePath) -> Metadata:
        raise NotImplementedError(
            "FileNameMetadataAdapter.extract_metadata_from_image is not implemented yet"
        )

    def extract_metadata_from_directory(self, directory: FilePath) -> List[Metadata]:
        raise NotImplementedError(
            "FileNameMetadataAdapter.extract_metadata_from_directory is not implemented yet"
        )

    def query_metadata(self, filters: Dict[str, Any]) -> List[Metadata]:
        return []

    def generate_naming_convention(self, metadata: Metadata, template: Optional[str] = None) -> str:
        if template:
            try:
                return template.format(
                    condition=metadata.condition or "",
                    timepoint=metadata.timepoint or "",
                    region=metadata.region or "",
                    channel=metadata.channel or "",
                )
            except Exception:
                pass
        return metadata.get_naming_convention()

    def validate_naming_convention(self, filename: str) -> bool:
        return True

    def get_unique_conditions(self, metadata_list: List[Metadata]) -> Set[str]:
        return {m.condition for m in metadata_list if getattr(m, 'condition', None)}

    def get_unique_timepoints(self, metadata_list: List[Metadata]) -> Set[str]:
        return {m.timepoint for m in metadata_list if getattr(m, 'timepoint', None)}

    def get_unique_regions(self, metadata_list: List[Metadata]) -> Set[str]:
        return {m.region for m in metadata_list if getattr(m, 'region', None)}

    def get_unique_channels(self, metadata_list: List[Metadata]) -> Set[str]:
        return {m.channel for m in metadata_list if getattr(m, 'channel', None)}

    def group_by_condition(self, metadata_list: List[Metadata]) -> Dict[str, List[Metadata]]:
        groups: Dict[str, List[Metadata]] = {}
        for item in metadata_list:
            key = item.condition or ""
            groups.setdefault(key, []).append(item)
        return groups

    def group_by_timepoint(self, metadata_list: List[Metadata]) -> Dict[str, List[Metadata]]:
        groups: Dict[str, List[Metadata]] = {}
        for item in metadata_list:
            key = item.timepoint or ""
            groups.setdefault(key, []).append(item)
        return groups

    def group_by_region(self, metadata_list: List[Metadata]) -> Dict[str, List[Metadata]]:
        groups: Dict[str, List[Metadata]] = {}
        for item in metadata_list:
            key = item.region or ""
            groups.setdefault(key, []).append(item)
        return groups

    def find_matching_files(
        self, reference_metadata: Metadata, search_directory: FilePath, match_criteria: List[str]
    ) -> List[FilePath]:
        return []

    def create_metadata_index(self, directory: FilePath) -> Dict[str, Metadata]:
        return {}

    def update_metadata_index(self, index: Dict[str, Metadata], new_files: List[FilePath]) -> Dict[str, Metadata]:
        return index

    def validate_metadata_completeness(self, metadata: Metadata) -> Dict[str, bool]:
        return {}

    def merge_metadata(self, metadata_list: List[Metadata]) -> Metadata:
        raise NotImplementedError("FileNameMetadataAdapter.merge_metadata is not implemented yet")

    def export_metadata(self, metadata_list: List[Metadata], output_path: FilePath, format: str = "json") -> None:
        raise NotImplementedError("FileNameMetadataAdapter.export_metadata is not implemented yet")

    def import_metadata(self, input_path: FilePath) -> List[Metadata]:
        raise NotImplementedError("FileNameMetadataAdapter.import_metadata is not implemented yet")

    def get_metadata_statistics(self, metadata_list: List[Metadata]) -> Dict[str, Any]:
        return {}

    def detect_naming_pattern(self, file_paths: List[FilePath]) -> Optional[str]:
        return None

    def suggest_metadata_corrections(self, metadata: Metadata) -> List[str]:
        return []


