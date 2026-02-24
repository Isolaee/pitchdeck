"""Load and validate a job application YAML file, or fetch one from a URL."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import requests
import yaml
from bs4 import BeautifulSoup


def load_job(path: Path) -> dict[str, Any]:
	"""Read a job YAML and return the parsed dict.

	Raises FileNotFoundError if the file does not exist.
	Raises ValueError if required fields are missing.
	"""
	if not path.exists():
		raise FileNotFoundError(f"Job file not found: {path}")

	with path.open("r", encoding="utf-8") as f:
		data = yaml.safe_load(f)

	_validate_job(data)
	return data


def fetch_job_from_url(url: str, model: str = "mistral") -> dict[str, Any]:
	"""Fetch a job posting from a URL and extract fields using the LLM.

	Downloads the page, strips HTML to plain text, then asks the LLM to
	extract company, role, description, and location as JSON.

	Raises requests.HTTPError if the page cannot be fetched.
	Raises ValueError if the LLM response cannot be parsed or required
	fields are missing.
	"""
	print(f"Fetching job posting from: {url}")
	page_text = _fetch_page_text(url)

	print("Extracting job details with LLM...")
	data = _extract_with_llm(page_text, model)

	_validate_job(data)
	# Always store the source URL
	data.setdefault("url", url)
	return data


def _fetch_page_text(url: str) -> str:
	"""Download a URL and return the visible text content."""
	headers = {"User-Agent": "Mozilla/5.0 (compatible; CVAgent/1.0)"}
	response = requests.get(url, headers=headers, timeout=15)
	response.raise_for_status()

	soup = BeautifulSoup(response.text, "html.parser")

	# Remove non-content tags
	for tag in soup(["script", "style", "nav", "footer", "header", "meta"]):
		tag.decompose()

	text = soup.get_text(separator="\n")
	# Collapse excessive blank lines
	text = re.sub(r"\n{3,}", "\n\n", text).strip()

	# Trim to ~8000 chars to stay within LLM context
	return text[:8000]


def _extract_with_llm(page_text: str, model: str) -> dict[str, Any]:
	"""Ask the LLM to extract structured job data from raw page text.

	Returns a dict with at minimum: company, role, description.
	Raises ValueError if the response cannot be parsed as JSON.
	"""
	# Import here to avoid circular dependency (llm imports nothing from job)
	from cvagent.llm import generate

	prompt = (
		"You are a job posting parser. Extract the following fields from the job posting text below "
		"and return ONLY a valid JSON object with these keys:\n"
		'  "company"     – the hiring company name (string)\n'
		'  "role"        – the job title (string)\n'
		'  "description" – the full job description including requirements (string)\n'
		'  "location"    – office location or "Remote" if remote (string, optional)\n\n'
		"Return only the JSON object, no explanation, no markdown fences.\n\n"
		f"Job posting text:\n{page_text}"
	)

	raw = generate(prompt, model=model)

	# Strip markdown fences if the LLM adds them despite instructions
	raw = re.sub(r"^```[a-z]*\n?", "", raw.strip())
	raw = re.sub(r"\n?```$", "", raw.strip())

	try:
		data = json.loads(raw)
	except json.JSONDecodeError as exc:
		raise ValueError(f"LLM returned non-JSON response. Raw output:\n{raw}") from exc

	if not isinstance(data, dict):
		raise ValueError(f"Expected a JSON object, got: {type(data).__name__}")

	return data


def _validate_job(data: dict[str, Any]) -> None:
	"""Check that required fields are present in the job input."""
	required = {"company", "role", "description"}
	missing = required - set(data.keys())
	if missing:
		raise ValueError(f"Job input is missing required fields: {missing}")
