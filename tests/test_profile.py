"""Tests for profile loading and validation."""

import pytest

from cvagent.profile import load_profile


def test_load_profile_file_not_found(tmp_path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError, match="missing.yaml"):
        load_profile(missing)


def test_load_profile_missing_required_key(tmp_path):
    # Profile missing 'work_history'
    yaml_content = "contact:\n  name: Test\nskills:\n  - Python\n"
    f = tmp_path / "profile.yaml"
    f.write_text(yaml_content)
    with pytest.raises(ValueError, match="work_history"):
        load_profile(f)


def test_load_profile_valid(tmp_path):
    yaml_content = (
        "contact:\n  name: Test\n"
        "skills:\n  - Python\n"
        "work_history:\n  - company: Acme\n    title: Dev\n    start: '2020-01'\n"
    )
    f = tmp_path / "profile.yaml"
    f.write_text(yaml_content)
    profile = load_profile(f)
    assert profile["contact"]["name"] == "Test"
    assert "Python" in profile["skills"]
    assert len(profile["work_history"]) == 1
