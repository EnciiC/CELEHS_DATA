# CELEHS local dataset demo

Start from the project directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_demo.ps1
```

- Website: http://127.0.0.1:8000
- Web API documentation: http://127.0.0.1:8000/docs
- Dedicated Ollama service: http://127.0.0.1:11435
- Model: celehs-catalog, based on gpt-oss:20b
- GPU backend: cuda_v12, used to avoid the observed cuda_v13 initialization crash
- Model storage: E:\.ollama

The services bind to loopback. There is no cloud model call, external search, patient-server connection or remote hosting. Only prepared local catalog folders are imported.

## Available data groups

MGB IBD, MGB AD and UPMC AD. Their nine synthetic CSVs total 9,000 generated rows. Each data preview is limited to 50 rows. Only explicitly registered synthetic data files can be previewed or downloaded as data. Original documentation and column dictionaries are available separately.

IBD is on MGB Windows/SFA and Eris, with no O2 copy. MGB AD and UPMC AD have documented O2 paths. UPMC monthly files are stored under an MGB/MS-AD directory; their site remains UPMC.

The catalog imports each folder's catalog_record.json, schema.json, column_dictionary.csv, README.md and README_original.docx. SQLite stores records and documentation in runtime/catalog.sqlite3. Full-text search indexes documented facts and the relevant section of the original README. The shared AD document's VA/KDI section is not indexed as a demo dataset.

The October 2 tracker at outputs/resource_catalog_20261002/CELEHS_Resource_Catalog.xlsx is read as an additional metadata source. Only DATA-001 (MGB AD), DATA-002 (UPMC AD), and DATA-004 (IBD) from Datasets are imported. No other datasets, the VA row, private README status or follow-up checklist are added. Spreadsheet fields retain cell references. The workbook is not modified or offered as a download. Click Spreadsheet entry to read the relevant public fields. Reload local files refreshes this source too.

IBD date summaries are read directly from the three date tables in Sara's original README. A general time-distribution question shows processed codified and processed NLP Total minimum, 25th percentile, median, 75th percentile and maximum dates. Raw/by-source questions select their own table groups. Reported extremes are preserved with a warning, not treated as a verified clean range. The source does not specify whether date percentiles are weighted by records or patients, and these are not automatically monthly-file coverage. Spreadsheet ranges are kept separate from README percentiles and from generated fake dates.

Research questions show matching file names with optional locations. APOE questions use a short matching original excerpt rather than a whole surrounding section. Monthly counts cannot establish precise medication start/stop dates; raw/daily code dates also need validated treatment-event definitions. Requests to draw clinical effectiveness conclusions from fake rows are stopped before model inference.

Monthly schema comparisons include a short conclusion before the file lists. The application derives the statement from the selected files' documented column meanings. It distinguishes codified and NLP code/count fields and limits the comparison to the requested file type. Similar row structure does not establish interchangeable code mappings or cohorts. This is a source-controlled presentation step, not model training or fine-tuning.

## Added IBD documentation (October 25, 2026)

The IBD entry also imports two unchanged original Markdown documents: `IBD_LAB_MONTHLY_README.md` and `IBD_README.md`. Both appear under READMEs alongside Sara's original DOCX, with separate readable views, original downloads, and source citations. The local copies are registered in `demo_input/IBD/catalog_record.json`; the source documents on the Desktop are not modified or monitored automatically.

The laboratory resource is documentation-only: its server folder, RDS/CSV names, processing script, columns, row meaning, reported counts, and coverage are read from its README. No real lab files are opened or served, no lab fake rows have been generated, and the original nine fake CSVs are unchanged. Its patient-lab-unit-month rows, unique patients, and contributing measurements are distinct counts. Lab dates do not replace the older codified/NLP date tables. The new project README also resolves the old unconfirmed raw concept-name lookup by identifying the full `concept_dimension` export; that export itself is not loaded locally.

Broad IBD inventory questions include the monthly lab summary and MAJOR project documentation. Code-count-only questions remain limited to the requested codified/NLP files. Questions about prior IBD work or what the data have supported show the five project aims; aim-specific questions retrieve the documented settings, folders, definitions, or reported findings. Aim 4's five-rule prediction response and Aim 5's four-rule causal response stay separate. These are descriptions of documented work, not analyses performed by the website or new clinical recommendations.

The local model interprets the question. Registered lab and project views then render source-backed content directly, without a redundant second selection call. No model training or fine-tuning is needed. Test the additions with `python tools/check_ibd_readmes.py`; the live report is saved in `runtime/ibd_readme_checks_20261025.json`.

Useful added questions:

- What IBD data do we have?
- Where can I find IBD monthly lab data?
- Show IBD monthly lab columns.
- How many patients are in the IBD lab data?
- What is the IBD lab date distribution?
- What can we do with IBD data?
- What have we done in IBD Aim 3?
- Compare IBD Aim 4 and Aim 5 outcome rules.
- Where is the code for IBD Aim 5?

## How the agent answers

1. Handle greetings and simple storage questions directly. A storage lookup must name a documented dataset without adding an unconfirmed subgroup or subject.
2. For other meaningful questions, ask the local model to interpret the request using supplied documentation.
3. Retrieve candidate datasets and relevant original README excerpts, then ask the model for a JSON selection of dataset/evidence IDs.
4. Reject unknown or cross-dataset evidence IDs.
5. Render the selected and required source facts with README links.

The model selects information but does not write paths, cohort numbers or new medical facts. Answers are limited to the requested topic: monthly structure, locations, dictionaries, counts, or sample rows. Paths and dictionary references are returned as structured fields and shown on click, not repeated in the answer. If the model fails, the response explicitly says saved documentation was used. This is retrieval with local inference, not fine-tuning. Fake rows are not sent to the model as evidence of real data distributions.

## Short answers and browsing

The website is called **Dataset Finder**. Monthly structure questions show only the matching codified/NLP column names. Location questions show storage and named folders/files, with paths collapsed. Codified and NLP dictionary references are tied to the requested file; the IBD raw CONCEPT_CD lookup is not shown for monthly files.

AD overview answers explicitly show Storage: O2 for both sites. The MGB AD monthly NLP reference points to the complete NLP folder, not the inspected 1_1501.RData batch. The batch filename is retained only as provenance for the observed file row count.

Dataset notes are short summaries of row meanings and column names, limited to the files in the current answer. They are not the original README and do not replace it. How the fake data were made is a separate, short explanation of generated files. The detailed generated README.md and its internal review checklist remain on disk, outside the public document endpoints. The old catalog document endpoint now returns the same short generation explanation.

Direct storage questions return a compact answer first: for example, Is IBD available on O2? and Can we find IBD data on O2? return No, with its documented MGB Windows/SFA and Eris storage. These clear lookups use verified metadata without model inference and are labeled Dataset search. Detailed locations and schemas are optional follow-up actions. An explicit no-O2 flag supports a negative answer; an undocumented copy on another platform is described as not documented, never as definitely absent.

## What the local model does (and does not do)

No model training or fine-tuning has been performed. The installed gpt-oss:20b weights are unchanged; celehs-catalog adds a system prompt and inference settings. README text, curator-supplied metadata and schemas are retrieved locally and passed as context for each model request. The model selects documented evidence IDs, which the application validates before rendering.

This is a hybrid prototype. The local model now interprets meaningful questions before dataset selection, including unfamiliar research subjects and synonyms. It distinguishes documented matches, unconfirmed subjects, clarification requests and simple source-backed explanations. It can draft a relevant clarification or a short explanation of rows/columns; it cannot establish availability from general medical knowledge. Paths, source statistics, storage decisions and schemas still use validated source fields and controlled rendering. Greetings and basic help are lightweight application responses.

The evaluation questions test that behavior; they are not training examples that update model weights. Synthetic CSV rows are preview material, not a model-training dataset. Adding or correcting documentation requires updating the prepared records/index, not retraining the model.

## Conversation and missing datasets

Greetings, thanks and basic help use a short Guide response. Missing-dataset questions use local-model interpretation and a short uncertainty statement plus a relevant clarification, labeled Local LLM when interpretation succeeds. This applies to arbitrary topics, not only RA/MS/VINCI/MIMIC. The generic words data, available and a site name no longer trigger an all-dataset answer. An information checklist or browsing current datasets is offered without pretending an unrelated cohort matches.

Dataset context survives greetings and thanks. A pending missing topic is kept for follow-up questions, so asking about monthly counts after an RA request does not silently return AD or IBD data. Choosing a named available dataset resets that pending topic. This context is temporary and held in the browser; reloading starts a new conversation. The chat cannot upload documents, contact a curator, or automatically add a dataset.

Fake examples can be opened on click in search answers. The combined Files and columns view lets users choose a file, see the first five generated rows, read a Column/Meaning/Type table, expand a source path, show ten rows, and download the synthetic CSV. The full column dictionary download uses an English-only copy with a UTF-8 BOM for Excel. The bilingual source CSV is unchanged. The original Word README is displayed with headings, paragraphs, merged table cells and highlighted paths; the original DOCX download remains unchanged. Bilingual annotations are removed from the English display and retrieval copies, not from the source files.

Original documentation is preserved. Generated README notes include synthetic assumptions, which are not treated as real cohort statistics. Dataset-specific access requirements and missing dictionary paths are shown as not documented rather than guessed.

## Useful demo questions

- I wanted to see IBD data, guide me and let me know where I can find it.
- I wanted to see AD, what we have now?
- Show UPMC AD monthly column names and their types.
- Compare the monthly count columns for MGB AD and UPMC AD.
- I want to study EHR data and the gut microbiome. What is documented?
- Where can I find raw and daily UPMC AD data?
- What is the patient count for IBD?
- What is the patient count for AD?
- Where can I find VINCI heart failure data?

## Updating local materials

Project READMEs can also describe searchable data components, including registry outcomes and their linkage to EHR. See `README_TOPICS.md` for the reusable section registration. The IBD overview includes two registry-cohort file references from the Aim 3 README. Registry questions retrieve the cohort description, known fields, outcomes or current linkage instructions with source references. No registry payload or fake registry rows are served.

Edit the prepared README/metadata files, then click Reload local files. This reloads the three configured groups. To add a new group, prepare the same folder structure and register it in local_demo/catalog.py. The user-facing catalog is a local snapshot and does not monitor source servers.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest local_demo/tests -q
.\.venv\Scripts\python.exe -m local_demo.evaluate
```

The acceptance report is local_demo/DEMO_TEST_RESULTS.md. Full response records are in runtime/acceptance_results.json. These tests cover the demo scope; they do not certify arbitrary research recommendations.

## Main APIs

- GET /api/health
- GET /api/datasets?q=AD
- GET /api/datasets/{id}
- GET /api/datasets/{id}/readme/catalog
- GET /api/datasets/{id}/readme/original
- GET /api/datasets/{id}/schema
- GET /api/datasets/{id}/files/{filename}/preview?limit=10
- GET /api/datasets/{id}/download/{filename}
- POST /api/chat with {"query":"Show IBD","use_llm":true}
- POST /api/catalog/reload

Dependencies are installed in the project's .venv, not in the bundled runtime. If rebuilding the environment, install local_demo/requirements.txt. Server logs are in runtime/web.stderr.log and runtime/ollama.stderr.log. The webpage has no external fonts, scripts or analytics.

