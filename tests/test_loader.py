"""Tests for pitchdeck.loader — input dispatch by file extension."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pitchdeck.loader import _detect_format, load_presentation
from pitchdeck.models import Presentation, Slide


def _fake_presentation(fmt: str) -> Presentation:
	return Presentation(slides=[Slide(1, "T", [], "")], source_path="/fake", source_format=fmt)


class TestDetectFormat:
	def test_pptx_extension(self):
		assert _detect_format(Path("deck.pptx")) == "pptx"

	def test_txt_extension(self):
		assert _detect_format(Path("notes.txt")) == "text"

	def test_unsupported_extension_raises(self):
		with pytest.raises(ValueError, match="Unsupported"):
			_detect_format(Path("slides.pdf"))

	def test_case_insensitive_pptx(self):
		assert _detect_format(Path("DECK.PPTX")) == "pptx"

	def test_case_insensitive_txt(self):
		assert _detect_format(Path("NOTES.TXT")) == "text"


class TestLoadPresentation:
	def test_dispatches_to_pptx_loader(self, tmp_path):
		path = tmp_path / "deck.pptx"
		path.write_bytes(b"")
		fake = _fake_presentation("pptx")
		# load_pptx is imported inside the function body, so patch its source module
		with patch("pitchdeck.pptx_input.load_pptx", return_value=fake) as mock_load:
			result = load_presentation(path)
		mock_load.assert_called_once_with(path)
		assert result.source_format == "pptx"

	def test_dispatches_to_text_loader(self, tmp_path):
		path = tmp_path / "notes.txt"
		path.write_text("--- Slide 1 ---\nTitle\n", encoding="utf-8")
		fake = _fake_presentation("text")
		with patch("pitchdeck.text_input.load_text", return_value=fake) as mock_load:
			result = load_presentation(path)
		mock_load.assert_called_once_with(path)
		assert result.source_format == "text"

	def test_unsupported_extension_raises(self, tmp_path):
		path = tmp_path / "slides.pdf"
		with pytest.raises(ValueError, match="Unsupported"):
			load_presentation(path)
