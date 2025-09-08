from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("import-linter") is None, reason="import-linter not installed in environment")
def test_import_linter_contracts_pass():
    """Run import-linter and assert that architecture contracts pass.

    Uses the repo-root .importlinter config. Fails with stdout/stderr when a
    contract is violated so the CI logs are helpful.
    """
    repo_root = Path(__file__).resolve().parents[1]
    cfg = repo_root / ".importlinter"
    assert cfg.exists(), ".importlinter configuration file not found at repo root"

    result = subprocess.run(
        ["import-linter", "--config", str(cfg)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("\n==== import-linter stdout ====\n" + (result.stdout or ""))
        print("\n==== import-linter stderr ====\n" + (result.stderr or ""))
    assert result.returncode == 0, "Import-linter contracts failed. See logs above."


