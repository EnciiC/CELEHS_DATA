IBD Project Data
Current as of 2026-09-28, created by SM Sweet
2026-09-28: Refreshed extraction of raw codified data (observation_fact table) to include additional columns
2026-09-24: Added descriptions for raw codified data from database, paths to extracted visit_dimension table
Data for this project comes from 3 overlapping sources.
IBD_2020 database: a MSSQL database
IBD_2019_2025_MART and IBD_2019_MART_EXTENDED: RPDR files
Merged RPDR files
IBD_2020
Diagnosis
Medication
Lab
Procedure
Unique patients
40,679
37,636
34,902
39,647
39,850
Unique codes
37,267
30,128
106
21,496
126,476
Min date
1990-01-03
1840-12-31
1990-01-01
1990-01-02
1840-12-31
25% date
2017-01-23
2015-11-09
2015-03-25
2015-09-17
2008-06-06
Median date
2020-08-05
2019-12-05
2019-12-30
2019-10-31
2014-01-31
75% date
2022-10-25
2022-07-12
2022-08-18
2022-06-25
2017-08-24
Max date
2025-03-09
2026-07-22
2025-03-09
2028-09-27
2101-08-27
Codified data
0. Raw Data
IBD_2020 database
Available on Partners MSSQL server MGBSQL0055.partners.org, database IBD_2020
Codified data (observation_fact table) available in RData format in batches split by patients: //SMBgpa.partners.org/asw_mgb$/Sara/IBD/IBD_2020_codified/raw
Data extracted using script: \\SMBGPA.partners.org\asw_mgb$\Sara\IBD\IBD_2020_codified\raw_extraction.R, extracts PATIENT_NUM, ENCOUNTER_NUM, MODIFIER_CD, START_DATE, END_DATE, CONCEPT_CD
Data containing just PATIENT_NUM, CONCEPT_CD, START_DATE (Generated May 2026) available in archive subfolder
Visit dimension table available in RData format in batches split by patients: //SMBgpa.partners.org/asw_mgb$/Sara/IBD/IBD_2020_codified/visit_dimension_table/raw
Data extracted using script: //SMBgpa.partners.org/asw_mgb$/Sara/IBD/IBD_2020_codified/visit_dimension_table/visit_dimension_extraction.R
RPDR sources
Available on SFA: //SMBgpa.partners.org/asw_mgb$/SHARE/IBD_2019_MART_EXTENDED
//SMBgpa.partners.org/asw_mgb$/SHARE/IBD_2019_2025_MART
Available on Eris: /data/aws-eris/IBD_2019_MART_EXTENDED, IBD_2019_2025_MART
1. Processed Data
Day-level data (split into RPDR and database) can be accessed on Eris at /data/aws-eris/Sara/IBD/2026-03-16_Refresh/codified_daily. The merged data can be found in the same directory under merged_daily_data.RDS.
Unique patients
56,704
Unique codes
40,125
Min date
1840-12-31
25% date
2009-09-18
Median date
2015-07-25
75% date
2019-06-14
Max date
2101-08-27
A few details to note:
Find the code I used to generate this data at /data/aws-eris/Sara/IBD/2026-03-16_Refresh/codified_rollup.R
Find the dictionary I used to map at /data/aws-eris/Sara/IBD/2026-03-16_Refresh/codified_daily/dictionary_mapping_v3.4.tsv
I aggregate using a variable called Rollup_Code. Where the local code mapped to a group code, Rollup_Code is set to be the group code. If no group code is available, Local_Ontology_Code is used, and if that is not available the local code is used. This means all codes are preserved in the monthly count, even if they did not have a mapping in the hierarchy.
2. Monthly Count Data
Available on Eris at /data/aws-eris/IBD_DATA_REAGGREGATED/codified_data_monthly.RData.
For the code used to generate this, please reference /data/aws-eris/Sara/IBD/2026-03-16_Refresh/codified_rollup.R
NLP data
0. Raw Data
Notes are stored at the following paths:
/data/aws-eris/IBD_2020_NOTES for the IBD_2020 database (notes were saved directly from the database and are grouped by patient number)
/data/aws-eris/IBD_2019_2025_MART for RPDR
/data/aws-eris/IBD_2019_MART_EXTENDED for RPDR
1. NILE results
All files were run in NILE. However, some files are not clinical notes and are excluded during postprocessing. You can find the NILE results for the excluded documents at:
IBD_2019_MART: /data/aws-eris/Sara/IBD_NLP_result/IBD_2019_MART/excluded
IBD_2019_2025_MART: /data/aws-eris/Sara/IBD_NLP_result/IBD_2019_2025_MART/excluded
You can find the NILE results in the subdirectories of /data/aws-eris/Sara/IBD_NLP_result/vedo_acronym, where there is one directory per data source. This data contains “vedo” as an acronym, AB00vedo, which can then be combined with the main vedolizumab CUI by the analyst.
The dictionary used can be found at /data/aws-eris/Sara/refactored-nile-processing-main/NILE/2026-05-26_IBD_dict_w_vedo_acr.txt. It is the same as the dictionary 2026-03-10_IBD_dict_w_drugs_and_brands.txt with the exception of the first line for the vedo acronym CUI.
2. Processed Data
Data breakdown per data source following NILE run
IBD_2020
IBD_2019_MART
IBD_2019_2025_MART
Total
Unique patients
39,173
20,999
32,174
55,436
Minimum date
1841-01-02
2019-01-01
1990-01-02
1841-01-02
25% date
2011-07-06
2020-02-11
2019-01-17
2015-07-06
Median date
2015-12-31
2021-08-20
2021-08-04
2019-07-23
75% date
2018-07-18
2022-12-09
2023-07-21
2022-08-27
Maximum date
6466-05-01
2024-04-02
2025-04-15
6466-05-01
3. Monthly Count Data
Monthly count data is stored at /data/aws-eris/IBD_DATA_REAGGREGATED/NLP_data_monthly.RData, with code used to process the data at /data/aws-eris/Sara/IBD/2026-03-16_Refresh/2026-03-16_NLP_Processing.R