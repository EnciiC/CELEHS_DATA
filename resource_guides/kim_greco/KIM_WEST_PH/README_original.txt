### README 

# Dataset Title: WEST data and labels for pulmonary hypertension phenotyping

BCH patients with at least 1 PheCode for pulmonary hypertension.

## Files Included

- `patient_summary.csv`: 
- `README.txt`: This documentation file.
- training and validation directories: patient-level EHR (codified) data

## Data Dictionary:

# Patient summary file:
# ID - Unique patient identifier
# FINALPAH - Equal to FINALPAH_gold when gold=1 or FINALPAH_silver when gold=0
# FINALPAH_gold - Gold label for PAH status (note: NA for patients with no gold label)
# FINALPAH_silver - Silver label for PAH status (note: 1 if PheCode 415.2 appeared 2+ times in EHR and 0 otherwise)
# gold - Indicator for whether a gold label is available for the ID
# REG_PT_X - Indicator for whether patient is in registry (note: NA for patients without a gold label)
# count_415_2 - Total code count for PheCode 415.2 for an ID
# KOMAP_prob - Probability of PAH from KOMAP algorithm
# training - Indicator is 1 if patient is in training cohort or 0 if patient is in validation cohort

# Individual patient files:
# ID - Unique patient identifier
# CODE - EHR code identifier (note: IDs can have multiple rows for each code corresponding to a different TIME)
# COUNT - Integer count for CODE at time TIME
# TIME - Number of months since first PAH code (note: first PAH code in EHR occurred at TIME=0; codes with TIME<0 excluded from analysis)

## Summary Statistics

- Total Samples: 14305
- Features: codified 

## Demographic Information

- Patient Size: 14305

## Metadata

1. Code: Transformer training pipeline (train.py, eval.py, silver label update scripts)
2. External Data (raw data): Raw EHR extracts from BCH MAPS server, including codified diagnosis (PheCodes), procedures, medications, and registry data.
3. Data (processed / derived from code):
- patient_summary.csv containing gold and silver labels, KOMAP probabilities, registry indicators, and train/validation split
- Patient-level longitudinal codified EHR files formatted for Transformer input
- Silver labels derived from PheCode 415.2 frequency rule (≥2 occurrences)
- FINALPAH labels combining gold and silver sources
4. Report: Associated analyses included in: https://www.nature.com/articles/s41746-026-02406-x

## Traceability 

- Sara extracted original data from BCH MAPS server
- Kim preprocessed data for transformer model

## Contact

Kim Greco

## Key Questions

1. Why is the data interesting, and what are its limitations?
- Enables weakly supervised phenotyping of pulmonary hypertension (PAH) using real-world longitudinal EHR data.
- Combines gold-standard registry labels with scalable silver labels derived from structured EHR codes.
- Limitation: Single-center dataset (BCH), limiting external generalizability.

2. Guide on how to use the dataset?
Use patient_summary.csv to:
- Select training vs validation cohort (training column)
- Choose label type (FINALPAH, FINALPAH_gold, FINALPAH_silver, or probabilistic labels such as KOMAP_prob)
- Restrict to gold-only subset if needed (gold == 1)
Load individual patient files from training/validation directories:
- Aggregate by ID
- Sort by TIME
- Construct sequences of (CODE, COUNT, TIME)
Feed sequences into the Transformer pipeline:
- Map CODE to embeddings
- Use FINALPAH (or probabilistic label) as training target
- Optionally perform iterative silver label updates

3. What are the related datasets 
Subset of BCH EHR data extracted from the MAPS server.