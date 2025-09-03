"""
Domain MetadataService

Provides high-level operations to scan directories, extract and index metadata
from filenames/images via the MetadataPort, returning domain entities and
value objects rather than touching IO directly outside of ports.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import re

from percell.ports.outbound.metadata_port import MetadataPort
from percell.ports.outbound.storage_port import StoragePort
from percell.domain.entities.metadata import Metadata
from percell.domain.value_objects.file_path import FilePath


class MetadataService:
    def __init__(self, storage: StoragePort, metadata_port: MetadataPort) -> None:
        self.storage = storage
        self.metadata_port = metadata_port

    def scan_directory_for_metadata(
        self,
        directory: FilePath,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
    ) -> List[Metadata]:
        """
        Walk a directory and extract Metadata for files matching extensions.
        """
        exts = set([e.lower() for e in (extensions or ['.tif', '.tiff'])])
        files = self.storage.list_files(directory, pattern='**/*' if recursive else '*', recursive=recursive)
        results: List[Metadata] = []
        for fp in files:
            if fp.get_suffix().lower() in exts:
                md = self.metadata_port.extract_metadata_from_filename(fp)
                # Fill gaps from path/filename if adapter couldn't parse fully
                try:
                    rel = fp.path.relative_to(directory.path)
                    parts = list(rel.parts)
                    if len(parts) >= 1 and (md.condition is None):
                        md.condition = parts[0]
                except Exception:
                    pass
                name = fp.get_stem()
                # Region: everything before _chXX if present
                if (md.region is None) and ('_ch' in name):
                    md.region = name.split('_ch')[0]
                # Channel
                if md.channel is None:
                    m = re.search(r'(ch\d+)', name, flags=re.IGNORECASE)
                    if m:
                        md.channel = m.group(1)
                # Timepoint
                if md.timepoint is None:
                    m = re.search(r'(t\d+)', name, flags=re.IGNORECASE)
                    if m:
                        md.timepoint = m.group(1)
                results.append(md)
        return results

    def build_directory_index(self, directory: FilePath) -> Dict[str, Metadata]:
        """
        Build a mapping from file path to Metadata for the directory.
        """
        return self.metadata_port.create_metadata_index(directory)

    def find_matches(
        self,
        reference: Metadata,
        search_directory: FilePath,
        match_fields: List[str],
    ) -> List[FilePath]:
        """
        Find files whose metadata matches the reference on given fields.
        """
        return self.metadata_port.find_matching_files(reference, search_directory, match_fields)

    def summarize(self, metadata_list: List[Metadata]) -> Dict[str, int]:
        """
        Quick summary counts for conditions/timepoints/regions/channels.
        """
        conds = self.metadata_port.get_unique_conditions(metadata_list)
        tps = self.metadata_port.get_unique_timepoints(metadata_list)
        regs = self.metadata_port.get_unique_regions(metadata_list)
        chans = self.metadata_port.get_unique_channels(metadata_list)
        return {
            'conditions': len(conds),
            'timepoints': len(tps),
            'regions': len(regs),
            'channels': len(chans),
        }

    def extract_experiment_metadata(self, directory: FilePath) -> Dict[str, List[str]]:
        """
        High-level summary of experiment dimensions from a root directory.
        Returns dict with conditions, regions, timepoints, channels.
        """
        md_list = self.scan_directory_for_metadata(directory, recursive=True)
        conditions = sorted(list(self.metadata_port.get_unique_conditions(md_list)))
        regions = sorted(list(self.metadata_port.get_unique_regions(md_list)))
        timepoints = sorted(list(self.metadata_port.get_unique_timepoints(md_list)))
        channels = sorted(list(self.metadata_port.get_unique_channels(md_list)))
        return {
            'conditions': conditions,
            'regions': regions,
            'timepoints': timepoints,
            'channels': channels,
        }


