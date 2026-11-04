### README 

# Dataset Title: WEST data and labels for severe asthma phenotyping

BCH patients with at least 1 ICD code (J45) for asthma. 

## Files Included

- `patient_summary.csv`: 
- `README.txt`: This documentation file.
- training and validation directories: patient-level EHR (codified) data

## Data Dictionary:

# Individual patient files:
# ID - Unique patient identifier
# CODE - EHR code identifier (note: IDs can have multiple rows for each code corresponding to a different TIME)
# COUNT - Integer count for CODE at time TIME
# TIME - Number of months since first asthma code (note: first asthma code in EHR occurred at TIME=0; codes with TIME<0 excluded from analysis)

# Patient summary file:
# ID - Unique patient identifier
# FINALSA - Equal to FINALSA_gold when gold=1 or FINALSA_silver when gold=0
# FINALSA_gold - Gold label for severe asthma status (note: NA for patients with no gold label)
# FINALSA_silver - Silver label for severe asthma status (based on KOMAP)
# gold - Indicator for whether a gold label is available for the ID
# severe_genie_ct - Total code count for CUI C0581126 for an ID
# KOMAP_ICD - Probability of severe asthma from KOMAP algorithm using ICD codes + CUIs
# KOMAP_calibrated - Probability of severe asthma from KOMAP algorithm re-calibrated via logistic regression
# training - Indicator is 1 if patient is in training cohort or 0 if patient is in validation cohort

## Summary Statistics

- Total Samples: 7822
- Features: NLP

## Demographic Information

- Patient Size: 7822

## Metadata
1. Code: Transformer training pipeline (train.py, eval.py, silver label update scripts)
2. External Data (raw data): Raw NLP extracts from BCH E3 server.
3. Data (processed / derived from code):
- patient_summary.csv containing gold and silver labels, silver probabilities, registry indicators, and train/validation split
- Patient-level longitudinal codified EHR files formatted for Transformer input
- FINALSA labels combining gold and silver sources
4. Report: Associated analyses included in: https://www.nature.com/articles/s41746-026-02406-x

## Traceability 
- Kim extracted original data from BCH E3 server (NILE on E3 notes)
- Kim preprocessed data for transformer model

## Contact
Kim Greco

## Key Questions

1. Why is the data interesting, and what are its limitations?
- Enables weakly supervised phenotyping of severe asthma (SA) using real-world longitudinal EHR data.
- Combines gold-standard registry labels with scalable silver labels derived from structured EHR codes.
- Limitation: Single-center dataset (BCH), limiting external generalizability.

2. Guide on how to use the dataset?
Use patient_summary.csv to:
- Select training vs validation cohort (training column)
- Choose label type (FINALSA, FINALSA_gold, FINALSA_silver, or probabilistic labels such as KOMAP_prob)
- Restrict to gold-only subset if needed (gold == 1)
Load individual patient files from training/validation directories:
- Aggregate by ID
- Sort by TIME
- Construct sequences of (CODE, COUNT, TIME)
Feed sequences into the Transformer pipeline:
- Map CODE to embeddings
- Use FINALSA (or probabilistic label) as training target
- Optionally perform iterative silver label updates

3. What are the related datasets 
Subset of BCH EHR data extracted from the E3 server.