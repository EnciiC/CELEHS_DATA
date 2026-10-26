# IBD Laboratory Monthly Summary

**Owner:** Enci Cai

## Purpose

This dataset combines the three IBD laboratory pulls and summarizes repeated measurements by patient, laboratory, unit, and calendar month.

## Location

- Folder: `//SMBgpa.partners.org/asw_mgb$/SHARE/IBD_lab_data_yunqing/monthly_summary/`
- Processing script: `lab_value_monthly_count.R`
- Main RDS: `IBD_lab_monthly_summary.rds`
- Main CSV: `IBD_lab_monthly_summary.csv`

## Source data

| Source | Identifier | Date field | Value and unit fields |
| --- | --- | --- | --- |
| `datapull_1/final_data.csv` | `PATIENT_NUM` | `START_DATE`, expected as `YYYY-MM-DD` | `NVAL_NUM`, `units`, `value_convert`, `converted_unit` |
| `datapull_2/final_data.csv` | `EMPI` | `Seq_Date_Time`, expected as `M/D/YYYY` or `MM/DD/YYYY` | `Result`, `Reference_Units`, `value_convert`, `converted_unit` |
| `datapull_3/final_data.csv` | `EMPI` | `Seq_Date_Time`, expected as `M/D/YYYY` or `MM/DD/YYYY` | `Result`, `Reference_Units`, `value_convert`, `converted_unit` |

The identifier map is `//SMBgpa.partners.org/asw_mgb$/SHARE/NLP/EMPI_to_Patient_num_full_mapping.csv`.

## Main output

Each row represents one patient-lab-unit-calendar-month combination.

| Column | Description |
| --- | --- |
| `EMPI`, `PATIENT_NUM` | Linked patient identifiers |
| `LAB_NAME` | Albumin, CRP, ESR, FCP, or Hemoglobin |
| `UNITS` | Standardized unit; separate rows are retained for different units |
| `MONTH_START` | First day of the calendar month |
| `YEAR`, `MONTH` | Calendar year and month |
| `N_MEASUREMENTS` | Number of source measurements contributing to the row |
| `MEAN`, `MIN`, `MAX`, `MEDIAN` | Monthly laboratory summaries |

## Current row counts

The loaded monthly dataset contains 1,694,280 rows.

| Laboratory | Monthly rows |
| --- | ---: |
| Albumin | 704,621 |
| CRP | 77,149 |
| ESR | 46,679 |
| FCP | 6,527 |
| Hemoglobin | 859,304 |

These are monthly summary rows, not raw measurement counts or unique-patient counts.

## Dataset coverage and repeated measurements

Across all five laboratories, the dataset contains:

- 1,694,280 patient-lab-unit-month rows;
- 50,826 unique patients;
- 5,511,418 contributing source measurements;
- coverage from August 1988 through March 2025; and
- five laboratory types represented in four distinct units overall. Each individual laboratory uses one unit in the final monthly table.

| Laboratory | Monthly rows | Patients | First month | Last month | Source measurements | Rows with one measurement |
| --- | ---: | ---: | --- | --- | ---: |  ---: |
| Albumin | 704,621 | 48,120 | 1989-02 | 2025-03 | 1,964,162 | 42.8% |
| CRP | 77,149 | 12,842 | 2000-11 | 2024-02 | 245,731 | 16.9% |
| ESR | 46,679 | 9,886 | 1990-06 | 2024-02 | 139,865 | 15.3% |
| FCP | 6,527 | 3,570 | 2018-02 | 2024-02 | 16,911 |33.2% |
| Hemoglobin | 859,304 | 50,573 | 1988-08 | 2025-03 | 3,144,749 | 40.1% |

The yearly coverage table contains 118 laboratory-year combinations. Hemoglobin provides the earliest observations in 1988. Albumin and Hemoglobin extend through March 2025, while CRP, ESR, and FCP currently extend through February 2024.
