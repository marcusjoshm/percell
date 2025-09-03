#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Group Cells by Expression Level

Thin CLI wrapper that delegates grouping to the domain layer service
`CellGroupingService`. This keeps I/O and business logic out of modules.
"""

import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger("CellGrouper")


def group_and_sum_cells(cell_dir, output_dir, num_bins, method='gmm', force_clusters=False, verbose=False):
    from percell.infrastructure.dependencies.container import Container as DIContainer, AppConfig as DIAppConfig
    from percell.domain.value_objects.file_path import FilePath as VOFilePath
    from percell.domain.services import GroupingConfig

    di = DIContainer(DIAppConfig())
    service = di.cell_grouping_service()
    cfg = GroupingConfig(bins=num_bins, force_clusters=force_clusters, channels=None)
    processed = service.process_all(
        VOFilePath.from_string(str(cell_dir)),
        VOFilePath.from_string(str(output_dir)),
        cfg,
    )
    return processed > 0


def main():
    parser = argparse.ArgumentParser(description='Group cells based on intensity')
    parser.add_argument('--cells-dir', required=True, help='Directory containing cell images')
    parser.add_argument('--output-dir', required=True, help='Directory to save grouped cells')
    parser.add_argument('--bins', type=int, default=5, help='Number of intensity bins')
    parser.add_argument('--force-clusters', action='store_true', help='Force clustering even if few cells')
    parser.add_argument('--channels', required=True, help='Channels to process (space-separated)')

    args = parser.parse_args()

    # Normalize channels
    channels = args.channels.split() if isinstance(args.channels, str) else args.channels

    from percell.infrastructure.dependencies.container import Container as DIContainer, AppConfig as DIAppConfig
    from percell.domain.value_objects.file_path import FilePath as VOFilePath
    from percell.domain.services import GroupingConfig

    di = DIContainer(DIAppConfig())
    service = di.cell_grouping_service()
    cfg = GroupingConfig(bins=args.bins, force_clusters=args.force_clusters, channels=channels)
    processed = service.process_all(
        VOFilePath.from_string(str(Path(args.cells_dir))),
        VOFilePath.from_string(str(Path(args.output_dir))),
        cfg,
    )

    if processed == 0:
        logger.error("No cell directories were successfully processed")
        return 1
    logger.info(f"Successfully processed {processed} cell directories")
    return 0


if __name__ == '__main__':
    sys.exit(main())


