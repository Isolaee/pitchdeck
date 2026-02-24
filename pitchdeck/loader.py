"""Detect input file type and dispatch to the appropriate loader."""

from __future__ import annotations

from pathlib import Path

from pitchdeck.models import Presentation

_SUPPORTED_FORMATS: dict[str, str] = {
	".pptx": "pptx",
	".txt": "text",
}


def load_presentation(path: Path) -> Presentation:
	"""Load a presentation from a .pptx or .txt file.

	Detects format by file extension (case-insensitive).
	Raises ValueError for unsupported extensions.
	Raises FileNotFoundError if path does not exist.
	"""
	fmt = _detect_format(path)
	if fmt == "pptx":
		from pitchdeck.pptx_input import load_pptx
		return load_pptx(path)
	else:
		from pitchdeck.text_input import load_text
		return load_text(path)


def _detect_format(path: Path) -> str:
	"""Return 'pptx' or 'text' based on file suffix.

	Raises ValueError for unrecognised suffixes.
	"""
	suffix = path.suffix.lower()
	if suffix not in _SUPPORTED_FORMATS:
		supported = ", ".join(_SUPPORTED_FORMATS)
		raise ValueError(
			f"Unsupported file type '{suffix}'. Supported extensions: {supported}"
		)
	return _SUPPORTED_FORMATS[suffix]
