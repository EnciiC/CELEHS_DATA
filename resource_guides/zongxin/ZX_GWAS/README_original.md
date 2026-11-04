# NHGRI–EBI GWAS Catalog association releases (e109/e110)

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `NHGRI–EBI GWAS Catalog association releases (e109/e110)`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

Two exact NHGRI–EBI GWAS Catalog association-release files used as public reference data.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/SHARE/geno_pheno/gwas/gwas_catalog_v1.0-associations_e109_r2023-04-24.tsv; /n/data1/hsph/biostat/celehs/lab/SHARE/geno_pheno/gwas/gwas_catalog_v1.0-associations_e110_r2023-10-29.tsv
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Release e109: `gwas_catalog_v1.0-associations_e109_r2023-04-24.tsv`; 324,149,743 bytes.
- Release e110: `gwas_catalog_v1.0-associations_e110_r2023-10-29.tsv`; 286,001,225 bytes.
- Both O2 files were previously verified as exact official-release matches.

## Access and authority boundary

- These are public-source release files; preserve the release/date identity and official source terms/attribution.
- Do not replace one release with the other or describe a mixed file as a single official release.
- A duplicate personal copy is not required because exact official reconstruction is available.

## How to use

1. Select e109 or e110 explicitly according to the experiment/config; record the release in outputs.
2. Verify the local file identity before use or re-download the exact official release if O2 is unavailable.
3. Use the preserved `generel_v2` code only after binding the experiment to the intended release.
4. Keep official-source attribution and release metadata with derived outputs.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private repository `z-x-yang/generel_v2` consumes these releases; the dataset release remains an independent input identity that must be recorded per experiment.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- The two releases are not interchangeable; downstream results must cite the exact release.
- This handoff preserves routing and identity, not a separate post-Harvard byte copy.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/reference-dependencies.md`.
- Fresh O2 metadata and official-match evidence were reconciled by 2026-08-14; the final registry row was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
