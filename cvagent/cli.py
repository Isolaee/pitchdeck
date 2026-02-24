"""CLI entry point for CVagent."""

from __future__ import annotations

import argparse
from pathlib import Path

from cvagent.job import fetch_job_from_url, load_job
from cvagent.llm import DEFAULT_MODEL, generate
from cvagent.profile import load_profile
from cvagent.prompt import build_prompt
from cvagent.renderer import render_docx, render_markdown, render_text, render_to_stdout

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_PROFILE = _REPO_ROOT / "data" / "user_profile.yaml"
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "output"


def main() -> None:
	parser = argparse.ArgumentParser(description="Generate a customized cover letter using a local LLM via Ollama.")
	parser.add_argument(
		"job",
		help="Path to a job YAML file, or a URL to a job posting page",
	)
	parser.add_argument(
		"--profile",
		type=Path,
		default=_DEFAULT_PROFILE,
		help="Path to user_profile.yaml (default: data/user_profile.yaml)",
	)
	parser.add_argument(
		"--model",
		default=DEFAULT_MODEL,
		help=f"Ollama model name (default: {DEFAULT_MODEL})",
	)
	parser.add_argument(
		"--format",
		choices=["markdown", "text", "stdout", "docx"],
		default="markdown",
		help="Output format (default: markdown)",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=None,
		help="Output file path (auto-named from company + role if omitted)",
	)
	args = parser.parse_args()

	profile = load_profile(args.profile)
	if args.job.startswith("http://") or args.job.startswith("https://"):
		job = fetch_job_from_url(args.job, model=args.model)
	else:
		job = load_job(Path(args.job))
	prompt = build_prompt(profile, job)

	print(f"Generating cover letter for {job['role']} at {job['company']}...")
	text = generate(prompt, model=args.model)

	if args.format == "stdout":
		render_to_stdout(text)
		return

	# Auto-name output file based on company + role slug
	if args.output is None:
		slug = f"{job['company']}_{job['role']}".lower().replace(" ", "_")
		_EXT = {"markdown": "md", "text": "txt", "docx": "docx"}
		ext = _EXT[args.format]
		args.output = _DEFAULT_OUTPUT_DIR / f"{slug}.{ext}"

	if args.format == "markdown":
		render_markdown(text, args.output)
	elif args.format == "docx":
		render_docx(text, args.output, profile, job)
	else:
		render_text(text, args.output)


if __name__ == "__main__":
	main()
