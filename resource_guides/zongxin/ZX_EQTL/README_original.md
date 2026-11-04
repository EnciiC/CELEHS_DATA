# ARIC/GTEx-derived eQTL gene–SNP–tissue data

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `ARIC/GTEx-derived eQTL gene–SNP–tissue data`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

A mixed ARIC/GTEx-derived eQTL source masterfile and a cleaned gene–SNP–tissue table used by preserved downstream code.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/hongyi/biollm/data/raw_data/Masterfile_ARIC_REDO_GENE_NAME2_20231020.txt; /n/data1/hsph/biostat/celehs/lab/hongyi/biollm/data/gene_snp_tissue_alex_cleaned.csv
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Masterfile: `Masterfile_ARIC_REDO_GENE_NAME2_20231020.txt`; 73,845,435 bytes.
- Derived table: `gene_snp_tissue_alex_cleaned.csv`; 8,827,563 bytes.
- The masterfile contains 40 GTEx-labelled tissues plus ARIC/MayoBrain rows; it is not a pure single-release GTEx file.

## Access and authority boundary

- ARIC, GTEx, and any source-specific licence/use conditions apply independently to the relevant rows/files.
- No personal data copy is claimed; code preservation does not grant source-data redistribution authority.
- Do not label the mixed masterfile as an exact public GTEx release.

## How to use

1. Identify whether the analysis requires the mixed masterfile or the cleaned derived table.
2. Record source/tissue filtering and the exact input path in a new analysis manifest.
3. Use the preserved transformation/downstream code only with the source/licence boundary respected.
4. Do not assume the derived table resolves the upstream release and licence lineage gap.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private `z-x-yang/generel_v2` plus the preserved ProjectWrapUpHMS transformation package contain related code; exact source-release authority remains separate.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- The exact upstream GTEx release/licence lineage remains open.
- The masterfile mixes GTEx-labelled, ARIC, and MayoBrain material; claims must match the actual selected rows.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/reference-dependencies.md`.
- Fresh paths/sizes and mixed-source coverage were reconciled on 2026-08-14; the registry row was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
