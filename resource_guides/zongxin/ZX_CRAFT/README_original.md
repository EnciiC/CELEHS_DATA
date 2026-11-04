# CRAFT UKB signed-correlation matrix

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `CRAFT UKB signed-correlation matrix`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

The older O2 UK Biobank signed-correlation Parquet matrix used by the preserved CRAFT downstream evaluation workflow.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/SHARE/biollm/ukb/SNP042424/snp_cx_corr_maf0.01.pq
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Canonical source is the exact Parquet file registered below.
- Fresh size: 3,912,827,241 bytes; owner/group `sl605:hpc_celehs`; mode `0664`.
- Prior content SHA-256: `f9770e250e074970dce2cb564f94bf9545edd98d601085fb28b6159cbbc4c170`.
- This file is not the FAS first-version matrix and is not the participant-level UKB bundle.

## Access and authority boundary

- UK Biobank application/DUA requirements still apply even though the file is visible on O2.
- The Git-tracked matrix path is a symlink and is not a data backup.
- Use or copying outside the approved UKB/O2 boundary requires separate authority; the encrypted personal continuity copy does not widen the audience.

## How to use

1. Confirm UKB authorization and verify the file identity before use.
2. Checkout the exact private `generel_v2` commit and run `src/data_prep/generate_eval_datasets.py --build ukb_sign` with an explicit `--ukb-corr` path.
3. Do not substitute the FAS matrix, MVP multi-ancestry source, or participant-level portable bundle.
4. Follow `docs/DATA_PROVENANCE.md` and `docs/DATA_TUTORIAL.md` in the pinned code checkout.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private repository `z-x-yang/generel_v2`, verified downstream/evaluation commit `8a12d517dd5f4a87a569bace9038ce5f9c506938`; main entrypoint `src/data_prep/generate_eval_datasets.py`.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- Earlier participant-level matrix-generation scripts were not recovered; the pinned code closes downstream consumption/evaluation, not original matrix generation.
- Treat this as a fixed historical evaluation asset, not the current multi-ancestry MVP source family.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/ukb-assets.md`.
- Fresh O2 metadata, encrypted-copy, and code continuity were reconciled on 2026-08-14; the registry path was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
