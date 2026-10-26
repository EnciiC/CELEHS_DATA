AD data and code filepaths
MGB
Raw data:
Codified
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/From_OneDrive/Survival_Analysis_Paper/MGB/Raw_Data/combined_daily.RData
Columns: PatientNum, Start_date, Local_Code, Local_Code_Description, Type
NLP
Raw NLP data (direct NILE output) unavailable
Demographics
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/From_OneDrive/EHR_AD/EHR_Derived/20240703 Consolidated by SV/Demographics/MGB demographics deidentified.csv
Visit/daily level:
Codified
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/Monthly_Counts/MGB/Daily_codified.RData
NLP
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/monthly_NLP/AD/daily_NLP
Monthly level (CALENDAR MONTH):
Codified
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/Monthly_Counts/MGB/Monthly_codified.RData
NLP
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/Monthly_Counts/MGB/NLP
Utilization
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/Monthly_Counts/MGB/Monthly_utl.RData
Code
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/2026-01-30_MGB_monthly_count_generation.R
Survival outcomes
Note: Yuming found an error in Sara’s code for calculation of t0 in UPMC and MGB survival outcomes on 2026-04-06. Sara refreshed data with updated path to code and data listed below, and confirmed the same error does not exist in the KDI data.
Data:
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/MGB_survival_outcomes/2026-04-06_MGB_survival_outcome.csv
Columns: patient_num, date_last_code, date_first_code, date_last_cui, date_first_cui, t0, date_first_nh_code, date_first_nh_code_post_t0, date_death
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/MGB_survival_outcomes/2026-04-06_MGB_all_nh_code_dates.csv
Columns: patient_num, nh_code, nh_code_date
Code:
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/MGB_survival_outcomes/2026-04-06_MGB_survival_outcome_calculation.R
KOMAP
Sara’s: /n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/MGB_regen_KOMAP
Shurthi’s: /n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/From_OneDrive/Survival_Analysis_Paper/UPMC/Intermediate Files/KOMAP Prediction/komap_pred_imputed.csv
Gold standard labels
100 chart reviewed patients: /n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/chart_review
Genetics
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/for_Mengyan/APOE_SNPs.csv
UPMC
Raw data:
Codified
/n/data1/hsph/biostat/celehs/lab/SHARE/UPMC/AD/data_raw/data_codified
Columns are unnamed, but the meanings are: patient_num, common_ontology_code, date, group_code, local_code
NLP
/n/data1/hsph/biostat/celehs/lab/SHARE/UPMC/AD/data_raw/data_NLP
Demographics
/n/data1/hsph/biostat/celehs/lab/SHARE/UPMC/AD/data_raw/ad_demographics.dsv
Visit/daily level:
Codified
/n/data1/hsph/biostat/celehs/lab/SHARE/UPMC/AD/data_table/data_processed/UPMC_AD_2004_to_2023_Codified_rolled_up_data_2023-10-06.csv
Columns are patient_num, start_date, feature_id
Rolled up by Clara/Ratnam, but uses feature_id/group code present in raw data listed above
NLP
/n/data1/hsph/biostat/celehs/lab/SHARE/UPMC/AD/data_table/data_processed/UPMC_AD_2011_to_2021_NLP_processed_data_2023-10-17.csv
Monthly level (CALENDAR MONTH):
Codified
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/Monthly_Counts/UPMC/Monthly_codified.RData
NLP
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/Monthly_Counts/UPMC/Monthly_NLP.RData
Utilization
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/Monthly_Counts/UPMC/Monthly_utl.RData
Code
/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/2026-01-30_UPMC_monthly_count_generation.R
Survival outcomes
Note: Yuming found an error in Sara’s code for calculation of t0 in UPMC and MGB survival outcomes on 2026-04-06. Sara refreshed data with updated path to code and data listed below, and confirmed the same error does not exist in the KDI data.
Data
/n/data1/hsph/biostat/celehs/lab/SHARE/UPMC/AD/data_table/data_processed/Sara/2026-04-06_UPMC_survival_outcome.csv
Columns: patient_num, date_last_code, date_first_code, date_first_cui, date_last_cui, t0, date_first_nh_code, date_first_nh_code_post_t0, date_death
/n/data1/hsph/biostat/celehs/lab/SHARE/UPMC/AD/data_table/data_processed/Sara/2026-04-06_UPMC_all_nh_code_dates.csv
Columns: patient_num, nh_code, nh_code_date
Code
/n/data1/hsph/biostat/celehs/lab/SHARE/UPMC/AD/data_table/data_processed/Sara/2026-04-06_UPMC_survival_outcome_calculation.R
VA (KDI)
Summary of available patients in data created by Jun:
Diagnosis
Medication
Lab
Procedure
NLP
Unique patients (# of files in directory)
905,238
876,729
889,589
904,732
947,142
Patients with PheCode:290.1
64,703
64,408
64,586
64,700
64,670
Monthly feature counts
Original formatting by Jun is per-patient, per- code type (e.g. 1 file per patient for each of {dx, lab, med, proc, nlp}). I didn’t want to make the resulting RData or CSV files too large, so monthly data is still stored per-patient and per- code type, but in headerless CSVs so they can easily be concatenated with bash if desired.
All available features extracted by Jun are included here, for NLP and all code types. Some codes aren’t rolled up to the group code level (e.g. diagnosis still has some codes like “V15.81”) - I have preserved these as they’re presented in the date-level data from Jun.
/mnt/mvpfs/MVP_CORE_OPS/sara/AD/1_monthly_counts/per_patient contains directories dx, lab, med, proc, and nlp. Using the command ls to view the files in these directories will be annoying/overflow the terminal. Use ls -U (option for unsorted) piped to head to view a few files or wc -l to count the files in the directory.
Each directory contains CSVs with no headers containing each patient’s monthly data. All categories have been concatenated to <category>_combined.csv by using the bash command (echo “PatientICN,Year,Month,Code,Count”; cat <category>/*) > <category>_combined.csv
The columns in these files are: PatientICN, year, month, code, count.
There are also the two flavors of healthcare utilization: encounter.days and ICD.count - they have subdirectories in 1_monthly_counts/per_patient. Code to generate these files is at 1_monthly_counts/1_HU.R
Survival outcomes
Used updated nursing home feature list to get dates of first nursing home code/CUI and first nursing home code/CUI following AD diagnosis.
Note that Jun’s raw data doesn’t roll up to common ontology codes, so I used the unprefixed codes to isolate the diagnosis and procedure dates. See my code at 2_survival_outcomes/2_NH_code_extraction.R for more details.
All survival outcomes and demographic information are saved in the same file: 2_survival_outcomes/survival_outcome_data.csv. It’s created using the script 2_survival_outcomes/2_survival_outcome_generation.R.
The survival outcome data has the following columns:
PatientICN, AD_t0, date_last_followup, date_first_nh_code, date_first_nh_code_post_t0, MVPCore_ID, DeathDate, MOB, YOB, sex, race.
Demographics note: exact DOB is unavailable for MVP patients - using MOB, YOB, and DeathDateTime from MVP_Source SQL table - SQL code is saved in 2_survival_outcomes directory
KOMAP
KOMAP was run using codified and NLP features with PheCode:290.11 as the main surrogate, and the patient population is anyone with PheCode:290.1. The input matrix (codified, NLP, and HU before log transformation) is stored at 3_KOMAP/KOMAP_input_feature_matrix.rds, and was created using code at 3_KOMAP/3_Data_organization.R.
Main surrogate: PheCode:290.11
Main CUI: C0002395
Healthcare utilization: encounter.days
KOMAP code: 3_KOMAP/Run_KOMAP.R
(references all data and paths necessary)
KOMAP results: 3_KOMAP/KOMAP_output.RData
Results below are directly from out$pred_prob$pred.cluster, using disease vs no disease labels.
Total patients
Patients predicted AD + (codified features)
Patients predicted AD + (codified + NLP)
N patients with PheCode:290.1)
64703
16867
37709
N patients with PheCode:290.11)
16037
16037
16037
N patients with C0002395/main CUI)
33746
13192
33746
Genetic information
Available in Jun’s data: /mnt/mvpfs/MVP_CORE_OPS/junwen/QC_MAP/1_AD_diseases/dosage1 or 2
Also consult Jun’s documentation: /mnt/mvpfs/MVP_CORE_OPS/junwen/QC_MAP/1_AD_diseases/readMe.txt
Additional notes
Visit-level data:
/mnt/mvpfs/MVP_CORE_OPS/junwen/QC_MAP/patient_level_data_days/<x>_all_ICN
Where <x> is diagnosis, lab, medication, procedure, NLP
Each patient has one CSV file named with the patient’s ICN
Columns: Code, Date
Where Date is in reference to 2000-01-01
Code is at rolled level (PheCode, RXNORM, LOINC/ShortName, CUI (including acronym CUIs), CCS)
Unrolled visit-level data for diagnosis and procedures:
/mnt/mvpfs/MVP_CORE_OPS/junwen/QC_MAP/1_curated_month_counts/diagnosis_all_ICN_rawcodes
Each patient has one CSV named with the patient’s ICN
Columns: Code, Date
Where Date is in reference to 2000-01-01
Codes are unrolled. This data is needed to get the first nursing home codes.