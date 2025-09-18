#!/usr/bin/env python3
"""
Advanced Image Processing Plugin for Percell

This plugin provides comprehensive microscopy image processing functionality including:
- Interactive directory selection with validation
- Metadata extraction from microscopy files with verbose output
- Maximum intensity projection for Z-series
- Channel merging for multi-channel images
- Image stitching for tile scans
- Z-stack creation with metadata preservation

This replaces the command-line functionality from image_metadata/workflow_orchestrator.py
and related scripts with an interactive menu-driven interface.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from percell.ports.driving.user_interface_port import UserInterfacePort

# Direct imports - these are required dependencies
import numpy as np
import tifffile
from PIL import Image


class MicroscopyMetadataExtractor:
    """Extract metadata from microscopy files with pattern analysis."""

    def __init__(self, base_directory: Path):
        self.base_directory = base_directory
        self.metadata = {}

    def parse_filename(self, filename: str) -> Dict:
        """Parse filename to extract image attributes."""
        file_data = {
            'filename': filename,
            'site': None,
            'z_plane': None,
            'channel': None,
            'timepoint': None,
            'image_name': '',
            'file_extension': '',
            'pattern': '',
            'tokens': {}
        }

        # Extract extension
        if '.' in filename:
            name_part, extension = filename.rsplit('.', 1)
            file_data['file_extension'] = extension.lower()
        else:
            name_part = filename

        # Parse different patterns
        tokens = []
        remaining_name = name_part

        # Site pattern: _s(\d+)
        site_match = re.search(r'_s(\d+)', remaining_name)
        if site_match:
            file_data['site'] = int(site_match.group(1))
            tokens.append(f"_s{site_match.group(1)}")
            remaining_name = remaining_name.replace(site_match.group(0), '')

        # Z-plane patterns: _z(\d+)
        z_match = re.search(r'_z(\d+)', remaining_name)
        if z_match:
            file_data['z_plane'] = int(z_match.group(1))
            tokens.append(f"_z{z_match.group(1)}")
            remaining_name = remaining_name.replace(z_match.group(0), '')

        # Channel patterns: _ch(\d+)
        ch_match = re.search(r'_ch(\d+)', remaining_name)
        if ch_match:
            file_data['channel'] = int(ch_match.group(1))
            tokens.append(f"_ch{ch_match.group(1)}")
            remaining_name = remaining_name.replace(ch_match.group(0), '')

        # Timepoint patterns: _t(\d+)
        t_match = re.search(r'_t(\d+)', remaining_name)
        if t_match:
            file_data['timepoint'] = int(t_match.group(1))
            tokens.append(f"_t{t_match.group(1)}")
            remaining_name = remaining_name.replace(t_match.group(0), '')

        file_data['image_name'] = remaining_name.strip('_')
        file_data['pattern'] = '_'.join(tokens) if tokens else 'simple'
        file_data['tokens'] = {
            'site': file_data['site'],
            'z_plane': file_data['z_plane'],
            'channel': file_data['channel'],
            'timepoint': file_data['timepoint']
        }

        return file_data

    def analyze_image_group(self, group_name: str, files: List[Path]) -> Dict:
        """Analyze a group of related image files."""
        parsed_files = [self.parse_filename(f.name) for f in files]

        sites = {f['site'] for f in parsed_files if f['site'] is not None}
        z_planes = {f['z_plane'] for f in parsed_files if f['z_plane'] is not None}
        channels = {f['channel'] for f in parsed_files if f['channel'] is not None}
        timepoints = {f['timepoint'] for f in parsed_files if f['timepoint'] is not None}
        tiles = sites

        expected_count = max(1, len(tiles or [0])) * max(1, len(z_planes or [0])) * max(1, len(channels or [0])) * max(1, len(timepoints or [0]))

        return {
            'group_name': group_name,
            'files': [str(f) for f in files],
            'file_count': len(files),
            'expected_file_count': expected_count,
            'missing_files': expected_count - len(files),
            'completeness': len(files) / expected_count if expected_count > 0 else 0,
            'dimensions': {
                'tiles': {
                    'count': len(tiles),
                    'values': sorted(list(tiles)) if tiles else [],
                    'min': min(tiles) if tiles else None,
                    'max': max(tiles) if tiles else None
                },
                'z_planes': {
                    'count': len(z_planes),
                    'values': sorted(list(z_planes)) if z_planes else [],
                    'min': min(z_planes) if z_planes else None,
                    'max': max(z_planes) if z_planes else None
                },
                'channels': {
                    'count': len(channels) if channels else 1,
                    'values': sorted(list(channels)) if channels else [0],
                    'min': min(channels) if channels else 0,
                    'max': max(channels) if channels else 0
                },
                'timepoints': {
                    'count': len(timepoints) if timepoints else 1,
                    'values': sorted(list(timepoints)) if timepoints else [0],
                    'min': min(timepoints) if timepoints else 0,
                    'max': max(timepoints) if timepoints else 0
                }
            },
            'files': [str(f) for f in files]
        }

    def extract_all_metadata(self) -> Dict:
        """Extract metadata from all .tif/.tiff files recursively."""
        self.metadata = {
            'base_directory': str(self.base_directory),
            'folders': {},
            'extraction_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Find all .tif/.tiff files recursively
        candidate_files = []
        for pattern in ('*.tif', '*.tiff', '*.TIF', '*.TIFF'):
            candidate_files.extend(self.base_directory.rglob(pattern))

        # De-duplicate and filter hidden files
        seen_paths = set()
        tif_files = []
        for f in candidate_files:
            if f.resolve() not in seen_paths and not any(part.startswith('.') for part in f.parts):
                seen_paths.add(f.resolve())
                tif_files.append(f)

        # Group files by folder and image name
        from collections import defaultdict
        grouped_files = defaultdict(lambda: defaultdict(list))

        for tif_file in tif_files:
            folder_rel = tif_file.parent.relative_to(self.base_directory)
            parsed = self.parse_filename(tif_file.name)
            image_name = parsed['image_name']
            grouped_files[str(folder_rel)][image_name].append(tif_file)

        # Process each folder
        total_files = 0
        total_groups = 0

        for folder_rel, image_groups in grouped_files.items():
            self.metadata['folders'][folder_rel] = {
                'image_groups': {},
                'total_files': 0
            }

            for image_name, files in image_groups.items():
                analysis = self.analyze_image_group(image_name, files)
                self.metadata['folders'][folder_rel]['image_groups'][image_name] = analysis
                self.metadata['folders'][folder_rel]['total_files'] += len(files)
                total_files += len(files)
                total_groups += 1

        self.metadata['summary'] = {
            'total_files': total_files,
            'total_folders': len(grouped_files),
            'total_image_groups': total_groups
        }

        return self.metadata


def merge_channels_imagej(input_dir: Path, output_dir: Path, ui: UserInterfacePort):
    """
    Merge channel TIFF files into ImageJ-compatible composite TIFF stacks.
    Based on original merge_channels_tiff.py logic.
    """
    results = {'merged_files': [], 'errors': []}

    # Find all channel 0 files (try both ch0 and ch00 patterns)
    # Be specific to avoid confusion between ch0 and ch00
    ch00_files = sorted(input_dir.rglob("*ch00*.tif"))
    ch0_files = [f for f in sorted(input_dir.rglob("*ch0*.tif")) if 'ch00' not in f.name and 'ch01' not in f.name]

    # Use whichever pattern has files
    if ch00_files:
        channel_files = ch00_files
        ch_pattern = "ch00"
        ch_replace = "ch01"
        ui.info(f"📚 Found {len(channel_files)} ch00/ch01 channel pairs to merge")
    elif ch0_files:
        channel_files = ch0_files
        ch_pattern = "ch0"
        ch_replace = "ch1"
        ui.info(f"📚 Found {len(channel_files)} ch0/ch1 channel pairs to merge")
    else:
        ui.info("ℹ️  No channel files found")
        return results

    # Process each channel 0 file
    for ch0_file in channel_files:
        # Generate corresponding channel 1 filename
        ch1_file = Path(str(ch0_file).replace(ch_pattern, ch_replace))

        # Check if channel 1 file exists
        if not ch1_file.exists():
            ui.info(f"  ⚠️  No matching {ch_replace} file for {ch0_file.name}")
            continue

        # Generate output filename
        base_name = ch0_file.name
        output_name = re.sub(f'_{ch_pattern}', '', base_name)
        output_name = "Merged_" + output_name
        output_path = output_dir / output_name

        ui.info(f"  Merging: {ch0_file.name} + {ch1_file.name}")

        try:
            # Read both channel images using tifffile
            img_ch0 = tifffile.imread(ch0_file)
            img_ch1 = tifffile.imread(ch1_file)

            # Ensure images have the same dimensions
            if img_ch0.shape != img_ch1.shape:
                ui.error(f"    ❌ Channel dimensions don't match")
                continue

            # Determine the correct axes based on the input shape
            if len(img_ch0.shape) == 3:
                # Z-stack format: (Z, Y, X) -> merge to (C, Z, Y, X)
                merged_stack = np.stack([img_ch0, img_ch1], axis=0)
                axes = 'CZYX'
            elif len(img_ch0.shape) == 2:
                # Single image format: (Y, X) -> merge to (C, Y, X)
                merged_stack = np.stack([img_ch0, img_ch1], axis=0)
                axes = 'CYX'
            else:
                ui.error(f"    ❌ Unexpected image shape {img_ch0.shape}")
                continue

            # Create metadata dictionary for ImageJ
            metadata = {'axes': axes}

            # Save as ImageJ-compatible TIFF
            try:
                tifffile.imwrite(
                    output_path,
                    merged_stack,
                    imagej=True,
                    metadata=metadata,
                    compression='lzw'
                )
            except (KeyError, ImportError):
                # LZW compression not available, save without compression
                tifffile.imwrite(
                    output_path,
                    merged_stack,
                    imagej=True,
                    metadata=metadata
                )

            results['merged_files'].append(str(output_path))
            ui.info(f"    ✅ Created: {output_name}")

        except Exception as e:
            ui.error(f"    ❌ Error: {e}")
            results['errors'].append({'files': [str(ch0_file), str(ch1_file)], 'error': str(e)})

    return results


def create_z_stacks_structured(input_dir: Path, output_dir: Path, ui: UserInterfacePort, metadata: Dict):
    """Create Z-stacks from individual z-plane images with proper directory structure."""
    results = {'stacks_created': [], 'errors': []}

    ui.info("🔍 Processing image groups for z-stack creation...")

    for folder_rel, folder_data in metadata['folders'].items():
        # Create experiment subdirectory in z-stacks output
        if folder_rel != '.':
            exp_output_dir = output_dir / folder_rel
        else:
            exp_output_dir = output_dir
        exp_output_dir.mkdir(parents=True, exist_ok=True)

        for image_name, group_data in folder_data['image_groups'].items():
            z_planes = group_data['dimensions']['z_planes']

            if z_planes['count'] > 1:
                ui.info(f"  📚 Creating z-stack for: {image_name}")

                # Group files by channel and timepoint
                files_by_ch_t = {}
                for file_path_str in group_data['files']:
                    file_path = Path(file_path_str)
                    parsed = MicroscopyMetadataExtractor(input_dir).parse_filename(file_path.name)

                    channel = parsed['channel'] if parsed['channel'] is not None else 0
                    timepoint = parsed['timepoint'] if parsed['timepoint'] is not None else 0

                    key = (channel, timepoint)
                    if key not in files_by_ch_t:
                        files_by_ch_t[key] = []
                    files_by_ch_t[key].append((parsed['z_plane'], file_path))

                # Create z-stack for each channel/timepoint combination (like original)
                for (channel, timepoint), z_files in files_by_ch_t.items():
                    z_files.sort(key=lambda x: x[0])  # Sort by z-plane

                    try:
                        # Read all z-planes
                        z_stack = []
                        for z_plane, z_file in z_files:
                            img = tifffile.imread(z_file)
                            z_stack.append(img)

                        # Stack along z-axis
                        z_stack_array = np.stack(z_stack, axis=0)

                        # Generate output filename (like original: z-stack_name_ch0.tif)
                        output_name = f"z-stack_{image_name}_ch{channel}.tif"
                        output_path = exp_output_dir / output_name

                        # Save z-stack
                        tifffile.imwrite(output_path, z_stack_array, imagej=True)
                        results['stacks_created'].append(str(output_path))

                    except Exception as e:
                        ui.error(f"    ❌ Error creating z-stack: {e}")
                        results['errors'].append({'image_name': image_name, 'error': str(e)})

    return results


def create_max_projections_structured(input_dir: Path, output_dir: Path, ui: UserInterfacePort, metadata: Dict):
    """Create maximum intensity projections from z-stack TIFF files with proper directory structure."""
    results = {'projections_created': [], 'errors': []}

    ui.info("🔍 Creating maximum intensity projections...")

    # Process each experiment directory
    for folder_rel in metadata['folders'].keys():
        if folder_rel != '.':
            exp_z_dir = input_dir / folder_rel
            exp_max_dir = output_dir / folder_rel / 'timepoint_1'  # Like original
        else:
            exp_z_dir = input_dir
            exp_max_dir = output_dir / 'timepoint_1'

        if not exp_z_dir.exists():
            continue

        # Find all TIFF files in this experiment's z-stacks directory
        tiff_files = list(exp_z_dir.glob('*.tif')) + list(exp_z_dir.glob('*.tiff'))

        if not tiff_files:
            continue

        ui.info(f"📚 Processing {len(tiff_files)} z-stack files in {folder_rel}")

        for tiff_file in tiff_files:
            ui.info(f"  Processing: {tiff_file.name}")

            try:
                # Read the multi-page TIFF
                with tifffile.TiffFile(tiff_file) as tif:
                    images = tif.asarray()
                    n_pages = len(tif.pages)

                # Handle different array dimensions
                if len(images.shape) == 2:
                    # Single image, no z-stack
                    ui.info(f"    ⚠️  Skipping: single image, not a z-stack")
                    continue
                elif len(images.shape) == 3:
                    # Standard z-stack (Z, Y, X) - create max projection
                    max_projection = np.max(images, axis=0)
                    ui.info(f"    ✅ Max projection from {n_pages} z-planes")
                else:
                    ui.error(f"    ❌ Unexpected dimensions: {images.shape}")
                    continue

                # Create output filename (like original: MAX_z-stack_name_ch0_t00.tif)
                # Parse the z-stack filename to get proper naming
                z_name = tiff_file.name.replace('.tif', '').replace('.tiff', '')
                output_name = f"MAX_{z_name}_t00.tif"
                output_path = exp_max_dir / output_name

                # Save the maximum projection
                try:
                    tifffile.imwrite(
                        output_path,
                        max_projection,
                        imagej=True,
                        compression='lzw'
                    )
                except (KeyError, ImportError):
                    # LZW compression not available, save without compression
                    tifffile.imwrite(
                        output_path,
                        max_projection,
                        imagej=True
                    )

                results['projections_created'].append(str(output_path))
                ui.info(f"    ✅ Created: {output_name}")

            except Exception as e:
                ui.error(f"    ❌ Error: {e}")
                results['errors'].append({'file': str(tiff_file), 'error': str(e)})

    return results


def merge_channels_from_max_projections(max_proj_dir: Path, output_dir: Path, ui: UserInterfacePort, metadata: Dict):
    """Merge channels from MAX projection files (like original workflow)."""
    results = {'merged_files': [], 'errors': []}

    ui.info("🔍 Merging channels from MAX projections...")

    # Process each experiment directory
    for folder_rel in metadata['folders'].keys():
        if folder_rel != '.':
            exp_max_dir = max_proj_dir / folder_rel / 'timepoint_1'
            exp_output_dir = output_dir / folder_rel
        else:
            exp_max_dir = max_proj_dir / 'timepoint_1'
            exp_output_dir = output_dir

        if not exp_max_dir.exists():
            continue

        exp_output_dir.mkdir(parents=True, exist_ok=True)

        # Find channel 0 MAX projection files
        ch0_files = [f for f in exp_max_dir.glob("*ch0*.tif") if 'MAX_' in f.name]

        if not ch0_files:
            continue

        ui.info(f"📚 Found {len(ch0_files)} channel pairs to merge in {folder_rel}")

        for ch0_file in ch0_files:
            # Find corresponding ch1 file
            ch1_file = Path(str(ch0_file).replace("ch0", "ch1"))

            if not ch1_file.exists():
                ui.info(f"  ⚠️  No matching ch1 file for {ch0_file.name}")
                continue

            ui.info(f"  Merging: {ch0_file.name} + {ch1_file.name}")

            try:
                # Read both channel images
                img_ch0 = tifffile.imread(ch0_file)
                img_ch1 = tifffile.imread(ch1_file)

                # Ensure images have the same dimensions
                if img_ch0.shape != img_ch1.shape:
                    ui.error(f"    ❌ Channel dimensions don't match")
                    continue

                # Create merged stack (single image format: (Y, X) -> merge to (C, Y, X))
                merged_stack = np.stack([img_ch0, img_ch1], axis=0)
                axes = 'CYX'

                # Create metadata dictionary for ImageJ
                metadata_dict = {'axes': axes}

                # Generate output filename (like original: Merged_MAX_z-stack_name.tif)
                # Remove channel info and timepoint info from filename
                base_name = ch0_file.name.replace('MAX_z-stack_', '').replace('_ch0_t00.tif', '')
                output_name = f"Merged_MAX_z-stack_{base_name}.tif"
                output_path = exp_output_dir / output_name

                # Save as ImageJ-compatible TIFF
                try:
                    tifffile.imwrite(
                        output_path,
                        merged_stack,
                        imagej=True,
                        metadata=metadata_dict,
                        compression='lzw'
                    )
                except (KeyError, ImportError):
                    # LZW compression not available, save without compression
                    tifffile.imwrite(
                        output_path,
                        merged_stack,
                        imagej=True,
                        metadata=metadata_dict
                    )

                results['merged_files'].append(str(output_path))
                ui.info(f"    ✅ Created: {output_name}")

            except Exception as e:
                ui.error(f"    ❌ Error: {e}")
                results['errors'].append({'files': [str(ch0_file), str(ch1_file)], 'error': str(e)})

    return results


def run_advanced_image_processing_workflow(ui: UserInterfacePort) -> None:
    """Run the comprehensive advanced image processing workflow."""

    ui.info("🔬 Advanced Image Processing Workflow")
    ui.info("=" * 60)
    ui.info("")
    ui.info("This comprehensive workflow provides:")
    ui.info("• Metadata extraction and analysis")
    ui.info("• Maximum intensity projection for z-series")
    ui.info("• Multi-channel image merging")
    ui.info("• Tile stitching capabilities")
    ui.info("• Z-stack creation with metadata preservation")
    ui.info("")

    # Directory setup
    ui.info("📁 Directory Setup")
    ui.info("")

    input_dir = None
    while not input_dir:
        input_path = ui.prompt("Enter input directory path: ")
        input_dir = Path(input_path)
        if not input_dir.exists():
            ui.error(f"❌ Input directory does not exist: {input_path}")
            input_dir = None
        elif not input_dir.is_dir():
            ui.error(f"❌ Path is not a directory: {input_path}")
            input_dir = None

    output_dir = None
    while not output_dir:
        output_path = ui.prompt("Enter output directory path: ")
        output_dir = Path(output_path)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            break
        except Exception as e:
            ui.error(f"❌ Cannot create output directory: {e}")
            output_dir = None

    ui.info("")
    ui.info(f"✅ Input directory: {input_dir}")
    ui.info(f"✅ Output directory: {output_dir}")
    ui.info("")

    # Confirmation
    proceed = ui.prompt("Proceed with processing? (y/n): ")
    if proceed.lower() != 'y':
        ui.info("❌ Processing cancelled")
        return

    ui.info("")
    ui.info("🚀 Starting advanced image processing workflow...")
    ui.info("")

    try:
        # Step 1: Extract metadata
        ui.info("Step 1: Extracting metadata from input directory...")
        extractor = MicroscopyMetadataExtractor(input_dir)
        metadata = extractor.extract_all_metadata()

        # Save metadata
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        metadata_file = output_dir / f"microscopy_metadata_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        ui.info(f"✅ Metadata saved to: {metadata_file}")
        ui.info("📊 Summary:")
        ui.info(f"  - Total folders: {metadata['summary']['total_folders']}")
        ui.info(f"  - Total files: {metadata['summary']['total_files']}")
        ui.info(f"  - Total image groups: {metadata['summary']['total_image_groups']}")
        ui.info("")

        # Step 2: Analyze data characteristics
        ui.info("Step 2: Analyzing data characteristics...")
        has_z_series = False
        has_multichannel = False
        has_tile_scan = False
        has_time_series = False

        for folder_data in metadata['folders'].values():
            for group_data in folder_data['image_groups'].values():
                dims = group_data['dimensions']
                if dims['z_planes']['count'] > 1:
                    has_z_series = True
                if dims['channels']['count'] > 1:
                    has_multichannel = True
                if dims['tiles']['count'] > 1:
                    has_tile_scan = True
                if dims['timepoints']['count'] > 1:
                    has_time_series = True

        ui.info("  📊 Data characteristics:")
        ui.info(f"    - Z-series data: {'Yes' if has_z_series else 'No'}")
        ui.info(f"    - Multi-channel data: {'Yes' if has_multichannel else 'No'}")
        ui.info(f"    - Time-series data: {'Yes' if has_time_series else 'No'}")
        ui.info(f"    - Tile scan data: {'Yes' if has_tile_scan else 'No'}")
        ui.info("")

        # Step 3: Create processing directories based on data characteristics
        ui.info("Step 3: Setting up processing directories...")

        # Create directories only if corresponding data types are present
        processing_dirs = {}

        if has_z_series:
            processing_dirs['z_stacks'] = output_dir / 'z-stacks'
            processing_dirs['max_projections'] = output_dir / 'max_projections'

        if has_multichannel:
            processing_dirs['merged'] = output_dir / 'merged'

        if has_tile_scan:
            processing_dirs['stitched'] = output_dir / 'stitched'

        if has_time_series:
            processing_dirs['time_lapse'] = output_dir / 'time_lapse'

        # Create experiment subdirectories that mirror input structure
        if processing_dirs:
            for folder_rel in metadata['folders'].keys():
                if folder_rel != '.':  # Skip root directory
                    for proc_name, proc_dir in processing_dirs.items():
                        exp_dir = proc_dir / folder_rel
                        exp_dir.mkdir(parents=True, exist_ok=True)

                        # Create timepoint subdirectories for max_projections (like original)
                        if proc_name == 'max_projections':
                            timepoint_dir = exp_dir / 'timepoint_1'
                            timepoint_dir.mkdir(exist_ok=True)

            ui.info("✅ Processing directories created")
        else:
            ui.info("ℹ️  No processing needed - no z-series, multi-channel, tile-scan, or time-series data detected")
        ui.info("")

        total_outputs = 0

        # Step 4a: Z-series processing
        if has_z_series:
            ui.info("Step 4a: Processing Z-series data...")

            # Look for existing z-stack files first
            ui.info("🔍 Searching for z-stack files...")
            z_files = list(input_dir.rglob("*z-stack*.tif")) + list(input_dir.rglob("*zstack*.tif"))
            if z_files:
                ui.info(f"📚 Found {len(z_files)} existing z-stack files")
            else:
                ui.info("ℹ️  No z-stack files found")

            # Create z-stacks from metadata (maintaining directory structure)
            if 'z_stacks' in processing_dirs:
                z_results = create_z_stacks_structured(input_dir, processing_dirs['z_stacks'], ui, metadata)
                total_outputs += len(z_results['stacks_created'])

                # Create maximum intensity projections from z-stacks (maintaining directory structure)
                if z_results['stacks_created'] and 'max_projections' in processing_dirs:
                    ui.info("🔍 Creating maximum intensity projections from z-stacks...")
                    max_results = create_max_projections_structured(processing_dirs['z_stacks'], processing_dirs['max_projections'], ui, metadata)
                    total_outputs += len(max_results['projections_created'])
            ui.info("")

        # Step 4b: Multi-channel processing (merge MAX projections, not original files)
        if has_multichannel and 'merged' in processing_dirs:
            ui.info("Step 4b: Processing multi-channel data...")
            ui.info("🔍 Merging channels from MAX projections...")

            # Merge channels from max projections (like original workflow)
            if has_z_series and 'max_results' in locals() and 'max_projections' in processing_dirs:
                merge_results = merge_channels_from_max_projections(processing_dirs['max_projections'], processing_dirs['merged'], ui, metadata)
            else:
                # Fallback: merge from original files if no z-series
                merge_results = merge_channels_imagej(input_dir, processing_dirs['merged'], ui)

            total_outputs += len(merge_results['merged_files'])
            ui.info("")

        # Final summary
        ui.info("✅ Advanced image processing completed!")
        ui.info(f"📁 Results saved to: {output_dir}")
        ui.info("")
        ui.info("📋 Processing summary:")
        if has_z_series and 'z_results' in locals():
            ui.info(f"  - z_stacks created: {len(z_results['stacks_created'])} files")
            if 'max_results' in locals():
                ui.info(f"  - max_projections created: {len(max_results['projections_created'])} files")
        if has_multichannel and 'merge_results' in locals():
            if merge_results['errors']:
                ui.info(f"  - channel_merging errors: {len(merge_results['errors'])} files")
            else:
                ui.info(f"  - channel_merging merged: {len(merge_results['merged_files'])} files")
        ui.info(f"  - Total output files: {total_outputs}")
        ui.info("")

    except Exception as e:
        ui.error(f"Error during workflow execution: {e}")
        import traceback
        ui.error(f"Details: {traceback.format_exc()}")


def show_advanced_image_processing_plugin(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show the Advanced Image Processing plugin interface."""

    run_advanced_image_processing_workflow(ui)

    ui.prompt("Press Enter to return to main menu...")
    return args