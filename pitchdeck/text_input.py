"""Parse a plain text file into a list of Slide objects.

Expected file format:

    --- Slide 1 ---
    Title Line

    Body bullet one
    Body bullet two

    Notes:
    Speaker notes here.

    --- Slide 2 ---
    ...

Rules:
- A slide block starts at '--- Slide N ---' (case-insensitive).
- The first non-empty line in a block is the title.
- Lines after a 'Notes:' label (on its own line) become speaker notes.
- All other non-empty lines between title and Notes: become body items.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pitchdeck.models import Presentation, Slide

# Matches:  --- Slide 3 ---
_SLIDE_DELIMITER = re.compile(r"^---\s*slide\s+(\d+)\s*---\s*$", re.IGNORECASE | re.MULTILINE)

# Matches a line that is just "Notes:" (case-insensitive)
_NOTES_LABEL = re.compile(r"^notes\s*:\s*$", re.IGNORECASE)


def load_text(path: Path) -> Presentation:
	"""Parse a plain text presentation file into a Presentation.

	Raises FileNotFoundError if path does not exist.
	Raises ValueError if no slide delimiters are found.
	"""
	if not path.exists():
		raise FileNotFoundError(f"Presentation file not found: {path}")
	raw_text = path.read_text(encoding="utf-8")
	slides = _parse_slides(raw_text)
	return Presentation(slides=slides, source_path=str(path.resolve()), source_format="text")


def _parse_slides(raw_text: str) -> list[Slide]:
	"""Split raw text into slide blocks and parse each one."""
	# re.split with a capturing group produces: [pre, num1, block1, num2, block2, ...]
	parts = _SLIDE_DELIMITER.split(raw_text)

	# parts[0] is text before the first delimiter (preamble); rest alternate num/block
	if len(parts) < 3:  # no delimiter found
		raise ValueError(
			"No slide delimiters found. Format each slide as '--- Slide N ---'."
		)

	preamble = parts[0].strip()
	if preamble:
		print(f"Warning: text before first slide delimiter ignored.\n", file=sys.stderr)

	# Pair up (slide_number_str, block_text)
	pairs = list(zip(parts[1::2], parts[2::2]))
	return [_parse_slide_block(block, int(num)) for num, block in pairs]


def _parse_slide_block(block: str, number: int) -> Slide:
	"""Extract title, body, and notes from a single slide text block."""
	lines = [line.rstrip() for line in block.splitlines()]

	title = ""
	body: list[str] = []
	notes_lines: list[str] = []
	in_notes = False
	title_found = False

	for line in lines:
		if not title_found:
			if line.strip():
				title = line.strip()
				title_found = True
			continue

		if _NOTES_LABEL.match(line.strip()):
			in_notes = True
			continue

		if in_notes:
			notes_lines.append(line)
		else:
			if line.strip():
				body.append(line.strip())

	notes = "\n".join(notes_lines).strip()
	return Slide(number=number, title=title, body=body, notes=notes)
