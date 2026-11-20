"""Environment configuration and ToolRegistry discovery for OpenMontage in EducAI."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VENDOR_OPENMONTAGE = _REPO_ROOT / "vendor" / "openmontage"


def ensure_openmontage_env() -> Path:
    """Configure system path and environment variables for OpenMontage tools."""
    if not _VENDOR_OPENMONTAGE.is_dir():
        raise RuntimeError(
            f"OpenMontage vendor directory not found at {_VENDOR_OPENMONTAGE}. "
            "Please ensure vendor/openmontage is populated."
        )

    vendor_str = str(_VENDOR_OPENMONTAGE)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)

    repo_str = str(_REPO_ROOT)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("OPENMONTAGE_PROJECTS_DIR", str(_REPO_ROOT / "films"))
    os.environ.setdefault("OPENMONTAGE_ASSET_CACHE", "1")

    return _VENDOR_OPENMONTAGE


def get_registry() -> Any:
    """Retrieve the global ToolRegistry discovered and ready for execution."""
    ensure_openmontage_env()
    from tools.tool_registry import ToolRegistry

    registry = ToolRegistry()
    registry.ensure_discovered()
    return registry
