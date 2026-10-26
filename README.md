# CELEHS Dataset Finder

Find documented dataset locations, read original documentation, inspect columns, and preview generated example rows.

This repository contains the application and a selected documentation snapshot for MGB IBD, MGB AD, and UPMC AD. It includes the IBD monthly laboratory README and the five-aim MAJOR IBD project README. Source-server paths are references, not public download links or access grants. Real patient data remain on their approved servers.

## What is included

- Python FastAPI backend and browser interface.
- Original Markdown documentation, readable body-only exports of the Word READMEs, recorded file structures, and a selected tracker-metadata snapshot.
- Nine fake CSVs with 1,000 generated rows each. These are not real patient records or real cohort sizes.
- Documentation-only IBD monthly laboratory summaries; no real or fake laboratory rows are supplied.
- Source-backed views of the MAJOR IBD project aims and reported analyses. The website does not perform those analyses.
- A local Ollama configuration based on `gpt-oss:20b`, without model weights or credentials.

The original full tracker, private review notes, Word review files/comments, recordings, runtime databases, logs, backups, and local Python installation are not included. Personal computer paths are removed from exported catalog JSON. The readable README exports retain their documented research-server paths; the original Word files are kept in the author's local workspace. The two supplied IBD Markdown originals are unchanged.

## Run locally

Use Python 3.12 or a compatible supported version and install Ollama separately.

```powershell
git clone https://github.com/EnciiC/CELEHS_DATA.git
cd CELEHS_DATA
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r local_demo/requirements.txt
ollama pull gpt-oss:20b
ollama create celehs-catalog -f llm/Modelfile
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_demo.ps1
```

Open http://127.0.0.1:8000/. The launcher uses a dedicated local Ollama service on port 11435. On Linux/macOS, start `ollama serve` with `OLLAMA_HOST=127.0.0.1:11435`, create the same named model on that service, set `CATALOG_OLLAMA_URL=http://127.0.0.1:11435`, and run `python -m uvicorn local_demo.app:app --host 127.0.0.1 --port 8000` inside the environment.

Browsing documentation, viewing schemas, and downloading fake examples do not invoke the language model. Natural-language questions generally use one or two model calls; basic storage lookups and greetings can be answered without one. The local model is not fine-tuned on patient data.

## Questions to try

- Where can I find IBD data?
- Can we find IBD data on O2?
- What AD data do we have?
- Show IBD monthly lab columns.
- How many patients are in the IBD lab data?
- What can we do with IBD data?
- Compare IBD Aim 4 and Aim 5 outcome rules.
- Compare the monthly count columns for MGB AD and UPMC AD.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest local_demo/tests -q
```

## Online deployment status

Publishing this repository does not deploy a working website. This version still binds to the local computer and expects a local Ollama model. GitHub Pages cannot run its Python backend or model service.

An online version needs a hosted backend and model service, explicit allowed domains, HTTPS, request limits, a spending cap, and protected administrative operations. A hosted-model API adapter and deployment configuration are not configured in this release. Keep provider credentials in backend secrets, never in browser code or this repository. Do not expose an Ollama service directly to the internet.

Review source-document permissions before redistributing them or sending them to a hosted model provider. Adding sign-in later does not retract copies already made from a public repository. Generated examples are for file-format and software testing only, not clinical inference or treatment advice.
