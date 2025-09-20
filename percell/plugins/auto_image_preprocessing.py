#!/usr/bin/env python3
"""
Auto Image Preprocessing Plugin for Percell

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
from percell.domain.services.image_metadata_service import ImageMetadataService
from percell.domain.models import ImageMetadata

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
    metadata_service = ImageMetadataService()

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
            # Extract metadata from the first channel file
            original_metadata = metadata_service.extract_metadata(ch0_file)

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

            # Preserve original metadata and add axes info
            original_metadata.imagej_metadata['axes'] = axes

            # Save as ImageJ-compatible TIFF with preserved metadata
            success = metadata_service.save_image_with_metadata(
                merged_stack, output_path, original_metadata
            )

            if not success:
                # Fallback to basic saving
                try:
                    tifffile.imwrite(output_path, merged_stack, imagej=True,
                                   compression='lzw')
                except (KeyError, ImportError):
                    tifffile.imwrite(output_path, merged_stack, imagej=True)

            results['merged_files'].append(str(output_path))
            ui.info(f"    ✅ Created: {output_name}")

        except Exception as e:
            ui.error(f"    ❌ Error: {e}")
            results['errors'].append({'files': [str(ch0_file), str(ch1_file)], 'error': str(e)})

    return results


def create_z_stacks_structured(input_dir: Path, output_dir: Path, ui: UserInterfacePort, metadata: Dict):
    """Create Z-stacks from individual z-plane images with proper directory structure."""
    results = {'stacks_created': [], 'errors': []}
    metadata_service = ImageMetadataService()

    ui.info("🔍 Processing image groups for z-stack creation...")

    for folder_rel, folder_data in metadata['folders'].items():
        # Create experiment subdirectory in z-stacks output
        if folder_rel != '.':
            exp_output_dir = output_dir / folder_rel
            exp_input_dir = input_dir / folder_rel
        else:
            exp_output_dir = output_dir
            exp_input_dir = input_dir
        exp_output_dir.mkdir(parents=True, exist_ok=True)

        for image_name, group_data in folder_data['image_groups'].items():
            z_planes = group_data['dimensions']['z_planes']

            if z_planes['count'] > 1:
                ui.info(f"  📚 Creating z-stack for: {image_name}")

                # Find all files in the current input directory that match this image group
                # If input_dir is stitched directory, look for stitched files
                # Otherwise use original metadata files
                is_stitched_input = 'stitched' in str(input_dir).lower()

                if is_stitched_input:
                    # Find stitched files for this image group
                    pattern_files = []
                    for pattern in ('*.tif', '*.tiff'):
                        pattern_files.extend(exp_input_dir.glob(pattern))

                    # Filter to files matching this image name
                    relevant_files = []
                    for f in pattern_files:
                        if f.name.startswith(f'stitched_{image_name}'):
                            relevant_files.append(f)
                else:
                    # Use original metadata files
                    relevant_files = [Path(file_path_str) for file_path_str in group_data['files']]

                # Group files by channel and timepoint
                files_by_ch_t = {}
                for file_path in relevant_files:
                    if is_stitched_input:
                        # Parse stitched filename
                        parsed = MicroscopyMetadataExtractor(input_dir).parse_filename(file_path.name)
                    else:
                        # Use original parsing
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
                        # Extract metadata from the first z-plane file
                        first_z_file = z_files[0][1]
                        original_metadata = metadata_service.extract_metadata(first_z_file)

                        # Read all z-planes
                        z_stack = []
                        for z_plane, z_file in z_files:
                            img = tifffile.imread(z_file)
                            z_stack.append(img)

                        # Stack along z-axis
                        z_stack_array = np.stack(z_stack, axis=0)

                        # Generate output filename following original pattern
                        if is_stitched_input:
                            prefix = f"z-stack_stitched_{image_name}"
                        else:
                            prefix = f"z-stack_{image_name}"

                        output_name = f"{prefix}_ch{channel}.tif"
                        output_path = exp_output_dir / output_name

                        # Save z-stack with preserved metadata
                        success = metadata_service.save_image_with_metadata(
                            z_stack_array, output_path, original_metadata
                        )

                        if not success:
                            # Fallback to basic saving
                            tifffile.imwrite(output_path, z_stack_array, imagej=True)

                        results['stacks_created'].append(str(output_path))

                    except Exception as e:
                        ui.error(f"    ❌ Error creating z-stack: {e}")
                        results['errors'].append({'image_name': image_name, 'error': str(e)})

    return results


def create_max_projections_structured(input_dir: Path, output_dir: Path, ui: UserInterfacePort, metadata: Dict):
    """Create maximum intensity projections from z-stack TIFF files with proper directory structure."""
    results = {'projections_created': [], 'errors': []}
    metadata_service = ImageMetadataService()

    ui.info("🔍 Creating maximum intensity projections...")

    # Process each experiment directory
    for folder_rel in metadata['folders'].keys():
        if folder_rel != '.':
            exp_z_dir = input_dir / folder_rel
            exp_max_dir = output_dir / folder_rel
        else:
            exp_z_dir = input_dir
            exp_max_dir = output_dir

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
                # Extract metadata from the z-stack file
                original_metadata = metadata_service.extract_metadata(tiff_file)

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

                # Create output filename following original pattern: MAX_z-stack_stitched_name_ch0.tif
                # Parse the z-stack filename to get proper naming (remove _t00 suffix)
                z_name = tiff_file.name.replace('.tif', '').replace('.tiff', '')
                output_name = f"MAX_{z_name}.tif"
                output_path = exp_max_dir / output_name

                # Save the maximum projection with preserved metadata
                success = metadata_service.save_image_with_metadata(
                    max_projection, output_path, original_metadata
                )

                if not success:
                    # Fallback to basic saving
                    try:
                        tifffile.imwrite(output_path, max_projection, imagej=True,
                                       compression='lzw')
                    except (KeyError, ImportError):
                        tifffile.imwrite(output_path, max_projection, imagej=True)

                results['projections_created'].append(str(output_path))
                ui.info(f"    ✅ Created: {output_name}")

            except Exception as e:
                ui.error(f"    ❌ Error: {e}")
                results['errors'].append({'file': str(tiff_file), 'error': str(e)})

    return results


def create_snake_pattern(width: int, height: int) -> np.ndarray:
    """Create snake pattern for tile arrangement (row-wise serpentine)."""
    grid = np.zeros((height, width), dtype=int)
    site = 0

    for row in range(height):
        if row % 2 == 0:
            # Even rows: left to right
            for col in range(width):
                grid[row, col] = site
                site += 1
        else:
            # Odd rows: right to left
            for col in range(width - 1, -1, -1):
                grid[row, col] = site
                site += 1

    return grid


def determine_grid_dimensions(num_tiles: int, aspect_ratio_hint: Tuple[int, int] = (5, 4)) -> Tuple[int, int]:
    """Determine optimal grid dimensions based on number of tiles."""
    best_w, best_h = 1, num_tiles
    min_diff = float('inf')

    for h in range(1, num_tiles + 1):
        if num_tiles % h == 0:
            w = num_tiles // h
            current_ratio = w / h
            hint_ratio = aspect_ratio_hint[0] / aspect_ratio_hint[1]
            diff = abs(current_ratio - hint_ratio)

            if diff < min_diff:
                min_diff = diff
                best_w, best_h = w, h

    return best_w, best_h


def stitch_tiles_structured(input_dir: Path, output_dir: Path, ui: UserInterfacePort, metadata: Dict) -> Dict:
    """Stitch tile-scan images using snake pattern with user prompts for grid dimensions."""
    results = {'stitched_files': [], 'errors': []}
    metadata_service = ImageMetadataService()

    ui.info("🧩 Stitching tile-scan images...")

    # Build grid dimension prompts for each tile-scan group
    grid_dims_map = {}

    for folder_rel, folder_data in metadata['folders'].items():
        for image_name, group_data in folder_data['image_groups'].items():
            tiles_info = group_data['dimensions']['tiles']

            if tiles_info['count'] > 1:
                # Prompt user for grid dimensions for this tile-scan
                label = f"{folder_rel}/{image_name}" if folder_rel != '.' else image_name
                num_tiles = tiles_info['count']

                # Auto-detect as default
                auto_w, auto_h = determine_grid_dimensions(num_tiles)

                ui.info(f"  📏 Tile-scan detected: {label} ({num_tiles} tiles)")
                ui.info(f"     Auto-detected grid: {auto_w}x{auto_h}")

                grid_input = ui.prompt(f"Enter grid dimensions 'W H' for {label} (or press Enter for auto {auto_w}x{auto_h}): ").strip()

                if grid_input:
                    try:
                        parts = grid_input.split()
                        if len(parts) == 2:
                            w, h = int(parts[0]), int(parts[1])
                            if w * h == num_tiles:
                                grid_dims_map[f"{folder_rel}:{image_name}"] = (w, h)
                                ui.info(f"     Using custom grid: {w}x{h}")
                            else:
                                ui.info(f"     Invalid grid {w}x{h} (total={w*h}, need {num_tiles}). Using auto.")
                                grid_dims_map[f"{folder_rel}:{image_name}"] = (auto_w, auto_h)
                        else:
                            ui.info(f"     Invalid format. Using auto grid: {auto_w}x{auto_h}")
                            grid_dims_map[f"{folder_rel}:{image_name}"] = (auto_w, auto_h)
                    except ValueError:
                        ui.info(f"     Invalid input. Using auto grid: {auto_w}x{auto_h}")
                        grid_dims_map[f"{folder_rel}:{image_name}"] = (auto_w, auto_h)
                else:
                    grid_dims_map[f"{folder_rel}:{image_name}"] = (auto_w, auto_h)

    ui.info("")

    # Process stitching
    for folder_rel, folder_data in metadata['folders'].items():
        # Create experiment subdirectory in stitched output
        if folder_rel != '.':
            exp_output_dir = output_dir / folder_rel
        else:
            exp_output_dir = output_dir
        exp_output_dir.mkdir(parents=True, exist_ok=True)

        for image_name, group_data in folder_data['image_groups'].items():
            tiles_info = group_data['dimensions']['tiles']

            if tiles_info['count'] > 1:
                ui.info(f"  📚 Stitching tiles for: {image_name}")

                # Get grid dimensions
                grid_key = f"{folder_rel}:{image_name}"
                grid_w, grid_h = grid_dims_map.get(grid_key, determine_grid_dimensions(tiles_info['count']))

                ui.info(f"     Using {grid_w}x{grid_h} snake pattern grid")

                # Group files by channel, z-plane, and timepoint
                files_by_ch_z_t = {}
                for file_path_str in group_data['files']:
                    file_path = Path(file_path_str)
                    parsed = MicroscopyMetadataExtractor(input_dir).parse_filename(file_path.name)

                    channel = parsed['channel'] if parsed['channel'] is not None else 0
                    z_plane = parsed['z_plane'] if parsed['z_plane'] is not None else 0
                    timepoint = parsed['timepoint'] if parsed['timepoint'] is not None else 0
                    site = parsed['site'] if parsed['site'] is not None else 0

                    key = (channel, z_plane, timepoint)
                    if key not in files_by_ch_z_t:
                        files_by_ch_z_t[key] = []
                    files_by_ch_z_t[key].append((site, file_path))

                # Stitch each channel/z-plane/timepoint combination
                for (channel, z_plane, timepoint), tile_files in files_by_ch_z_t.items():
                    tile_files.sort(key=lambda x: x[0])  # Sort by site number

                    try:
                        # Create snake pattern grid
                        snake_grid = create_snake_pattern(grid_w, grid_h)

                        # Load tiles and arrange according to snake pattern
                        tile_dict = {}
                        first_tile_file = None
                        for site, tile_file in tile_files:
                            img = tifffile.imread(tile_file)
                            tile_dict[site] = img
                            if first_tile_file is None:
                                first_tile_file = tile_file

                        if tile_dict:
                            # Extract metadata from the first tile
                            original_metadata = metadata_service.extract_metadata(first_tile_file)

                            # Get tile dimensions
                            sample_tile = next(iter(tile_dict.values()))
                            tile_height, tile_width = sample_tile.shape[:2]

                            # Create stitched image
                            stitched_height = grid_h * tile_height
                            stitched_width = grid_w * tile_width

                            if len(sample_tile.shape) == 2:
                                stitched = np.zeros((stitched_height, stitched_width), dtype=sample_tile.dtype)
                            else:
                                stitched = np.zeros((stitched_height, stitched_width, sample_tile.shape[2]), dtype=sample_tile.dtype)

                            # Place tiles according to snake pattern
                            for row in range(grid_h):
                                for col in range(grid_w):
                                    site = snake_grid[row, col]
                                    if site in tile_dict:
                                        y_start = row * tile_height
                                        y_end = y_start + tile_height
                                        x_start = col * tile_width
                                        x_end = x_start + tile_width
                                        stitched[y_start:y_end, x_start:x_end] = tile_dict[site]

                            # Generate output filename following original convention
                            # Original pattern: stitched_A549 Control_z0_ch0.tif
                            suffix_parts = []
                            suffix_parts.append(f"z{z_plane}")
                            suffix_parts.append(f"ch{channel}")
                            if timepoint != 0:
                                suffix_parts.append(f"t{timepoint}")

                            suffix = "_" + "_".join(suffix_parts)
                            output_name = f"stitched_{image_name}{suffix}.tif"
                            output_path = exp_output_dir / output_name

                            # Save stitched image with preserved metadata
                            success = metadata_service.save_image_with_metadata(
                                stitched, output_path, original_metadata
                            )

                            if not success:
                                # Fallback to basic saving
                                tifffile.imwrite(output_path, stitched, imagej=True)

                            results['stitched_files'].append(str(output_path))
                            ui.info(f"    ✅ Created: {output_name} ({grid_w}x{grid_h} snake pattern)")

                    except Exception as e:
                        ui.error(f"    ❌ Error stitching: {e}")
                        results['errors'].append({'image_name': image_name, 'channel': channel, 'z_plane': z_plane, 'timepoint': timepoint, 'error': str(e)})

    return results


def merge_channels_from_max_projections(max_proj_dir: Path, output_dir: Path, ui: UserInterfacePort, metadata: Dict):
    """Merge channels from MAX projection files (like original workflow)."""
    results = {'merged_files': [], 'errors': []}
    metadata_service = ImageMetadataService()

    ui.info("🔍 Merging channels from MAX projections...")

    # Process each experiment directory
    for folder_rel in metadata['folders'].keys():
        if folder_rel != '.':
            exp_max_dir = max_proj_dir / folder_rel
            exp_output_dir = output_dir / folder_rel
        else:
            exp_max_dir = max_proj_dir
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
                # Extract metadata from the first channel file
                original_metadata = metadata_service.extract_metadata(ch0_file)

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

                # Preserve original metadata and add axes info
                original_metadata.imagej_metadata['axes'] = axes

                # Generate output filename following original pattern: Merged_MAX_z-stack_stitched_name.tif
                # Remove channel info from filename
                base_name = ch0_file.name.replace('MAX_z-stack_', '').replace('_ch0.tif', '')
                output_name = f"Merged_MAX_z-stack_{base_name}.tif"
                output_path = exp_output_dir / output_name

                # Save as ImageJ-compatible TIFF with preserved metadata
                success = metadata_service.save_image_with_metadata(
                    merged_stack, output_path, original_metadata
                )

                if not success:
                    # Fallback to basic saving
                    try:
                        tifffile.imwrite(output_path, merged_stack, imagej=True,
                                       compression='lzw')
                    except (KeyError, ImportError):
                        tifffile.imwrite(output_path, merged_stack, imagej=True)

                results['merged_files'].append(str(output_path))
                ui.info(f"    ✅ Created: {output_name}")

            except Exception as e:
                ui.error(f"    ❌ Error: {e}")
                results['errors'].append({'files': [str(ch0_file), str(ch1_file)], 'error': str(e)})

    return results


def run_auto_image_preprocessing_workflow(ui: UserInterfacePort) -> None:
    """Run the comprehensive auto image preprocessing workflow."""

    ui.info("🔬 Auto Image Preprocessing Workflow")
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
    ui.info("🚀 Starting auto image preprocessing workflow...")
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

                        # Create experiment subdirectories
                        pass

            ui.info("✅ Processing directories created")
        else:
            ui.info("ℹ️  No processing needed - no z-series, multi-channel, tile-scan, or time-series data detected")
        ui.info("")

        total_outputs = 0

        # Step 4: Process workflow in original order
        current_source_dir = input_dir

        # Step 4a: Tile-scan stitching (first step if tile-scan data exists)
        if has_tile_scan:
            ui.info("Step 4a: Processing tile-scan data...")
            stitch_results = stitch_tiles_structured(current_source_dir, processing_dirs['stitched'], ui, metadata)
            total_outputs += len(stitch_results['stitched_files'])
            # Update source for next step
            current_source_dir = processing_dirs['stitched']
            ui.info("")

        # Step 4b: Z-series processing (create z-stacks from stitched or original files)
        if has_z_series:
            ui.info("Step 4b: Processing Z-series data...")

            # Create z-stacks from current source (stitched files if tile-scan, otherwise original)
            if 'z_stacks' in processing_dirs:
                z_results = create_z_stacks_structured(current_source_dir, processing_dirs['z_stacks'], ui, metadata)
                total_outputs += len(z_results['stacks_created'])
                # Update source for next step
                current_source_dir = processing_dirs['z_stacks']

                # Create maximum intensity projections from z-stacks
                if z_results['stacks_created'] and 'max_projections' in processing_dirs:
                    ui.info("🔍 Creating maximum intensity projections from z-stacks...")
                    max_results = create_max_projections_structured(current_source_dir, processing_dirs['max_projections'], ui, metadata)
                    total_outputs += len(max_results['projections_created'])
                    # Update source for next step (prefer MAX projections)
                    current_source_dir = processing_dirs['max_projections']
            ui.info("")

        # Step 4c: Multi-channel processing (merge from current processing step)
        if has_multichannel and 'merged' in processing_dirs:
            ui.info("Step 4c: Processing multi-channel data...")
            ui.info("🔍 Merging channels...")

            # Merge channels from the current processing step
            if has_z_series and 'max_projections' in processing_dirs and current_source_dir == processing_dirs['max_projections']:
                # Merge from MAX projections (preferred)
                merge_results = merge_channels_from_max_projections(current_source_dir, processing_dirs['merged'], ui, metadata)
            else:
                # Merge from current source (stitched files or original files)
                merge_results = merge_channels_imagej(current_source_dir, processing_dirs['merged'], ui)

            total_outputs += len(merge_results['merged_files'])
            ui.info("")

        # Final summary
        ui.info("✅ Auto image preprocessing completed!")
        ui.info(f"📁 Results saved to: {output_dir}")
        ui.info("")
        ui.info("📋 Processing summary:")
        if has_tile_scan and 'stitch_results' in locals():
            ui.info(f"  - tile_stitching created: {len(stitch_results['stitched_files'])} files")
            if stitch_results['errors']:
                ui.info(f"  - tile_stitching errors: {len(stitch_results['errors'])} groups")
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


def show_auto_image_preprocessing_plugin(ui: UserInterfacePort, args: argparse.Namespace) -> Optional[argparse.Namespace]:
    """Show the Auto Image Preprocessing plugin interface."""

    run_auto_image_preprocessing_workflow(ui)

    ui.prompt("Press Enter to return to main menu...")
    return args