# FAVOR gene/protein–disease relations

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `FAVOR gene/protein–disease relations`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

The gene/protein–disease relation portion of a collaborator-delivered FAVOR/GWAS annotation package; it is not an original public FAVOR release.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/zoy043/My works/generel_v2/data/external/favor/raw/gene_disease_not_in_primekg.csv
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Primary relation file: `raw/gene_disease_not_in_primekg.csv` under the registered O2 path.
- File size: 66,333,602 bytes; SHA-256 `71d19aac35967582a2db00731dc986d45a1bfa3f2c70f52bd38174ae3b355de9`.
- The complete delivered/expanded FAVOR package contains 11 files / 523,997,698 bytes; this row represents the gene/protein–disease relation role within that package.

## Access and authority boundary

- Use is limited by the collaborator delivery and governing source terms; confirm the intended audience/use before opening or redistributing.
- The canonical source remains on O2; the encrypted personal continuity copy does not widen the audience.
- Do not upload the payload to Notion, GitHub, chat, or a group-readable data share.

## How to use

1. Confirm source-term and audience coverage for the intended analysis.
2. Keep the raw delivery object and expanded package metadata together so provenance remains recoverable.
3. Use the pinned FAVOR task-building and scoring code in `generel_v2`.
4. Do not substitute a public FAVOR release or a similarly named PrimeKG-derived file.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private repository `z-x-yang/generel_v2`, verified FAVOR commit `2a4beb31a352294e2418429b2ed76977d2e2bbf6`; task builders under `src/evaluation/favor/`.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- This is a collaborator-derived export, not a versioned public FAVOR release.
- The 11-file package is the provenance unit even though this registry row names only the gene/protein–disease role.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/favor-export.md`.
- Fresh O2, encrypted-copy, and code evidence were reconciled on 2026-08-14; the registry path was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
