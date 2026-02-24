# CVAgent

A local, privacy-first cover letter generator. Describe yourself once in a YAML profile, point the tool at a job posting (file or URL), and get a tailored cover letter — without sending your data to any cloud service.

## Goals

- **Automate** the tedious parts of job applications — no more rewriting the same cover letter from scratch
- **Personalise** every letter to the specific role and company using a local LLM
- **Keep data local** — your profile and generated letters never leave your machine
- **Demonstrate practical engineering** — the project itself is a portfolio piece

## How It Works

1. Your skills, work history, and contact details live in `data/user_profile.yaml`
2. A job description is provided as a YAML file or a public URL
3. The LLM (running locally via [Ollama](https://ollama.com)) writes a tailored cover letter
4. Output is saved as a formatted `.docx` file ready to open in Word and export as PDF

## Setup

**Prerequisites:** Python 3.9+, [Ollama](https://ollama.com) installed and running

```bash
# 1. Clone the repo
git clone https://github.com/isolaee/CVagent.git
cd CVagent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull a model
ollama pull mistral

# 4. Create your profile (gitignored — stays local)
cp data/user_profile.example.yaml data/user_profile.yaml
# Edit data/user_profile.yaml with your details
```

## Usage

**From a job YAML file:**
```bash
python -m cvagent.cli data/jobs/myjob.yaml --format docx
```

**From a job posting URL:**
```bash
python -m cvagent.cli https://company.com/careers/job-posting --format docx
```

**Options:**
```
positional:
  job                  Path to a job YAML file, or a URL to a job posting page

optional:
  --profile PATH       Path to user_profile.yaml (default: data/user_profile.yaml)
  --model MODEL        Ollama model name (default: mistral)
  --format FORMAT      Output format: markdown | text | stdout | docx (default: markdown)
  --output PATH        Output file path (auto-named from company + role if omitted)
```

Output is saved to `output/` and named `company_role.docx` automatically.

## Job Input Format (YAML)

```yaml
company: "Acme Corp"
role: "Software Engineer"
location: "Helsinki, Finland"          # optional
url: "https://acme.com/careers/123"   # optional

description: >
  We are looking for a software engineer to join our team...

tone: "professional"     # professional | friendly | enthusiastic
target_length: "medium"  # short (~200 words) | medium (~350 words) | long (~500 words)
```

See `data/user_profile.example.yaml` for the full profile format.

## Tech Stack

| Component | Library |
|---|---|
| LLM inference | [Ollama](https://ollama.com) + `ollama` Python SDK |
| DOCX rendering | `python-docx` |
| HTML scraping | `requests` + `beautifulsoup4` |
| Config format | `PyYAML` |
| Testing | `pytest` + `pytest-mock` |
| Linting | `ruff` |

## License

MIT License — see [LICENSE](LICENSE) for details.

Free to use, modify, and distribute. Attribution appreciated but not required.

---

*Built by [Eero Isola](https://github.com/isolaee) — the project itself is a demonstration of practical software engineering.*
