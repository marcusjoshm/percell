from __future__ import annotations

from typing import Dict, Any


class CleanupService:
    """Service wrapper around cleanup helpers for consistency with DI.

    Uses the in-process functions provided by percell.modules.cleanup_directories.
    """

    def scan(self, output_dir: str,
             include_cells: bool = True,
             include_masks: bool = True,
             include_combined_masks: bool = False,
             include_grouped_cells: bool = False,
             include_grouped_masks: bool = False) -> Dict[str, Dict[str, Any]]:
        from percell.modules.cleanup_directories import scan_cleanup_directories
        return scan_cleanup_directories(
            output_dir,
            include_cells=include_cells,
            include_masks=include_masks,
            include_combined_masks=include_combined_masks,
            include_grouped_cells=include_grouped_cells,
            include_grouped_masks=include_grouped_masks,
        )

    def cleanup(self, output_dir: str,
                delete_cells: bool = True,
                delete_masks: bool = True,
                delete_combined_masks: bool = False,
                delete_grouped_cells: bool = False,
                delete_grouped_masks: bool = False,
                dry_run: bool = False,
                force: bool = True) -> tuple[int, int]:
        from percell.modules.cleanup_directories import cleanup_directories
        return cleanup_directories(
            output_dir,
            delete_cells=delete_cells,
            delete_masks=delete_masks,
            delete_combined_masks=delete_combined_masks,
            delete_grouped_cells=delete_grouped_cells,
            delete_grouped_masks=delete_grouped_masks,
            dry_run=dry_run,
            force=force,
        )


__all__ = ["CleanupService"]


