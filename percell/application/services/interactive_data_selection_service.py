#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Data Selection Service.

This service mirrors the legacy DataSelectionStage interactive behavior:
- Sets up output directory structure (bash script)
- Prepares input structure (bash script)
- Extracts experiment metadata from input directory
- Runs interactive prompts to select datatype/conditions/timepoints/regions/channels
- Saves selections to configuration
- Copies selected files into output/raw_data structure
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

from percell.domain.ports import (
    FileSystemPort,
    LoggingPort,
    SubprocessPort,
    ConfigurationPort,
)


class InteractiveDataSelectionService:
    def __init__(
        self,
        filesystem_port: FileSystemPort,
        logging_port: LoggingPort,
        subprocess_port: SubprocessPort,
        configuration_port: ConfigurationPort,
    ) -> None:
        self.filesystem_port = filesystem_port
        self.logging_port = logging_port
        self.subprocess_port = subprocess_port
        self.configuration_port = configuration_port
        self.logger = logging_port.get_logger("InteractiveDataSelectionService")

    def execute(
        self,
        *,
        input_dir: str,
        output_dir: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            self.logger.info("[InteractiveDataSelectionService] Starting interactive data selection...")
            self.logger.info(f"[InteractiveDataSelectionService] Input directory: {input_dir}")
            self.logger.info(f"[InteractiveDataSelectionService] Output directory: {output_dir}")

            if not self._setup_output_structure(output_dir):
                return {"success": False, "error": "Failed to setup output directory structure"}

            if not self._prepare_input_structure(input_dir):
                return {"success": False, "error": "Failed to prepare input directory structure"}

            metadata = self._extract_experiment_metadata(input_dir)
            if not metadata:
                return {"success": False, "error": "Failed to extract experiment metadata"}

            selections = self._run_interactive_selection(metadata)
            if not selections:
                return {"success": False, "error": "Data selection cancelled or invalid"}

            self._save_selections_to_config(selections, metadata)

            if not self._copy_selected_files(input_dir, output_dir, selections, metadata):
                return {"success": False, "error": "Failed to copy selected files"}

            self.logger.info("[InteractiveDataSelectionService] Data selection completed successfully")
            return {
                "success": True,
                "message": "Interactive data selection completed",
                "metadata": metadata,
                "selections": selections,
                "input_dir": input_dir,
                "output_dir": output_dir,
            }
        except Exception as e:
            self.logger.error(f"[InteractiveDataSelectionService] Error: {e}")
            return {"success": False, "error": str(e)}

    # --- Scripts ---
    def _setup_output_structure(self, output_dir: str) -> bool:
        try:
            from percell.infrastructure.filesystem.paths import get_path, ensure_executable
            script_path = get_path("setup_output_structure_script")
            ensure_executable("setup_output_structure_script")
            result = self.subprocess_port.run_with_progress(
                [str(script_path), str(output_dir)],
                title="Setup Output Structure",
            )
            if result != 0:
                self.logger.error("setup_output_structure.sh returned non-zero exit code")
                return False
            self.logger.info("[InteractiveDataSelectionService] Output directory structure setup complete")
            return True
        except Exception as e:
            self.logger.error(f"Error setting up output structure: {e}")
            return False

    def _prepare_input_structure(self, input_dir: str) -> bool:
        try:
            from percell.infrastructure.filesystem.paths import get_path, ensure_executable
            script_path = get_path("prepare_input_structure_script")
            ensure_executable("prepare_input_structure_script")
            result = self.subprocess_port.run_with_progress(
                [str(script_path), str(input_dir)],
                title="Prepare Input Structure",
            )
            if result != 0:
                self.logger.error("prepare_input_structure.sh returned non-zero exit code")
                return False
            self.logger.info("[InteractiveDataSelectionService] Input directory structure prepared successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error preparing input structure: {e}")
            return False

    # --- Metadata ---
    def _extract_experiment_metadata(self, input_dir: str) -> Optional[Dict[str, Any]]:
        try:
            input_path = Path(input_dir)
            if not input_path.exists():
                self.logger.error(f"Input directory does not exist: {input_dir}")
                return None

            metadata: Dict[str, Any] = {
                "conditions": [],
                "regions": set(),
                "timepoints": set(),
                "channels": set(),
                "directory_timepoints": set(),
                "datatype_inferred": "multi_timepoint",
            }

            for condition_dir in [p for p in input_path.iterdir() if p.is_dir() and not p.name.startswith('.')]:
                metadata["conditions"].append(condition_dir.name)
                tifs_direct = list(condition_dir.glob("*.tif"))
                if not tifs_direct:
                    for sub in [d for d in condition_dir.iterdir() if d.is_dir()]:
                        tifs = list(sub.glob("*.tif"))
                        if tifs:
                            if sub.name.startswith("timepoint_") or re.match(r"t\d+", sub.name or ""):
                                metadata["directory_timepoints"].add(sub.name)
                            for tif in tifs:
                                self._accumulate_file_metadata(tif.name, metadata)
                else:
                    for tif in tifs_direct:
                        self._accumulate_file_metadata(tif.name, metadata)

            # finalize
            metadata["regions"] = sorted(list(metadata["regions"]))
            metadata["timepoints"] = sorted(list(metadata["timepoints"]))
            metadata["channels"] = sorted(list(metadata["channels"]))
            metadata["directory_timepoints"] = sorted(list(metadata["directory_timepoints"]))
            metadata["datatype_inferred"] = (
                "single_timepoint" if len(metadata["timepoints"]) <= 1 else "multi_timepoint"
            )

            self.logger.info(f"[InteractiveDataSelectionService] Extracted metadata: {metadata}")
            return metadata
        except Exception as e:
            self.logger.error(f"Error extracting experiment metadata: {e}")
            return None

    def _accumulate_file_metadata(self, filename: str, metadata: Dict[str, Any]) -> None:
        # timepoint
        m_t = re.search(r"t(\d+)", filename)
        if m_t:
            metadata["timepoints"].add(f"t{m_t.group(1)}")
        # channel
        m_c = re.search(r"ch(\d+)", filename)
        if m_c:
            metadata["channels"].add(f"ch{m_c.group(1)}")
        # region
        temp = re.sub(r"(ch\d+|t\d+)", "", filename)
        temp = os.path.splitext(temp)[0]
        region = re.sub(r"_+", "_", temp).strip("_")
        if region:
            metadata["regions"].add(region)

    # --- Interactive selection ---
    def _run_interactive_selection(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            selected_datatype = self._prompt_single(
                title="select_datatype",
                prompt="Select the type of data: single_timepoint or multi_timepoint.",
                items=["single_timepoint", "multi_timepoint"],
                default=metadata.get("datatype_inferred", "single_timepoint"),
            )
            selected_conditions = self._prompt_list(
                title="select_condition",
                label="conditions",
                items=metadata.get("conditions", []),
            )
            selected_timepoints = self._prompt_list(
                title="select_timepoints",
                label="timepoints",
                items=metadata.get("timepoints", []),
            )
            # Regions available across selected conditions (assume common)
            selected_regions = self._prompt_list(
                title="select_regions",
                label="regions",
                items=metadata.get("regions", []),
            )
            segmentation_channel = self._prompt_single(
                title="select_segmentation_channel",
                prompt="Select the channel to use for cell segmentation.",
                items=metadata.get("channels", []),
                default=(metadata.get("channels", [None])[0] if metadata.get("channels") else None),
            )
            analysis_channels = self._prompt_list(
                title="select_analysis_channels",
                label="analysis channels",
                items=metadata.get("channels", []),
            )

            selections = {
                "datatype": selected_datatype,
                "conditions": selected_conditions,
                "timepoints": selected_timepoints,
                "regions": selected_regions,
                "segmentation_channel": segmentation_channel or "ch01",
                "analysis_channels": analysis_channels or ([segmentation_channel] if segmentation_channel else []),
            }
            self.logger.info(f"[InteractiveDataSelectionService] Selections: {selections}")
            return selections
        except Exception as e:
            self.logger.error(f"Error in interactive selection: {e}")
            return None

    def _prompt_single(self, *, title: str, prompt: str, items: List[str], default: Optional[str] = None) -> Optional[str]:
        print("\n" + "=" * 80)
        print(f"MANUAL STEP REQUIRED: {title}")
        print("=" * 80)
        if default:
            print(f"Detected default: {default}")
        for i, item in enumerate(items, 1):
            print(f"{i}. {item}")
        choice = input("Enter selection (number or name, press Enter for default): ").strip()
        if not choice and default:
            return default
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(items):
                return items[idx - 1]
        if choice in items:
            return choice
        return default if default in items else (items[0] if items else None)

    def _prompt_list(self, *, title: str, label: str, items: List[str]) -> List[str]:
        print("\n" + "=" * 80)
        print(f"MANUAL STEP REQUIRED: {title}")
        print("=" * 80)
        if not items:
            return []
        print(f"Available {label}s:")
        for i, item in enumerate(items, 1):
            print(f"{i}. {item}")
        print(f"\nInput options for {label}s:")
        print(f"- Enter {label}s as space-separated text")
        print(f"- Enter numbers from the list (e.g., '1 2')")
        print(f"- Type 'all' to select all {label}s")
        while True:
            selection = input("\nEnter your selection: ").strip()
            if selection.lower() == "all":
                return items
            try:
                indices = [int(x) for x in selection.split()]
                if all(1 <= i <= len(items) for i in indices):
                    return [items[i - 1] for i in indices]
            except ValueError:
                pass
            names = [x for x in selection.split() if x in items]
            if names:
                return names
            print("Invalid selection. Please try again.")

    # --- Save selections ---
    def _save_selections_to_config(self, selections: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        try:
            cfg = self.configuration_port.get_config()
            if hasattr(cfg, "set"):
                cfg.set("data_selection.selected_datatype", selections.get("datatype"))
                cfg.set("data_selection.selected_conditions", selections.get("conditions", []))
                cfg.set("data_selection.selected_timepoints", selections.get("timepoints", []))
                cfg.set("data_selection.selected_regions", selections.get("regions", []))
                cfg.set("data_selection.segmentation_channel", selections.get("segmentation_channel"))
                cfg.set("data_selection.analysis_channels", selections.get("analysis_channels", []))
                cfg.set("data_selection.experiment_metadata", metadata)
                if hasattr(cfg, "save"):
                    cfg.save()
            self.logger.info("[InteractiveDataSelectionService] Data selections saved to configuration")
        except Exception as e:
            self.logger.error(f"Error saving selections to config: {e}")

    # --- Copy files ---
    def _copy_selected_files(
        self,
        input_dir: str,
        output_dir: str,
        selections: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> bool:
        try:
            input_path = Path(input_dir)
            raw_data_dir = Path(output_dir) / "raw_data"
            raw_data_dir.mkdir(parents=True, exist_ok=True)

            selected_conditions = selections.get("conditions", [])
            selected_timepoints = selections.get("timepoints", [])
            selected_regions = selections.get("regions", [])
            directory_timepoints = metadata.get("directory_timepoints", [])

            total_copied = 0
            for condition in selected_conditions:
                cond_in = input_path / condition
                cond_out = raw_data_dir / condition
                cond_out.mkdir(parents=True, exist_ok=True)

                # timepoint mapping: t00 -> timepoint_1, etc.
                for tp in selected_timepoints:
                    tp_num = tp.replace("t", "")
                    try:
                        tp_dirname = f"timepoint_{int(tp_num) + 1}"
                    except ValueError:
                        tp_dirname = tp
                    if tp_dirname not in directory_timepoints:
                        self.logger.warning(f"No directory timepoint found for {tp}")
                        continue
                    tp_in = cond_in / tp_dirname
                    tp_out = cond_out / tp_dirname
                    tp_out.mkdir(parents=True, exist_ok=True)

                    tif_files = list(tp_in.glob("*.tif"))
                    # filter by regions
                    filtered = []
                    for tif in tif_files:
                        if not selected_regions:
                            filtered.append(tif)
                        else:
                            name = tif.stem
                            if any(r in name for r in selected_regions):
                                filtered.append(tif)
                    for tif in filtered:
                        dst = tp_out / tif.name
                        if dst.exists():
                            total_copied += 1
                            continue
                        shutil.copy2(tif, dst)
                        total_copied += 1

            self.logger.info(f"[InteractiveDataSelectionService] File copy completed. Total files copied: {total_copied}")
            return True
        except Exception as e:
            self.logger.error(f"Error copying selected files: {e}")
            return False



