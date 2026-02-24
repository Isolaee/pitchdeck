"""Tests for job loading and validation."""

import json

import pytest

from cvagent.job import fetch_job_from_url, load_job


def test_load_job_file_not_found(tmp_path):
	missing = tmp_path / "missing.yaml"
	with pytest.raises(FileNotFoundError, match="missing.yaml"):
		load_job(missing)


def test_load_job_missing_required_field(tmp_path):
	# Job missing 'description'
	yaml_content = "company: Acme\nrole: Engineer\n"
	f = tmp_path / "job.yaml"
	f.write_text(yaml_content)
	with pytest.raises(ValueError, match="description"):
		load_job(f)


def test_load_job_valid(tmp_path):
	yaml_content = "company: Futurice\nrole: Senior Python Engineer\ndescription: We need a Python engineer.\n"
	f = tmp_path / "job.yaml"
	f.write_text(yaml_content)
	job = load_job(f)
	assert job["company"] == "Futurice"
	assert job["role"] == "Senior Python Engineer"


# ---------------------------------------------------------------------------
# fetch_job_from_url tests (all network and LLM calls are mocked)
# ---------------------------------------------------------------------------

_SAMPLE_HTML = """
<html>
<head><title>Senior Python Engineer at Futurice</title></head>
<body>
<nav>Nav stuff</nav>
<main>
<h1>Senior Python Engineer</h1>
<p>Futurice is looking for a Python engineer to join our backend team in Helsinki.</p>
<p>Requirements: FastAPI, PostgreSQL, Docker.</p>
</main>
<footer>Footer stuff</footer>
</body>
</html>
"""

_EXTRACTED = {
	"company": "Futurice",
	"role": "Senior Python Engineer",
	"description": "Futurice is looking for a Python engineer to join our backend team in Helsinki. Requirements: FastAPI, PostgreSQL, Docker.",
	"location": "Helsinki",
}


def test_fetch_job_from_url_returns_job(mocker):
	mock_resp = mocker.MagicMock()
	mock_resp.text = _SAMPLE_HTML
	mock_resp.raise_for_status = mocker.MagicMock()
	mocker.patch("cvagent.job.requests.get", return_value=mock_resp)
	mocker.patch("cvagent.llm.generate", return_value=json.dumps(_EXTRACTED))

	job = fetch_job_from_url("https://example.com/job", model="mistral")

	assert job["company"] == "Futurice"
	assert job["role"] == "Senior Python Engineer"
	assert "description" in job
	assert job["url"] == "https://example.com/job"


def test_fetch_job_from_url_strips_nav_footer(mocker):
	mock_resp = mocker.MagicMock()
	mock_resp.text = _SAMPLE_HTML
	mock_resp.raise_for_status = mocker.MagicMock()
	mocker.patch("cvagent.job.requests.get", return_value=mock_resp)

	captured = {}

	def fake_generate(prompt, model):
		captured["prompt"] = prompt
		return json.dumps(_EXTRACTED)

	mocker.patch("cvagent.llm.generate", side_effect=fake_generate)
	fetch_job_from_url("https://example.com/job")

	assert "Nav stuff" not in captured["prompt"]
	assert "Footer stuff" not in captured["prompt"]


def test_fetch_job_from_url_handles_markdown_fences(mocker):
	mock_resp = mocker.MagicMock()
	mock_resp.text = _SAMPLE_HTML
	mock_resp.raise_for_status = mocker.MagicMock()
	mocker.patch("cvagent.job.requests.get", return_value=mock_resp)
	# LLM wraps JSON in ```json fences
	mocker.patch("cvagent.llm.generate", return_value=f"```json\n{json.dumps(_EXTRACTED)}\n```")

	job = fetch_job_from_url("https://example.com/job")
	assert job["company"] == "Futurice"


def test_fetch_job_from_url_raises_on_bad_json(mocker):
	mock_resp = mocker.MagicMock()
	mock_resp.text = _SAMPLE_HTML
	mock_resp.raise_for_status = mocker.MagicMock()
	mocker.patch("cvagent.job.requests.get", return_value=mock_resp)
	mocker.patch("cvagent.llm.generate", return_value="This is not JSON at all.")

	with pytest.raises(ValueError, match="non-JSON"):
		fetch_job_from_url("https://example.com/job")


def test_fetch_job_from_url_raises_on_missing_fields(mocker):
	mock_resp = mocker.MagicMock()
	mock_resp.text = _SAMPLE_HTML
	mock_resp.raise_for_status = mocker.MagicMock()
	mocker.patch("cvagent.job.requests.get", return_value=mock_resp)
	# LLM returns JSON but missing 'description'
	mocker.patch("cvagent.llm.generate", return_value=json.dumps({"company": "X", "role": "Y"}))

	with pytest.raises(ValueError, match="description"):
		fetch_job_from_url("https://example.com/job")


def test_fetch_job_from_url_http_error(mocker):
	import requests as req

	mock_resp = mocker.MagicMock()
	mock_resp.raise_for_status.side_effect = req.HTTPError("404")
	mocker.patch("cvagent.job.requests.get", return_value=mock_resp)

	with pytest.raises(req.HTTPError):
		fetch_job_from_url("https://example.com/job")
