# IBD registry data from Ashwin

## Location

```text
//SMBgpa.partners.org/asw_mgb$/SHARE/Registry_data_by_Ashwin/
```

## Overview

Three registry workbooks contain PRISM endoscopy scores and treatment-response information. The MGH and legacy treatment-response files relate to the Aim 3 EHR phenotyping work.

Documentation prepared from the column lists, labels and frequency tables supplied by Enci Cai on November 8, 2026. Aim 3 linkage instructions come from Enci’s existing MAJOR IBD Project README.

Data contact: Ashwin. Contact details: ____________________

## Files

| File | Contents | Columns |
| --- | --- | --- |
| `endo score PRISM EMPI merged July 2025_deID.xlsx` | PRISM diagnosis, disease classification, endoscopy dates and clinical/endoscopic activity scores. | 11 |
| `MGH_data-LLM_project__EMPI_and_patientnum.xlsx` | Index treatment and treatment-start date, baseline endoscopy, clinical response at 3 and 12 months, and post-treatment endoscopy. | 8 |
| `traetment response_for informatics_nodupl_mergedpatient_num_forXin_Feb6.xlsx` | Registry treatment and baseline information, demographic and medication fields, follow-up measures, and clinical-status/composite fields used in earlier Aim 3 work. | 94 |

## 1. PRISM endoscopy scores

Source file: `endo score PRISM EMPI merged July 2025_deID.xlsx`

This file includes diagnosis, age-at-diagnosis group, disease location/behavior/extent, endoscopy date and activity scores. `dateofendoscopy` uses `yyyy-mm-dd`.

| Column | Meaning | Type |
| --- | --- | --- |
| `patient_num` | Patient identifier in the registry file. | Identifier |
| `dx` | Diagnosis: UC or CD. | Category |
| `cdageatdiagnosisa` | Age at diagnosis: A1 (16 years or younger), A2 (17 to 40 years), A3 (Over 40 years), or N/A. | Category |
| `cdlocationlpriortofirstsurgery` | Recorded disease location before first surgery; preserve the supplied L categories, 0 and N/A. | Category |
| `cdbehaviorb` | Recorded disease behavior; includes B1/B2/B3, perianal variants, 0 and N/A. | Category |
| `ucextente` | UC extent: E1 (Ulcerative proctitis), E2 (Left-sided UC), E3 (Extensive UC / Pancolitis), or N/A. | Category |
| `dateofendoscopy` | Endoscopy date, supplied as yyyy-mm-dd. | Date |
| `sescd` | Simple Endoscopic Score for Crohn’s Disease (SES-CD). Reported observed values 0–29, mostly 0, with missing values. | Integer or missing |
| `modifiedbaronsscore` | Recorded modified Baron score. Values and coding have not yet been supplied. | Not supplied |
| `hbi` | Harvey-Bradshaw Index (HBI), a Crohn’s disease clinical activity score. Reported observed values 0–19, with possible missing values. | Integer or missing |
| `sccai` | Simple Clinical Colitis Activity Index (SCCAI), a UC clinical activity score. Reported observed values 0–12, with possible missing values. | Integer or missing |

The reported score ranges are observed examples from this file, not universal limits of the scoring systems. The supplied `modifiedbaronsscore` values have not yet been described.

The complete supplied age, location, behavior and extent labels and frequencies are in [SOURCE_SUMMARIES.md](Registry_data_by_Ashwin/SOURCE_SUMMARIES.md). Those four supplied tables each sum to 1,422 category entries.

## 2. MGH treatment-response registry

Source file: `MGH_data-LLM_project__EMPI_and_patientnum.xlsx`

This file records index treatment, its start date, baseline and post-treatment endoscopy, and clinical response at 3 and 12 months. The supplied response categories are Clinical remission, No response and Partial clinical response.

| Column | Meaning | Type |
| --- | --- | --- |
| `Patient_num` | Patient identifier; retain the capital P in Patient_num. | Identifier |
| `Index treatment (IL23 vs JAK)` | Index treatment: Risankizumab, Tofacitinib or Upadacitinib. | Category |
| `Date of Start index treatment` | Index-treatment start date, yyyy-mm-dd. | Date |
| `Findings on baseline endoscopy (within 6 months prior to start)` | Baseline endoscopy findings within six months before treatment: Mild, Moderate to severe or Normal. | Category |
| `clinical response at 3 months` | Three-month response: Clinical remission, No response or Partial clinical response. | Category |
| `clinical response at 12 months` | Twelve-month response, using the same three supplied categories. Separate 12-month frequencies were not supplied. | Category |
| `endoscopic severity at first endoscopy after therapy start` | Severity at the first endoscopy after therapy begins: Mild, Moderate to severe or Normal. | Category |
| `Date of scope` | Scope date, yyyy-mm-dd. | Date |

The supplied treatment frequencies total 337 entries. The three-month response frequencies total 325 entries. The 12-month categories were supplied as the same categories, but their separate counts were not supplied.

## 3. Legacy PRISM treatment-response registry

Source file: `traetment response_for informatics_nodupl_mergedpatient_num_forXin_Feb6.xlsx`

The main fields for Aim 3 are `patient_num`, `prismid`, `drugsubstudy`, `baseline_date`, `dx`, and `wk14_remis` / `wk30_remis` / `wk52_remis`. The supplied treatment frequencies total 461 entries. Diagnosis includes UC, CD and a few IC entries.

The raw remission fields contain clinical outcomes and statuses such as a missing visit, no note, stopped treatment or a follow-up not yet reached. Preserve their spelling and capitalization. They are not binary remission indicators.

This file contains `week54_*` measurement columns and separate `wk52_remis` / `week52_composite` columns. Keep those time labels unchanged.

| Column | Meaning | Type |
| --- | --- | --- |
| `patient_num` | Patient identifier; retain the lower-case column name. | Identifier |
| `prismid` | PRISM registry identifier. | Identifier |
| `drugsubstudy` | Registry treatment code: ADA, IFX, RIS, TOFA, UPA, USK or VEDO. | Category |
| `baseline_date` | Registry treatment-baseline date, yyyy-mm-dd. | Date |
| `sex` | Sex field; response coding to be supplied. | Not supplied |
| `hispanicorlatinoorigin` | Hispanic/Latino-origin field; response coding to be supplied. | Not supplied |
| `race` | Race field; response coding to be supplied. | Not supplied |
| `ageatdiagnosisa` | Age at diagnosis group: A1 (16 years or younger), A2 (17 to 40 years), A3 (Over 40 years). | Category |
| `locationlpriortofirstsurgery` | Disease-location field before first surgery; source coding to be supplied for this file. | Not supplied |
| `behaviorb` | Disease-behavior field; source coding to be supplied for this file. | Not supplied |
| `extente` | Disease-extent field; source coding to be supplied for this file. | Not supplied |
| `dx` | Diagnosis: UC, CD and a few IC entries. Definition of IC to be confirmed. | Category |
| `doesthesubjecthaveanyotherimmune` | Other immune-condition field; confirm the full question and response coding. | Not supplied |
| `hasthesubjecteverhadbowelresecti` | Bowel-resection-history field; confirm the full question and response coding. | Not supplied |
| `delzicoloralmesalamine` | Mesalamine (Delzicol) medication field; response coding and timing to be supplied. | Not supplied |
| `asacolmesalamine` | Mesalamine (Asacol) medication field; response coding and timing to be supplied. | Not supplied |
| `pentasamesalamine` | Mesalamine (Pentasa) medication field; response coding and timing to be supplied. | Not supplied |
| `lialdamesalamine` | Mesalamine (Lialda) medication field; response coding and timing to be supplied. | Not supplied |
| `aprisomesalamine` | Mesalamine (Apriso) medication field; response coding and timing to be supplied. | Not supplied |
| `colazalbalsalazide` | Balsalazide (Colazal) medication field; response coding and timing to be supplied. | Not supplied |
| `sulfasalazineazulfidine` | Sulfasalazine (Azulfidine) medication field; response coding and timing to be supplied. | Not supplied |
| `dipentumolsalazine` | Olsalazine (Dipentum) medication field; response coding and timing to be supplied. | Not supplied |
| `prednisone` | Prednisone medication field; response coding and timing to be supplied. | Not supplied |
| `entocortbudesonide` | Budesonide (Entocort) medication field; response coding and timing to be supplied. | Not supplied |
| `ucerisbudesonideer` | Budesonide ER (Uceris) medication field; response coding and timing to be supplied. | Not supplied |
| `solumedrolmedrol` | Solu-Medrol/Medrol medication field; response coding and timing to be supplied. | Not supplied |
| `ivsteroids` | Intravenous steroids medication field; response coding and timing to be supplied. | Not supplied |
| `cortenemascortifoamproctofoam` | Cortenema/Cortifoam/Proctofoam medication field; response coding and timing to be supplied. | Not supplied |
| `azathioprineimuranazasan` | Azathioprine (Imuran/Azasan) medication field; response coding and timing to be supplied. | Not supplied |
| `methotrexate` | Methotrexate medication field; response coding and timing to be supplied. | Not supplied |
| `mercaptopurinepurinethol6mp` | Mercaptopurine (Purinethol/6-MP) medication field; response coding and timing to be supplied. | Not supplied |
| `ozanimodzeposia` | Ozanimod (Zeposia) medication field; response coding and timing to be supplied. | Not supplied |
| `xeljanztofacitinib` | Tofacitinib (Xeljanz) medication field; response coding and timing to be supplied. | Not supplied |
| `rinvoqupadacitinib` | Upadacitinib (Rinvoq) medication field; response coding and timing to be supplied. | Not supplied |
| `remicadeinfliximab` | Infliximab (Remicade) medication field; response coding and timing to be supplied. | Not supplied |
| `humiraadalimumab` | Adalimumab (Humira) medication field; response coding and timing to be supplied. | Not supplied |
| `cimziacertalizumab` | Cimzia field as named in the source header medication field; response coding and timing to be supplied. | Not supplied |
| `tysabrinatalizumab` | Natalizumab (Tysabri) medication field; response coding and timing to be supplied. | Not supplied |
| `simponigolimumab` | Golimumab (Simponi) medication field; response coding and timing to be supplied. | Not supplied |
| `entyviovedolizumab` | Vedolizumab (Entyvio) medication field; response coding and timing to be supplied. | Not supplied |
| `stelaraustekinumab` | Ustekinumab (Stelara) medication field; response coding and timing to be supplied. | Not supplied |
| `skyrizirisankizumab` | Risankizumab (Skyrizi) medication field; response coding and timing to be supplied. | Not supplied |
| `whatisthesubjectscurrentsmokings` | Smoking-status field; confirm the full question and response coding. | Not supplied |
| `heightcm` | Height field labeled in centimetres; source value format to be supplied. | Numeric format not supplied |
| `weightkg` | Weight field labeled in kilograms; source value format to be supplied. | Numeric format not supplied |
| `baseline_crp` | Baseline C-reactive protein (CRP) field; units or score coding to be supplied. | Numeric format not supplied |
| `baseline_hct` | Baseline Hematocrit field; units or score coding to be supplied. | Numeric format not supplied |
| `baseline_hgb` | Baseline Hemoglobin field; units or score coding to be supplied. | Numeric format not supplied |
| `baseline_esr` | Baseline Erythrocyte sedimentation rate (ESR) field; units or score coding to be supplied. | Numeric format not supplied |
| `baseline_wbc` | Baseline White blood cell count field; units or score coding to be supplied. | Numeric format not supplied |
| `baseline_plt` | Baseline Platelet count field; units or score coding to be supplied. | Numeric format not supplied |
| `baseline_alb` | Baseline Albumin field; units or score coding to be supplied. | Numeric format not supplied |
| `baseline_hbi_total` | Baseline Harvey-Bradshaw Index (HBI) total field; units or score coding to be supplied. | Numeric format not supplied |
| `baseline_sibdq_total` | Baseline Short Inflammatory Bowel Disease Questionnaire (SIBDQ) total field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_crp` | Week 14 C-reactive protein (CRP) field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_hct` | Week 14 Hematocrit field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_hgb` | Week 14 Hemoglobin field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_esr` | Week 14 Erythrocyte sedimentation rate (ESR) field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_wbc` | Week 14 White blood cell count field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_plt` | Week 14 Platelet count field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_alb` | Week 14 Albumin field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_hbi_total` | Week 14 Harvey-Bradshaw Index (HBI) total field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_sccai_total` | Week 14 Simple Clinical Colitis Activity Index (SCCAI) total field; units or score coding to be supplied. | Numeric format not supplied |
| `week14_sibdq` | Week 14 Short Inflammatory Bowel Disease Questionnaire (SIBDQ) field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_crp` | Week 30 C-reactive protein (CRP) field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_hct` | Week 30 Hematocrit field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_hgb` | Week 30 Hemoglobin field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_esr` | Week 30 Erythrocyte sedimentation rate (ESR) field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_wbc` | Week 30 White blood cell count field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_plt` | Week 30 Platelet count field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_alb` | Week 30 Albumin field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_hbi` | Week 30 Harvey-Bradshaw Index (HBI) field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_sccai` | Week 30 Simple Clinical Colitis Activity Index (SCCAI) field; units or score coding to be supplied. | Numeric format not supplied |
| `week30_sibdq` | Week 30 Short Inflammatory Bowel Disease Questionnaire (SIBDQ) field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_crp` | Week 54 C-reactive protein (CRP) field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_hct` | Week 54 Hematocrit field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_hgb` | Week 54 Hemoglobin field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_esr` | Week 54 Erythrocyte sedimentation rate (ESR) field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_wbc` | Week 54 White blood cell count field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_plt` | Week 54 Platelet count field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_alb` | Week 54 Albumin field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_hbi` | Week 54 Harvey-Bradshaw Index (HBI) field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_sccai` | Week 54 Simple Clinical Colitis Activity Index (SCCAI) field; units or score coding to be supplied. | Numeric format not supplied |
| `week54_sibdq` | Week 54 Short Inflammatory Bowel Disease Questionnaire (SIBDQ) field; units or score coding to be supplied. | Numeric format not supplied |
| `bmi_bl` | Baseline BMI field; calculation and source value format to be supplied. | Numeric format not supplied |
| `wk14_remis` | Week-14 registry clinical status; retain every supplied label, including non-assessment statuses. | Category |
| `wk30_remis` | Week-30 registry clinical-status field; categories were not supplied. | Not supplied |
| `wk52_remis` | Week-52 registry clinical status; retain every supplied label, including non-assessment statuses. | Category |
| `endo_date` | Endoscopy-date field; exact source representation to be supplied. | Date format not supplied |
| `crohns` | Crohn-related field; exact definition and coding to be supplied. | Not supplied |
| `week14_composite` | Week-14 composite-outcome field; definition and coding to be supplied. | Not supplied |
| `week52_composite` | Week-52 composite-outcome field; definition and coding to be supplied. | Not supplied |
| `week30_composite` | Week-30 composite-outcome field; definition and coding to be supplied. | Not supplied |
| `endo_remission` | Endoscopic-remission field; cutoff and coding to be supplied. | Not supplied |

## Relationship to Aim 3

The existing MAJOR IBD Project README describes linking clinician registry outcomes to EHR, constructing codified/NLP features and fitting separate CD and UC phenotyping models. It reports work using penalized logistic regression, random forest and XGBoost.

The two documented clinical-outcome comparisons were:

1. Remission versus no response.
2. Remission or partial response versus no response.

For the MGH file, the stated comparisons correspond to:

| Comparison | Positive category | Negative category |
| --- | --- | --- |
| Remission versus no response | Clinical remission | No response |
| Remission or partial response versus no response | Clinical remission or Partial clinical response | No response |

Partial clinical response is separate from the first stated comparison. For the legacy file, confirm the approved recoding of Response, No remission, LOR and other statuses before constructing those outcomes. Definitions of `week14_composite`, `week30_composite`, `week52_composite` and `endo_remission` still need to be supplied.

### EHR linkage

The existing Aim 3 README recommends:

1. Use the registry `baseline_date` as the treatment index. The corresponding index-date field in the supplied MGH file is `Date of Start index treatment`.
2. Map identifiers to `EMPI` and `patient_num` using a deduplicated mapping. Confirm that `Patient_num` in the MGH file and `patient_num` in the other files use the intended EHR identifier system.
3. Normalize registry and EHR treatment labels with the project’s approved treatment mapping.
4. Use any same-drug EHR occurrence within ±30 days for the broader linked cohort, and the earliest same-drug occurrence within ±30 days for the stricter sensitivity cohort.
5. Retain unmatched, multiply mapped, prior-use and conflicting-treatment records for review.

Documented identifier mapping:

```text
//SMBgpa.partners.org/asw_mgb$/SHARE/NLP/EMPI_to_Patient_num_full_mapping.csv
```

Documented Aim 3 processing folder:

```text
//SMBgpa.partners.org/asw_mgb$/Enci/Aim 3 phenotyping/
```

### File versions

The earlier Aim 3 README refers to an MGH filename ending `patientnum (2).xlsx`, stored under Enci’s folder, and a 338-patient analysis. The newly supplied file has no `(2)` suffix and is documented under `SHARE/Registry_data_by_Ashwin`. Its treatment table contains 337 entries. Keep the files and their summaries separate until their version relationship is confirmed.

The older project README also uses week-14/week-52 language, while the newer MGH headers specify 3 and 12 months. Use each file’s recorded assessment labels and confirm their time-window correspondence.

## Fake data for the local demo

**All generated sample rows are FAKE DATA.** Each example CSV contains 100 generated rows, preserves the supplied column names and order, and uses `SYN_` identifiers. File-specific identifiers keep the examples from implying real overlap between cohorts.

| Folder | Fake CSV | Dictionary |
| --- | --- | --- |
| endo_scores | [endo score PRISM EMPI merged July 2025_deID_fake_data.csv](Registry_data_by_Ashwin/endo_scores/endo%20score%20PRISM%20EMPI%20merged%20July%202025_deID_fake_data.csv) | [Column / Meaning / Type](Registry_data_by_Ashwin/endo_scores/column_dictionary.csv) |
| mgh_treatment_response | [MGH_data-LLM_project__EMPI_and_patientnum_fake_data.csv](Registry_data_by_Ashwin/mgh_treatment_response/MGH_data-LLM_project__EMPI_and_patientnum_fake_data.csv) | [Column / Meaning / Type](Registry_data_by_Ashwin/mgh_treatment_response/column_dictionary.csv) |
| legacy_treatment_response | [traetment response_for informatics_nodupl_mergedpatient_num_forXin_Feb6_fake_data.csv](Registry_data_by_Ashwin/legacy_treatment_response/traetment%20response_for%20informatics_nodupl_mergedpatient_num_forXin_Feb6_fake_data.csv) | [Column / Meaning / Type](Registry_data_by_Ashwin/legacy_treatment_response/column_dictionary.csv) |

The legacy fake file keeps all 94 columns. Fields with unspecified coding are blank, including the medication/lab fields, `wk30_remis` and composite variables. `modifiedbaronsscore` is also blank. The fake values illustrate structure and do not reproduce the source distributions. Generation choices are recorded in [GENERATION_NOTES.md](Registry_data_by_Ashwin/GENERATION_NOTES.md).

### Read a fake CSV in R

```r
x <- read.csv("path/to/the_fake_data.csv", check.names = FALSE,
              stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM",
              na.strings = "")
```

Keep literal `N/A` labels separate from blank/NA cells. Zero is a value, not a missing-value code unless the source codebook explicitly defines it that way.

## Adding another registry file

Add its exact filename/path, purpose, row unit, identifier fields, date basis, column names and meanings, outcome categories and linkage instructions. Record its version and the scripts used to prepare it. Keep new raw labels intact until their recoding has been reviewed.

Patient counts, unique-patient overlap, full date coverage and confirmed row uniqueness: ____________________

## Term references

Clinical index names can be checked against [SES-CD development](https://www.giejournal.org/article/S0016-5107%2804%2901878-4/abstract), [Harvey and Bradshaw](https://pubmed.ncbi.nlm.nih.gov/6102236/) and [SCCAI development](https://gut.bmj.com/content/43/1/29). These references explain terminology; the supplied file ranges and counts above come from Enci’s description.