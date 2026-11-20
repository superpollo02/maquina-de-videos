"""Shared pytest fixtures and path discovery helpers for EducAI + OpenMontage E2E tests."""

import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHROME_EXECUTABLE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def find_openmontage_root() -> Path | None:
    """Locate integrated OpenMontage directory (repo root, openmontage/, or vendor/openmontage/)."""
    candidates = [
        REPO_ROOT,
        REPO_ROOT / "openmontage",
        REPO_ROOT / "vendor" / "openmontage",
    ]
    for cand in candidates:
        if (cand / "tools" / "tool_registry.py").is_file() and (cand / "lib").is_dir():
            return cand
    return None


def ensure_openmontage_on_path() -> Path:
    """Resolve OpenMontage root and add to sys.path, failing loudly if absent."""
    root = find_openmontage_root()
    if root is None:
        raise AssertionError(
            "OpenMontage is not integrated yet (expected tools/tool_registry.py + lib/ "
            "under repo root, openmontage/, or vendor/openmontage/)."
        )
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


# Add OpenMontage to sys.path early if already present
_om_root = find_openmontage_root()
if _om_root is not None and str(_om_root) not in sys.path:
    sys.path.insert(0, str(_om_root))


try:
    import pytest  # type: ignore

    @pytest.fixture
    def repo_root() -> Path:
        return REPO_ROOT

    @pytest.fixture
    def temp_workspace():
        with tempfile.TemporaryDirectory(prefix="educai_e2e_") as tmp:
            yield Path(tmp)

except ImportError:
    # pytest is optional in baseline before M2 installs it
    pass
