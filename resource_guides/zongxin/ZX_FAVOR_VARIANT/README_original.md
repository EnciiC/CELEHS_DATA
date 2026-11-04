# FAVOR SNP/variant→gene regulatory relations

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `FAVOR SNP/variant→gene regulatory relations`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

The SNP/variant-to-gene regulatory relation portion of the collaborator-delivered FAVOR/GWAS annotation package for 295,763 rsIDs.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/zoy043/My works/generel_v2/data/external/favor/from_jun_eur_295763
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Raw delivery object: `raw/from_jun_eur_295763.zip`; 41,432,968 bytes; SHA-256 `764a0baee6803c7c79ccf8a0b8dc9dd71ba72b471f44493d8d44422d15cfadd6`.
- Expanded members include rsID resolution, gene mapping, L2G/QTL implied genes, promoter/enhancer links, PPI, counts, and README metadata.
- The complete delivered/expanded package contains 11 files / 523,997,698 bytes and must remain together for provenance.

## Access and authority boundary

- Collaborator delivery and source-term restrictions apply; confirm audience and intended use before access or redistribution.
- O2 is canonical. The encrypted personal copy is a continuity copy, not a new sharing authority.
- Do not place this package in Notion, GitHub, chat, or a broad group-readable data location.

## How to use

1. Start from the raw ZIP plus its expanded members and package metadata; do not retain only selected derived tables.
2. Record the exact mapping/evidence fields used (for example L2G, QTL, promoter/enhancer, or PPI).
3. Use the pinned FAVOR task builders/scorers in `generel_v2`.
4. Do not substitute a public FAVOR release with different coverage or schema.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private repository `z-x-yang/generel_v2`, verified FAVOR commit `2a4beb31a352294e2418429b2ed76977d2e2bbf6`; task builders/scorers under `src/evaluation/favor/`.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- This is a collaborator-derived package and its exact source terms must remain attached to the intended audience/use.
- The row names one regulatory-relation role, but the raw and expanded 11-file package is the provenance unit.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/favor-export.md`.
- Fresh O2, encrypted-copy, and code evidence were reconciled on 2026-08-14; the registry path was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
