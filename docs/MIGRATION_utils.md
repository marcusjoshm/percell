# Migration Report: core/utils.py → Ports and Adapters

This document explains how we migrated `percell/core/utils.py` into the hexagonal architecture (ports and adapters), validated via tests, and then safely removed the legacy file.

## 1) Responsibilities in utils.py (Before)
- Package root discovery: `get_package_root()`, `find_package_root_from_script()`
- Package resource access: `get_package_resource()`, `get_bash_script()`, `get_config_file()`, `get_macro_file()`
- Filesystem permission: `ensure_executable(Path)`

## 2) Target Architecture Mapping (After)
- Domain (pure logic):
  - `percell/domain/services/package_resource_service.py`
    - `verify_root()` checks expected directories under a given package root
    - `resource(relative_path)`, `bash(name)`, `config(name)`, `macro(name)` resolve resources and raise if missing
- Driven Port + Adapter (I/O concerns):
  - Port: `percell/ports/driven/file_management_port.py`
    - Added `ensure_executable(path: Path) -> None`
  - Adapter: `percell/adapters/local_filesystem_adapter.py`
    - Implemented `ensure_executable` (chmod 0o755), plus existing `list_files`, `copy`, `move`, `ensure_dir`
- Centralized Paths (existing):
  - `percell/core/paths.py` remains the authority for named paths (scripts, macros, etc.) via `get_path(...)`

## 3) Test-Driven Migration
- Legacy parity tests (pre-deletion): `tests/migration/test_core_utils_migration.py`
  - Validates package root, resource access, error on missing resource, and chmod behavior
- New domain tests: `tests/unit/domain/test_package_resource_service.py`
  - Verifies `verify_root()`, accessors for bash/config/macro, and error on missing resource

## 4) Incremental Code Changes
- Added: `percell/domain/services/package_resource_service.py` (pure path logic & validation)
- Updated port/adapter: added `ensure_executable` to the file management port and implemented in `LocalFileSystemAdapter`
- Replaced remaining chmod calls:
  - `percell/modules/stage_classes.py` now uses `LocalFileSystemAdapter().ensure_executable(get_path(...))`
- Decoupled core API from utils:
  - Removed utils re-exports from `percell/core/__init__.py`

## 5) Safe Deletion Procedure
1. Confirmed no app modules import `percell.core.utils` (repo-wide search)
2. Adjusted the migration test to skip when utils is removed
3. Ran the full test suite; deleted `percell/core/utils.py`
4. Result: all tests passed (migration test skipped), no regressions

## 6) Validation Checklist (All Satisfied)
- [x] Business logic moved to domain service (`PackageResourceService`)
- [x] I/O moved to adapter/port (`ensure_executable`)
- [x] No domain dependencies on frameworks
- [x] No code still imports `percell.core.utils`
- [x] Tests for legacy parity and new services added/passing
- [x] Safe deletion executed with tests green

## 7) Notes for Callers Going Forward
- Prefer `percell/core/paths.py` for named paths: `get_path('…')`, `get_path_config()`
- Use `PackageResourceService` for domain-level resource derivation relative to a root
- Use `LocalFileSystemAdapter.ensure_executable(Path)` for chmod semantics
