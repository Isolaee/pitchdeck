"""Core data models for pitchdeck."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Slide:
	"""Represents a single presentation slide."""

	number: int
	title: str
	body: list[str]
	notes: str


@dataclass
class Presentation:
	"""Unified representation of a loaded presentation regardless of source format."""

	slides: list[Slide]
	source_path: str
	source_format: str  # "pptx" | "text"
	metadata: dict[str, object] = field(default_factory=dict)
