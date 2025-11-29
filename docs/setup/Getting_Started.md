# Getting Started

This guide gets you productive fast with PerCell.

## Install

```bash
git clone https://github.com/marcusjoshm/percell.git
cd percell
./install
```

## Run

```bash
# From any directory
percell

# Help and common options
percell --help
percell --interactive
percell --input /path/to/data --output /path/to/output --complete-workflow
```

## Data layout

```
input_directory/
├── condition_1/
│   ├── timepoint_1/
│   │   └── region_1/ ... channel_1.tif, channel_2.tif, ...
│   └── timepoint_2/
└── condition_2/
```

## Recommended path

1. Choose "Run Complete Workflow" in the interactive menu
2. Follow prompts for data selection
3. Complete segmentation step when prompted

## Troubleshooting

- If command not found: re-run `./install`
- If permission errors: ensure `/usr/local/bin` is writable

## Next steps

- Architecture overview: see `docs/Architecture.md`
- Centralized paths: see `docs/CENTRALIZED_PATHS.md`

