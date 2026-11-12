# Build derived IBD data

## Start here

Use this guide to build a patient list, apply the historical MAJOR cohort filters, and choose the next output. The full MAJOR IBD Project README explains the five study aims and their analysis choices.

## Select the historical MAJOR cohort

1. **Start with 55,651 patients.** Identify patients with diagnostic ICD codes at MGH from January 2013 through February 2025.
2. **Keep 25,921 patients.** Require at least one dose of an IBD drug of interest after diagnosis and at least three visits.
3. **Apply KOMAP phenotyping.** The historical flow retained 21,194 patients: 10,718 with ulcerative colitis (UC) and 10,476 with Crohn’s disease (CD).
4. **For the advanced therapy cohort, require at least one dose of an IBD advanced therapy.** This branch retained 10,610 patients: 6,753 UC and 3,857 CD.

These are historical cohort-flow counts. The three initial steps define the starting MAJOR cohort. Apply further criteria for your study, such as adult age at treatment start or required lookback and follow-up for Aim 1.

## Build and save the derived files

1. Start with the merged codified EHR, identifier mapping, demographics and treatment records listed below. Build a patient list with `EMPI`, `patient_num`, first qualifying IBD diagnosis date and demographics. Attach the KOMAP disease label at the phenotyping step.
2. Build the longitudinal drug history, then record the index date for any IBD drug or for advanced therapy, according to the cohort you are making. The MAJOR README lists separate patient index tables and all-drug-event tables for these two definitions.
3. Review and run the relevant R scripts on the MGB share. They cover how the project went from the full cohort to filtered and saved datasets. Use the script’s input and output paths for the version you are reproducing. Record the filter counts and output filenames when you save a new version.
4. Choose the next branch. For registry outcomes, follow the linkage steps below. For EHR features, use the documented monthly codified, NLP and lab files and align features to the index date for your aim.

### Reuse the existing inputs and outputs

- **Merged codified EHR:** `//SMBgpa.partners.org/asw_mgb$/Xin/IBD/data_IBD_after_merge_05272025.RData`.
- **KOMAP labels:** `//SMBgpa.partners.org/asw_mgb$/Enci/causal_data/7_14/KOMAP_patientnum_disease.csv`. Use the documented `patient_num` and `disease_pred_final` fields.
- **Patient identifier mapping:** `//SMBgpa.partners.org/asw_mgb$/SHARE/NLP/EMPI_to_Patient_num_full_mapping.csv`.

The MAJOR README lists these existing derived files under `//SMBgpa.partners.org/asw_mgb$/Xin/IBD/data/more_sensitivity/`:

| File | Use |
| --- | --- |
| `all_ibd_drug_t0.RDS` | Patient index dates for any IBD drug of interest. |
| `all_ibd_drug_df.RDS` | Longitudinal records for all IBD drugs of interest. |
| `AT_ibd_drug_t0.RDS` | Patient index dates for advanced therapy. |
| `AT_ibd_drug_df.RDS` | Longitudinal advanced therapy records. |
| `demo_data_all.RDS` | Demographics. |

### R scripts and contact

**R scripts:** `//SMBgpa.partners.org/asw_mgb$/Xin/IBD/prep_data/more_sensitivity/`

**Contact for cohort construction:** Xin Xiong.

## Link registry treatment outcomes to EHR

1. Start with the registry patient identifier, treatment and index date. The legacy PRISM treatment-response file uses `patient_num`, `drugsubstudy` and `baseline_date`. The MGH file uses `Patient_num`, `Index treatment (IL23 vs JAK)` and `Date of Start index treatment`.
2. Use the deduplicated `EMPI_to_Patient_num_full_mapping.csv` to align registry and EHR identifiers on the MGB share. Keep unmatched and multiply mapped records for review.
3. Normalize treatment names and classes across the registry and EHR. Require a compatible treatment class and use the same drug for the timing check. The historical Aim 3 workflow used any same-drug EHR occurrence within ±30 days of registry baseline for the broader cohort. Its stricter sensitivity cohort required the earliest same-drug occurrence to be within ±30 days. Review records with prior use or conflicting treatments.
4. Attach the outcomes from the workbook you used. Legacy PRISM has week 14, 30 and 52 fields. The MGH workbook records response at 3 and 12 months. Keep the workbook’s assessment times and response categories in the derived file.
5. Use the registry index date to align the EHR feature windows. Save the linked cohort and review records on the MGB share and record the match rule, exclusions and label definitions used.

**Identifier mapping:** `//SMBgpa.partners.org/asw_mgb$/SHARE/NLP/EMPI_to_Patient_num_full_mapping.csv`

## Sources

- Historical cohort flow supplied by Enci Cai, including the four filter counts above.
- MAJOR IBD Project README, **Useful processed files**, **Aim 1**, **Aim 3** and **End-to-End Execution Steps**.
- IBD registry README for workbook names, column names and outcome timing.
