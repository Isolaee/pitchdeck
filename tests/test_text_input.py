"""Tests for pitchdeck.text_input — plain text presentation parser."""

from __future__ import annotations

import pytest

from pitchdeck.text_input import _parse_slide_block, _parse_slides


class TestParseSlides:
	def test_single_slide_produces_one_slide(self):
		raw = "--- Slide 1 ---\nTitle\nBody line\n"
		slides = _parse_slides(raw)
		assert len(slides) == 1

	def test_multiple_slides_correct_count(self):
		raw = "--- Slide 1 ---\nA\n--- Slide 2 ---\nB\n--- Slide 3 ---\nC\n"
		slides = _parse_slides(raw)
		assert len(slides) == 3

	def test_slide_numbers_from_delimiter_not_position(self):
		# Slides numbered 5 and 10 — should use those numbers, not 1 and 2
		raw = "--- Slide 5 ---\nA\n--- Slide 10 ---\nB\n"
		slides = _parse_slides(raw)
		assert slides[0].number == 5
		assert slides[1].number == 10

	def test_no_delimiters_raises_value_error(self):
		with pytest.raises(ValueError, match="No slide delimiters"):
			_parse_slides("This is just some text with no delimiter.")

	def test_preamble_before_first_slide_is_ignored(self):
		raw = "Preamble text\n--- Slide 1 ---\nTitle\n"
		slides = _parse_slides(raw)
		assert len(slides) == 1
		assert slides[0].title == "Title"

	def test_case_insensitive_delimiter(self):
		raw = "--- SLIDE 1 ---\nTitle\n"
		slides = _parse_slides(raw)
		assert len(slides) == 1


class TestParseSlideBlock:
	def test_title_is_first_non_empty_line(self):
		slide = _parse_slide_block("\n\nMy Title\nBody text\n", 1)
		assert slide.title == "My Title"

	def test_body_excludes_title(self):
		slide = _parse_slide_block("Title\nBody line one\nBody line two\n", 1)
		assert "Title" not in slide.body
		assert "Body line one" in slide.body
		assert "Body line two" in slide.body

	def test_notes_extracted_after_label(self):
		block = "Title\nBody\nNotes:\nSpeaker note here.\n"
		slide = _parse_slide_block(block, 1)
		assert "Speaker note here." in slide.notes

	def test_body_excludes_notes_content(self):
		block = "Title\nBody line\nNotes:\nNote content\n"
		slide = _parse_slide_block(block, 1)
		assert "Note content" not in slide.body

	def test_empty_body_lines_filtered(self):
		block = "Title\n\nBody A\n\nBody B\n\n"
		slide = _parse_slide_block(block, 1)
		assert "" not in slide.body
		assert len(slide.body) == 2

	def test_missing_notes_label_gives_empty_notes(self):
		block = "Title\nBody text\n"
		slide = _parse_slide_block(block, 1)
		assert slide.notes == ""

	def test_case_insensitive_notes_label(self):
		for label in ("Notes:", "NOTES:", "notes:", "Notes:  "):
			block = f"Title\nBody\n{label}\nNote text\n"
			slide = _parse_slide_block(block, 1)
			assert "Note text" in slide.notes, f"Failed for label: {label!r}"

	def test_slide_number_set_correctly(self):
		slide = _parse_slide_block("Title\n", 7)
		assert slide.number == 7

	def test_empty_block_gives_empty_title_and_body(self):
		slide = _parse_slide_block("\n\n\n", 1)
		assert slide.title == ""
		assert slide.body == []
		assert slide.notes == ""
