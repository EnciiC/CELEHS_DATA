Dataset and Contact

Dataset name KDI RA

Brief description

README curator and email  Tianrun(Austin) Cai

Date updated

Storage platform  KDI

Patients and date coverage

Who is included and how were they selected [Give the starting population, RA code rule, phenotype method and cutoff, and any later filters]

|  | Value | What is counted |
| --- | --- | --- |
| Patients | 1987 | [Unique patients and selection stage] KOMAP positive for RA, cutoff - 1.387 ppv90% |
| Notes | 3.5million | [All notes or notes selected for the agent] |
| Date coverage | All dates until 2024.9.30 | [Note dates or other dates covered] |

Other useful cohort details if available [Demographics, note types, or exclusions]

Files and locations

| File or group | Full path and filename | Format | What one record represents |
| --- | --- | --- | --- |
| Notes for the agent | /scratch/MVP_CORE_OPS/caitianrun/notes/RA_KOMAP_positive /scratch/MVP_CORE_OPS/caitianrun/notes/RA_KOMAP_positive_parquet | JSON and Parquet  30 patients in each file | MVPCore_ID,TiuDocumentSID, EpisodeBeginDateTime, ScrubbedText |
| Results | /mnt/mvpfs/MVP_CORE_OPS/caitianrun/DAS_Agent/TEST/output | tags.csv | informativeness |
| Disease activity results | /mnt/mvpfs/MVP_CORE_OPS/caitianrun/DAS_Agent/TEST/output | results.csv | existing_DAS_score, calculated_das_score, calculated_das_category, TiuDocumentSID,evidences |

Fields and how files connect

How is the JSON organized - Column names, meanings. If possible, can show fake rows with units

Which fields connect the notes and result files [Give exact patient and note ID fields, date fields and date formats, and whether IDs match other EHR files]

How the agent results were created

Agent and score names

DAS_agent

How were the source notes prepared

Extracted from large note pool for all MVP patients in Parquet format and Snappy compression

How are the scores produced

Scores are from two resources: 1. Extracted from notes 2. Calculated based on the DAS score calculation formula online by understanding the notes.

DAS category: high, moderate, low, remission (all informative notes will be evaluated) 5.1 - 3.2 - 2.5

Agent version (if any)

How were the results checked

Compare with human chart review on 187 notes, the performance is evaluated

Access rule

Requires KDI access

Related Codes

How should a new user open and use the files

Using python as an example:

pip install pyarrow

import pyarrow.parquet as pq

table = pq.read_table("data.parquet", columns=["col1","col2"])

df = table.to_pandas()

Code to recreate the files (if any)

import pandas as pd

data = [ {"id": 1, "text": "sample 1", "label": 0}, {"id": 2, "text": "sample 2", "label": 1}, ] df = pd.DataFrame(data) # write parquet

df.to_parquet("out.parquet", engine="pyarrow")
