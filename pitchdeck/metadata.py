"""Load and validate the presentation metadata YAML file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_REQUIRED_FIELDS: frozenset[str] = frozenset({"title", "author"})


def load_metadata(path: Path) -> dict[str, Any]:
	"""Read a metadata YAML file and return the parsed dict.

	Raises FileNotFoundError if the file does not exist.
	Raises ValueError if required fields are missing.
	"""
	if not path.exists():
		raise FileNotFoundError(f"Metadata file not found: {path}")
	with path.open(encoding="utf-8") as f:
		data = yaml.safe_load(f) or {}
	_validate_metadata(data)
	return data


def _validate_metadata(data: dict[str, Any]) -> None:
	"""Check that required top-level keys are present."""
	missing = _REQUIRED_FIELDS - data.keys()
	if missing:
		raise ValueError(f"Metadata is missing required fields: {', '.join(sorted(missing))}")
