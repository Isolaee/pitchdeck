"""Load and validate the user profile from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_profile(path: Path) -> dict[str, Any]:
    """Read user_profile.yaml and return the parsed dict.

    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if required top-level keys are missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Profile file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _validate_profile(data)
    return data


def _validate_profile(data: dict[str, Any]) -> None:
    """Check that required sections are present in the profile."""
    required = {"contact", "skills", "work_history"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Profile is missing required sections: {missing}")
