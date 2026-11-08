# IBD genetic and microbiome scores

## Location

```text
//SMBgpa.partners.org/asw_mgb$/Xin/IBD/data/snp_data/
```

## Overview

`deID scores.xlsx` contains score tables for the PRISM and Biobank cohorts. The PRISM worksheet includes genetic risk scores and microbiome scores. The Biobank worksheet includes PRS fields for IBD and other traits.

Documentation source: column names and descriptions supplied by Enci Cai on November 8, 2026, including a colleague's description of the PRISM scores.

Data contact: ____________________

## Files

| File | Contents |
| --- | --- |
| `deID scores.xlsx` | PRISM genetic/microbiome scores and Biobank PRS fields. |
| `Biobank_snp_merged.RDS` | |
| `GRS_Biobank_merged.RDS` | |
| `ibd_gwas.RDS` | |
| `snp_dict_merge.RDS` | |

## PRISM worksheet

| Column | Description |
| --- | --- |
| `dx` | IBD diagnosis: UC or CD. |
| `patient_num` | Patient identifier in this workbook. |
| `ibd_score_genetic` | IBD genetic risk score. |
| `uc_score_genetic` | Ulcerative colitis genetic risk score. |
| `cd_score_genetic` | Crohn's disease genetic risk score. |
| `hcindex_microbiome` | Microbiome score. Meaning of `hcindex`: ____________________ |
| `ibdindex_microbiome` | IBD-related microbiome score. Definition: ____________________ |

The reported genetic-score examples include `0.00700` and `-0.0007`. The microbiome-score values were described as lying between -1 and 1, with examples such as `0.7` and `-0.5`. These are descriptions supplied for documentation, rather than calculated full-file summary statistics.

Genetic and microbiome score methods, scaling and interpretation: ____________________

## Biobank worksheet

The columns are:

```text
patient_num
disease
disease2
pc1
pc2
pc3
pc4
pc5
pc6
pc7
pc8
pc9
pc10
prs_anxiety
prs_depression
prs_parkinson
prs_metabolic
prs_celiac
prs_psoriasis
prs_ra
prs_t1dm
prs_colorectal_cancer
prs_nafld
prs_mi
prs_hs
prs_psc
prs_crohns
prs_uc
prs_ibd
prs_smoking_initiation
prs_smoking_cessation
prs_age_of_smoking
prs_drink_per_week
prs_cigarettes_per_day
```

The main IBD-related scores are:

| Column | Description |
| --- | --- |
| `prs_crohns` | Crohn's disease polygenic risk score. |
| `prs_uc` | Ulcerative colitis polygenic risk score. |
| `prs_ibd` | IBD polygenic risk score. |

`patient_num` is the patient identifier. Definitions of `disease`, `disease2`, and `pc1`–`pc10`: ____________________

Many Biobank cells have missing values. Score values include both positive and negative numbers. Retain missing values as missing; zero is a distinct numeric value.

PRS calculation method, source GWAS and scaling: ____________________

## Linking to EHR

Both worksheets contain `patient_num`. Confirm the identifier mapping, patient overlap and duplicate-record rules before linking these tables to EHR.

Mapping file or linkage script: ____________________

## Additional information

- Patient counts and overlap between worksheets: ____________________
- Microbiome sampling dates and underlying data location: ____________________
- Processing scripts and related papers: ____________________
- Access requirements: ____________________
