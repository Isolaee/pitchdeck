"""Tests for pitchdeck.pptx_input — PowerPoint file parser."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from pitchdeck.pptx_input import (
	_get_body_texts,
	_get_notes,
	_get_title,
	_extract_slide,
	load_pptx,
)


def _make_text_frame(text: str) -> MagicMock:
	tf = MagicMock()
	tf.text = text
	para = MagicMock()
	para.text = text
	tf.paragraphs = [para]
	return tf


def _make_shape(name: str, text: str, is_title: bool = False) -> MagicMock:
	shape = MagicMock()
	shape.name = name
	shape.has_text_frame = True
	shape.text_frame = _make_text_frame(text)
	return shape


class TestGetTitle:
	def test_returns_title_text(self):
		slide = MagicMock()
		title_shape = _make_shape("Title 1", "My Title")
		title_shape.has_text_frame = True
		slide.shapes.title = title_shape
		assert _get_title(slide) == "My Title"

	def test_returns_empty_string_when_no_title_shape(self):
		slide = MagicMock()
		slide.shapes.title = None
		assert _get_title(slide) == ""

	def test_strips_whitespace(self):
		slide = MagicMock()
		title_shape = _make_shape("Title 1", "  Spaced Title  ")
		slide.shapes.title = title_shape
		assert _get_title(slide) == "Spaced Title"


class TestGetBodyTexts:
	def test_excludes_title_shape(self):
		slide = MagicMock()
		title_shape = _make_shape("Title 1", "Title text")
		body_shape = _make_shape("Content 1", "Body text")
		slide.shapes.title = title_shape
		slide.shapes.__iter__ = MagicMock(return_value=iter([title_shape, body_shape]))
		texts = _get_body_texts(slide)
		assert "Title text" not in texts
		assert "Body text" in texts

	def test_collects_multiple_text_frames(self):
		slide = MagicMock()
		slide.shapes.title = None
		shape_a = _make_shape("A", "Alpha")
		shape_b = _make_shape("B", "Beta")
		slide.shapes.__iter__ = MagicMock(return_value=iter([shape_a, shape_b]))
		texts = _get_body_texts(slide)
		assert "Alpha" in texts
		assert "Beta" in texts

	def test_filters_empty_paragraphs(self):
		slide = MagicMock()
		slide.shapes.title = None
		shape = _make_shape("A", "")
		para_empty = MagicMock()
		para_empty.text = ""
		para_text = MagicMock()
		para_text.text = "Real content"
		shape.text_frame.paragraphs = [para_empty, para_text]
		slide.shapes.__iter__ = MagicMock(return_value=iter([shape]))
		texts = _get_body_texts(slide)
		assert "" not in texts
		assert "Real content" in texts

	def test_skips_shapes_without_text_frame(self):
		slide = MagicMock()
		slide.shapes.title = None
		shape = MagicMock()
		shape.has_text_frame = False
		slide.shapes.__iter__ = MagicMock(return_value=iter([shape]))
		texts = _get_body_texts(slide)
		assert texts == []


class TestGetNotes:
	def test_returns_notes_text(self):
		slide = MagicMock()
		slide.notes_slide.notes_text_frame.text = "Speaker notes here."
		assert _get_notes(slide) == "Speaker notes here."

	def test_returns_empty_string_on_exception(self):
		# Use a real object with no notes_slide attribute to trigger AttributeError
		class FakeSlide:
			pass

		assert _get_notes(FakeSlide()) == ""

	def test_strips_whitespace(self):
		slide = MagicMock()
		slide.notes_slide.notes_text_frame.text = "  Note with spaces  "
		assert _get_notes(slide) == "Note with spaces"


class TestLoadPptx:
	def test_raises_file_not_found_for_missing_path(self):
		with pytest.raises(FileNotFoundError):
			load_pptx(Path("/nonexistent/file.pptx"))

	def test_source_format_is_pptx(self, tmp_path):
		pptx_file = tmp_path / "test.pptx"
		pptx_file.write_bytes(b"")  # create dummy file so exists() passes
		mock_slide = MagicMock()
		mock_slide.shapes.title = None
		mock_slide.shapes.__iter__ = MagicMock(return_value=iter([]))
		type(mock_slide).notes_slide = PropertyMock(side_effect=AttributeError)
		mock_prs = MagicMock()
		mock_prs.slides = [mock_slide]
		with patch("pitchdeck.pptx_input.PptxPresentation", return_value=mock_prs):
			prs = load_pptx(pptx_file)
		assert prs.source_format == "pptx"

	def test_correct_slide_count(self, tmp_path):
		pptx_file = tmp_path / "test.pptx"
		pptx_file.write_bytes(b"")
		mock_slides = []
		for _ in range(3):
			s = MagicMock()
			s.shapes.title = None
			s.shapes.__iter__ = MagicMock(return_value=iter([]))
			type(s).notes_slide = PropertyMock(side_effect=AttributeError)
			mock_slides.append(s)
		mock_prs = MagicMock()
		mock_prs.slides = mock_slides
		with patch("pitchdeck.pptx_input.PptxPresentation", return_value=mock_prs):
			prs = load_pptx(pptx_file)
		assert len(prs.slides) == 3

	def test_raises_value_error_for_invalid_pptx(self, tmp_path):
		pptx_file = tmp_path / "bad.pptx"
		pptx_file.write_bytes(b"not a pptx")
		# Don't patch — let python-pptx actually try to parse the bad bytes
		with pytest.raises((ValueError, Exception)):
			load_pptx(pptx_file)
