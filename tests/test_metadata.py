"""Tests for pitchdeck.metadata — YAML metadata loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pitchdeck.metadata import load_metadata


def _write_yaml(path: Path, data: dict) -> Path:
	path.write_text(yaml.dump(data), encoding="utf-8")
	return path


class TestLoadMetadata:
	def test_valid_metadata_loads(self, tmp_path):
		f = _write_yaml(tmp_path / "meta.yaml", {"title": "My Talk", "author": "Jane"})
		data = load_metadata(f)
		assert data["title"] == "My Talk"
		assert data["author"] == "Jane"

	def test_missing_author_raises_value_error(self, tmp_path):
		f = _write_yaml(tmp_path / "meta.yaml", {"title": "My Talk"})
		with pytest.raises(ValueError, match="author"):
			load_metadata(f)

	def test_missing_title_raises_value_error(self, tmp_path):
		f = _write_yaml(tmp_path / "meta.yaml", {"author": "Jane"})
		with pytest.raises(ValueError, match="title"):
			load_metadata(f)

	def test_optional_fields_pass_through(self, tmp_path):
		f = _write_yaml(
			tmp_path / "meta.yaml",
			{"title": "T", "author": "A", "tone": "professional", "audience": "investors"},
		)
		data = load_metadata(f)
		assert data["tone"] == "professional"
		assert data["audience"] == "investors"

	def test_file_not_found_raises(self):
		with pytest.raises(FileNotFoundError):
			load_metadata(Path("/nonexistent/meta.yaml"))

	def test_both_required_fields_missing_error_mentions_both(self, tmp_path):
		f = _write_yaml(tmp_path / "meta.yaml", {"topic": "something"})
		with pytest.raises(ValueError) as exc_info:
			load_metadata(f)
		msg = str(exc_info.value)
		assert "author" in msg
		assert "title" in msg
