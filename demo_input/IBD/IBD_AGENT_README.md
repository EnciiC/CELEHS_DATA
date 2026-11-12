# IBD agent outputs

## Overview

The endoscopy scoring agent has a documented output managed by Thomas Charlon. The chart review agent for treatment response is listed here for future documentation.

## Endoscopy agent output

**Managed by:** Thomas Charlon.

The CSV contains endoscopy dates, scores, high/low labels and a flag. The related registry resource is **PRISM endoscopy scores**, which also includes endoscopy dates, SES-CD and modified Baron scores. The agent uses `EMPI`; the PRISM workbook uses `patient_num`. Confirm the identifier mapping, date matching and handling of multiple procedures before comparing scores across files.

| Column | Meaning | Type |
| --- | --- | --- |
| `EMPI` | Patient identifier used in the source system. The sample uses generated identifiers. | Identifier |
| `dateofendoscopy` | Endoscopy date in yyyy-mm-dd format. | Date |
| `sescd` | Simple Endoscopic Score for Crohn’s Disease (SES-CD). Observed values range from 0 to 49. | Integer or blank |
| `binary_sescd` | High or low label for SES-CD. | Category or blank |
| `low` | Field named low in the output. Its definition and type are pending. | Pending |
| `high` | Field named high in the output. Its definition and type are pending. | Pending |
| `binary_low` | High or low label from the field named low. The rule is pending. | Category |
| `binary_high` | High or low label from the field named high. The rule is pending. | Category |
| `flagged` | TRUE or FALSE flag. The condition that triggers it is pending. | Boolean |
| `modifiedbaronsscore` | Modified Baron endoscopy score. Observed scores are 0, 1, 2 and 3. | Integer or blank |
| `binary_mbs` | High or low label for the modified Baron score. | Category or blank |

## Location

```text
//eristwofs.partners.org/ASW-ERIS/agent_extdata/
```

Source file: `endoscopy_agent_results_final.csv`.

## Output summary

The supplied frequency tables count rows. Four complete tables sum to 47,847 rows each.

| Column | High | Low | Blank |
| --- | ---: | ---: | ---: |
| `binary_sescd` | 6,273 | 17,853 | 23,721 |
| `binary_low` | 9,517 | 38,330 | 0 |
| `binary_high` | 15,385 | 32,462 | 0 |
| `binary_mbs` | 7,665 | 16,056 | 24,126 |

`flagged` is FALSE in 41,977 rows and TRUE in 5,870 rows. The supplied modified Baron score counts are 11,286 for score 0, 4,770 for 1, 6,564 for 2 and 1,101 for 3.

## Chart review agent for treatment response

This agent’s related registry files are the **MGH treatment-response registry** and the **Legacy PRISM treatment-response registry**. MGH records response at 3 and 12 months. Legacy PRISM includes week 14, 30 and 52 remission fields. The agent’s output location, columns and review method will be added when documented.

## Synthetic examples

The sample contains 100 generated rows with the same 11 columns. It shows file structure. The `low` and `high` fields are blank while their definitions are pending. The binary labels and flags are illustrative values.
