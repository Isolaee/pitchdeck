"""Build the LLM prompt from profile + job data."""

from __future__ import annotations

from typing import Any

# Maps job YAML values to human-readable instructions embedded in the prompt
_LENGTH_GUIDE: dict[str, str] = {
    "short": "approximately 200 words",
    "medium": "approximately 350 words",
    "long": "approximately 500 words",
}

_TONE_GUIDE: dict[str, str] = {
    "professional": "formal and professional",
    "friendly": "warm and approachable",
    "enthusiastic": "enthusiastic and energetic",
}


def build_prompt(profile: dict[str, Any], job: dict[str, Any]) -> str:
    """Compose the full prompt string to send to the LLM.

    Structures applicant profile and job details into a single instruction
    block that works well with Mistral and Llama instruction-tuned models.
    """
    tone = _TONE_GUIDE.get(job.get("tone", "professional"), "formal and professional")
    length = _LENGTH_GUIDE.get(job.get("target_length", "medium"), "approximately 350 words")

    skills_str = ", ".join(profile.get("skills", []))
    work_str = _format_work_history(profile.get("work_history", []))
    projects_str = _format_projects(profile.get("projects", []))

    contact = profile.get("contact", {})
    name = contact.get("name", "Applicant")

    prompt = f"""You are an expert career coach and professional writer.
Write a cover letter for the following applicant and job.

# Applicant
Name: {name}
Skills: {skills_str}

## Work History
{work_str}

## Projects
{projects_str}

# Target Job
Company: {job['company']}
Role: {job['role']}
Location: {job.get('location', 'Not specified')}

## Job Description
{job['description'].strip()}

# Instructions
- Write {length}
- Tone: {tone}
- Address the letter to the hiring team at {job['company']}
- Highlight skills and experience most relevant to the job description
- Do not invent facts; use only what is provided above
- Output only the cover letter text, no preamble or commentary
- Bold key phrases where appropriate using markdown (**phrase**)
"""
    return prompt


def _format_work_history(history: list[dict[str, Any]]) -> str:
    lines = []
    for entry in history:
        end = entry.get("end") or "Present"
        lines.append(f"- {entry['title']} at {entry['company']} ({entry['start']} to {end})")
        for highlight in entry.get("highlights", []):
            lines.append(f"  * {highlight}")
    return "\n".join(lines)


def _format_projects(projects: list[dict[str, Any]]) -> str:
    lines = []
    for p in projects:
        tech = ", ".join(p.get("tech", []))
        lines.append(f"- {p['name']}: {p['description']} [{tech}]")
    return "\n".join(lines)
