"""Tests for the prompt builder."""

from cvagent.prompt import build_prompt

_PROFILE = {
    "contact": {"name": "Jane Doe"},
    "skills": ["Python", "Docker"],
    "work_history": [
        {
            "company": "Acme",
            "title": "Engineer",
            "start": "2020-01",
            "end": None,
            "highlights": ["Built things"],
        }
    ],
    "projects": [
        {"name": "MyProject", "description": "A project", "tech": ["Python"]}
    ],
}

_JOB = {
    "company": "Futurice",
    "role": "Backend Engineer",
    "description": "We need a Python engineer.",
    "tone": "professional",
    "target_length": "medium",
}


def test_prompt_contains_company():
    prompt = build_prompt(_PROFILE, _JOB)
    assert "Futurice" in prompt


def test_prompt_contains_applicant_name():
    prompt = build_prompt(_PROFILE, _JOB)
    assert "Jane Doe" in prompt


def test_prompt_contains_skills():
    prompt = build_prompt(_PROFILE, _JOB)
    assert "Python" in prompt
    assert "Docker" in prompt


def test_prompt_tone_instruction():
    prompt = build_prompt(_PROFILE, _JOB)
    assert "formal and professional" in prompt


def test_prompt_length_instruction():
    prompt = build_prompt(_PROFILE, _JOB)
    assert "350 words" in prompt


def test_prompt_friendly_tone():
    job = {**_JOB, "tone": "friendly"}
    prompt = build_prompt(_PROFILE, job)
    assert "warm and approachable" in prompt


def test_prompt_short_length():
    job = {**_JOB, "target_length": "short"}
    prompt = build_prompt(_PROFILE, job)
    assert "200 words" in prompt


def test_prompt_work_history_present():
    prompt = build_prompt(_PROFILE, _JOB)
    assert "Acme" in prompt
    assert "Built things" in prompt


def test_prompt_no_profile_contact_falls_back():
    profile = {**_PROFILE, "contact": {}}
    prompt = build_prompt(profile, _JOB)
    assert "Applicant" in prompt
