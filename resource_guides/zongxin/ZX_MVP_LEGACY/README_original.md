# Legacy MVP HARE/PheWAS summary-statistics benchmark

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `Legacy MVP HARE/PheWAS summary-statistics benchmark`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

Legacy MVP HARE/PheWAS summary-statistics and phenotype-mapping files retained as a historical benchmark and source dependency.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/SHARE/biollm/gwPheWAS_HARE/Merged_PheCodes.csv; /n/data1/hsph/biostat/celehs/lab/SHARE/biollm/gwPheWAS_HARE/x_str.csv
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Registered files: `Merged_PheCodes.csv` and `x_str.csv` at the O2 paths below.
- Fresh sizes: 1,214,887,929 bytes for `Merged_PheCodes.csv` and 71,409 bytes for `x_str.csv`.
- This benchmark is distinct from the current AFR/AMR/EAS/EUR MVP source family.

## Access and authority boundary

- Internal VA/KDI/MVP lineage and the applicable data-use rules apply.
- No personal or new broad handoff copy is claimed.
- Do not infer redistribution authority from summary-statistics format or O2 readability.

## How to use

1. Use this only when a historical HARE/PheWAS benchmark or its phenotype mapping is explicitly required.
2. Record which of the two files and which fields were consumed.
3. Do not substitute it for the current multi-ancestry MVP matrices or the UKB-derived signed-correlation matrices.
4. Verify the exact downstream code/config binding in `generel_v2` before comparing against current results.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private repository `z-x-yang/generel_v2` is preserved; bind the exact historical experiment/config before claiming reproducibility.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- Exact upstream release, steward, and derivation lineage are not fully recovered in this handoff.
- No post-Harvard personal data copy is claimed.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/reference-dependencies.md`.
- Fresh path/size metadata were reconciled on 2026-08-14; the final registry path was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
