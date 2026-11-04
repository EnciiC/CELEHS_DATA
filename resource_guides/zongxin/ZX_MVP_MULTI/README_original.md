# MVP multi-ancestry variant–phenotype matrices (AFR/AMR/EAS/EUR)

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `MVP multi-ancestry variant–phenotype matrices (AFR/AMR/EAS/EUR)`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

The current MVP source-family directory containing variant–phenotype matrices and summaries across AFR, AMR, EAS, and EUR ancestries.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/SHARE/From_JunWen/MVP/Variant_phenotype_correlation_matrix
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Canonical source root is the O2 directory registered above.
- Top-level objects include `MVP_data_readMe.txt`, `PheMART`, `Phecode_residual_Ybinary2_summary`, `V_summary`, `Variant_lab_matrix`, `Variant_phenotype_matrix_Ybinary2`, and `Variant_phenotype_matrix_Ylog`.
- Metadata-only verification found ancestry-labelled paths for AFR, AMR, EAS, and EUR; no HIS or SAS ancestry label was observed.
- This source-family coverage does not prove that every preserved CRAFT runtime or model used all four ancestries.

## Access and authority boundary

- MVP/VA/KDI data-use and recipient rules apply. O2 path visibility does not establish transfer or post-Harvard authority.
- No personal source-data copy is claimed for this family.
- Do not expose participant-level, cell-level, or restricted summary-statistic content through GitHub, Notion, chat, or an unapproved destination.

## How to use

1. Read the source `MVP_data_readMe.txt` and identify the required ancestry, matrix role, and phenotype representation before opening large payloads.
2. Keep source-family ancestry coverage separate from the exact ancestry used by a particular model/run.
3. Use the registered private `generel_v2` repository for downstream task construction, but verify the exact experiment/code binding before making a reproduction claim.
4. Record the selected ancestry and exact files in any new analysis manifest.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private repository `z-x-yang/generel_v2` is preserved. The registry does not establish one exact generation commit for the entire multi-ancestry source family; bind the exact downstream experiment before use.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- Verification was metadata-only: directories and filenames were inspected, not matrix contents.
- The source family is multi-ancestry, while specific current/historical CRAFT implementations may still bind only a subset such as EUR.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- Metadata receipt: `mvp-multi-ancestry-o2-metadata-readback-20260816-v1.json` (directory/filename metadata only).
- The Google Sheet and Google Doc identities were read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
