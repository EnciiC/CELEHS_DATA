MGB Biobank Data for CELEHS lab members

Documentation created by SM Sweet, September 2026

On Eris/Partners

Main project path: /data/vbio-methodsdev/SHARE/BIOBANK/2025

Codified data

Raw data

Not available on Eris, just in MSSQL database

Processed data

DAILY codified data is available in a series of batched CSV files according to the type of code contained.

Parent directories: /data/vbio-methodsdev/SHARE/BIOBANK/2025/Processed_Data/codified/rolled_<TYPE>_Group_Code, where TYPE is one of <Lab, Med, Phecode, Proc>

|  | Diagnosis | Medication | Lab | Procedure |
| --- | --- | --- | --- | --- |
| Unique patients | 156735 | 151617 | 148955 | 155827 |
| Unique codes | 1868 | 2662 | 7276 | 248 |
| Min date | 1994-01-01 | 1994-01-01 | 1994-01-01 | 1994-01-02 |
| Median date | 2018-10-30 | 2017-01-23 | 2017-09-13 | 2017-04-17 |
| Max date | 2025-05-06 | 2915-08-16 | 2025-05-06 | 2025-02-28 |

NLP data

Raw data

Raw NILE output is available per RPDR note file at: Raw_Data/Raw_NILE_output

Processed data

Monthly unrolled data is available in patient batches at: /data/vbio-methodsdev/SHARE/BIOBANK/Processed_Data/cleaned_unrolled

| Unique patients | 154954 |
| --- | --- |
| Unique CUIs (including acronyms) | 296265 |
| Min date | 1976-03 |
| Median date | 2005-12 |
| Max date | 2025-07 |

Demographics

Demographic information for 2025 patients: Processed_Data/Demographic/Biobank2025_Demographic_RaceFeldman_CD_ZIP_Dth_Cnst_hcu_addr_n159763_2026_0506_sq.csv

Columns: PATIENT_NUM, BIRTH_DATE, SEX_CD, RACE_CD, subject_id, Race_Cd_updated, EMPI, zip_cd, VITAL_STATUS_Death_Flag, Death_date, Consent_date, race_American_Indian_Alaska_Native, race_Native_Hawaiian_Pacific_Islander, race_White, race_Other, race_Declined, race_Unknown, race_Unavailable, race_Not_Given, race_NOT_REPORTED, hispanic, race_feldman, hcu, empi, Address, Address2, City, State, Zip, hypertension, diabetes, cad, hf, ra

| Unique patients | 157963 |
| --- | --- |
| Min BIRTH_DATE | 1912-11-06 |
| Median BIRTH_DATE | 1962-12-18 |
| Max BIRTH_DATE | 2021-12-03 |

On O2

Pending DUA acceptance between HMS and BWH.
