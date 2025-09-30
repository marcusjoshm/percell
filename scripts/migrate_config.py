#!/usr/bin/env python3
"""
Automated migration script for updating from Config to ConfigurationService.

This script helps automate the migration from the legacy config_api.Config
to the new domain.services.configuration_service.ConfigurationService.

Usage:
    python scripts/migrate_config.py [--dry-run] [--file FILE] [--all]

Options:
    --dry-run    Show what would be changed without modifying files
    --file FILE  Migrate a specific file
    --all        Migrate all files in the project
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import argparse


class ConfigMigrationTool:
    """Tool to help migrate from old Config to new ConfigurationService."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.changes_made = 0
        self.files_modified = 0

    def migrate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Migrate a single file from old config API to new.

        Returns:
            Tuple of (was_modified, list_of_changes)
        """
        if not file_path.exists():
            return False, [f"File not found: {file_path}"]

        content = file_path.read_text(encoding='utf-8')
        original_content = content
        changes = []

        # Step 1: Update imports
        content, import_changes = self._update_imports(content, file_path.name)
        changes.extend(import_changes)

        # Step 2: Update Config() instantiations
        content, init_changes = self._update_instantiations(content)
        changes.extend(init_changes)

        # Step 3: Update exception handling
        content, exception_changes = self._update_exceptions(content)
        changes.extend(exception_changes)

        # Step 4: Update create_default_config calls
        content, default_changes = self._update_default_config(content)
        changes.extend(default_changes)

        # Check if anything changed
        if content != original_content:
            if not self.dry_run:
                file_path.write_text(content, encoding='utf-8')
                self.files_modified += 1
            self.changes_made += len(changes)
            return True, changes

        return False, changes

    def _update_imports(self, content: str, filename: str) -> Tuple[str, List[str]]:
        """Update import statements."""
        changes = []

        # Pattern 1: Import Config, ConfigError
        old_pattern = r'from percell\.application\.config_api import ([^\n]+)'

        def replace_import(match):
            imports = match.group(1)

            # Parse what's being imported
            has_config = 'Config' in imports and 'ConfigError' not in imports.replace('Config', '', 1)
            has_config_error = 'ConfigError' in imports
            has_create_default = 'create_default_config' in imports

            new_imports = []

            if has_config:
                new_imports.append(
                    "from percell.domain.services.configuration_service import (\n"
                    "    ConfigurationService,\n"
                    "    create_configuration_service\n"
                    ")"
                )
                changes.append(f"  Updated Config import to ConfigurationService")

            if has_config_error:
                new_imports.append(
                    "from percell.domain.exceptions import ConfigurationError"
                )
                changes.append(f"  Updated ConfigError import to ConfigurationError")

            if has_create_default:
                changes.append(
                    f"  Note: create_default_config removed - implement manually (see migration guide)"
                )

            if new_imports:
                return "\n".join(new_imports)
            return match.group(0)

        content = re.sub(old_pattern, replace_import, content)

        # Pattern 2: Import from configuration_manager (should not exist, but check)
        if 'from percell.application.configuration_manager import' in content:
            content = content.replace(
                'from percell.application.configuration_manager import ConfigurationManager',
                'from percell.domain.services.configuration_service import ConfigurationService'
            )
            changes.append("  Replaced ConfigurationManager import")

        return content, changes

    def _update_instantiations(self, content: str) -> Tuple[str, List[str]]:
        """Update Config() instantiations to create_configuration_service()."""
        changes = []

        # Pattern: Config(path)
        pattern = r'Config\((["\'][^"\']+["\'])\)'

        def replace_init(match):
            path = match.group(1)
            changes.append(f"  Replaced Config({path}) with create_configuration_service()")
            return f'create_configuration_service({path}, create_if_missing=True)'

        content = re.sub(pattern, replace_init, content)

        # Pattern: ConfigurationManager(path)
        pattern2 = r'ConfigurationManager\(([^)]+)\)'

        def replace_manager(match):
            args = match.group(1)
            changes.append(f"  Replaced ConfigurationManager({args}) with ConfigurationService()")
            return f'ConfigurationService(path={args})'

        content = re.sub(pattern2, replace_manager, content)

        return content, changes

    def _update_exceptions(self, content: str) -> Tuple[str, List[str]]:
        """Update ConfigError to ConfigurationError."""
        changes = []

        if 'ConfigError' in content and 'ConfigurationError' not in content:
            # Replace exception name
            content = content.replace('ConfigError', 'ConfigurationError')
            changes.append("  Replaced ConfigError with ConfigurationError")

        return content, changes

    def _update_default_config(self, content: str) -> Tuple[str, List[str]]:
        """Handle create_default_config calls."""
        changes = []

        if 'create_default_config(' in content:
            changes.append(
                "  WARNING: create_default_config() usage found - needs manual migration"
            )
            changes.append(
                "    See migration guide: docs/CONFIGURATION_MIGRATION_GUIDE.md"
            )

        return content, changes

    def find_files_to_migrate(self, root: Path) -> List[Path]:
        """Find all Python files that import from config_api."""
        files = []

        for py_file in root.rglob("*.py"):
            # Skip migration script itself and test files
            if py_file.name == 'migrate_config.py':
                continue
            if 'venv' in str(py_file) or 'cellpose_venv' in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                if 'config_api' in content or 'configuration_manager' in content:
                    files.append(py_file)
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")

        return files


def main():
    parser = argparse.ArgumentParser(
        description='Migrate from Config to ConfigurationService'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Migrate a specific file'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Migrate all files in the project'
    )

    args = parser.parse_args()

    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Initialize migration tool
    tool = ConfigMigrationTool(dry_run=args.dry_run)

    print("=" * 80)
    print("Configuration Migration Tool")
    print("=" * 80)
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print()

    # Determine which files to process
    if args.file:
        files = [Path(args.file)]
    elif args.all:
        print("🔍 Scanning project for files to migrate...")
        files = tool.find_files_to_migrate(project_root / "percell")
        print(f"Found {len(files)} files that may need migration")
        print()
    else:
        print("Error: Specify --file FILE or --all")
        parser.print_help()
        return 1

    # Process files
    for file_path in files:
        print(f"📄 Processing: {file_path.relative_to(project_root)}")

        modified, changes = tool.migrate_file(file_path)

        if modified:
            print(f"  ✅ Modified")
            for change in changes:
                print(change)
        else:
            if changes:
                for change in changes:
                    print(change)
            else:
                print(f"  ℹ️  No changes needed")
        print()

    # Summary
    print("=" * 80)
    print("Migration Summary")
    print("=" * 80)
    print(f"Files processed: {len(files)}")
    print(f"Files modified: {tool.files_modified}")
    print(f"Total changes: {tool.changes_made}")

    if args.dry_run:
        print()
        print("This was a dry run. Run without --dry-run to apply changes.")
    else:
        print()
        print("✅ Migration complete!")
        print()
        print("Next steps:")
        print("1. Review the changes: git diff")
        print("2. Run tests: pytest")
        print("3. Check for manual migrations needed (see warnings above)")
        print("4. Read: docs/CONFIGURATION_MIGRATION_GUIDE.md")

    return 0


if __name__ == '__main__':
    sys.exit(main())
