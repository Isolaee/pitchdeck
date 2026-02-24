"""CLI entry point for the pitchdeck agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from pitchdeck.llm import DEFAULT_MODEL
from pitchdeck.loader import load_presentation
from pitchdeck.metadata import load_metadata

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_METADATA = _REPO_ROOT / "data" / "metadata.yaml"
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "output"


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Generate a pitchdeck voiceover script using a local LLM via Ollama."
	)
	parser.add_argument(
		"--input",
		type=Path,
		required=True,
		metavar="PATH",
		help="Path to a .pptx or .txt presentation file",
	)
	parser.add_argument(
		"--metadata",
		type=Path,
		default=_DEFAULT_METADATA,
		metavar="PATH",
		help="Path to metadata.yaml (default: data/metadata.yaml)",
	)
	parser.add_argument(
		"--model",
		default=DEFAULT_MODEL,
		help=f"Ollama model name (default: {DEFAULT_MODEL})",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=None,
		metavar="PATH",
		help="Output file path for generated script (auto-named if omitted)",
	)
	args = parser.parse_args()

	presentation = load_presentation(args.input)
	metadata = load_metadata(args.metadata)
	presentation.metadata = metadata

	# Prompt building and LLM call are implemented in a later phase.
	print(f"Loaded {len(presentation.slides)} slides from '{args.input.name}'")
	print(f"Title: {metadata.get('title')}  |  Author: {metadata.get('author')}")
	for slide in presentation.slides:
		body_preview = f" — {slide.body[0][:60]}..." if slide.body else ""
		print(f"  Slide {slide.number}: {slide.title or '(no title)'}{body_preview}")


if __name__ == "__main__":
	main()
