# UMLS terminology (2020) and derived dictionary (2021)

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `UMLS terminology (2020) and derived dictionary (2021)`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

UMLS 2020 MRCONSO/MRREL terminology files plus a 2021 derived dictionary used by preserved clinical and representation-learning code.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/SHARE/From_Keming/UMLS/umls2020/MRCONSO.RRF; /n/data1/hsph/biostat/celehs/lab/SHARE/From_Keming/UMLS/umls2020/MRREL.RRF; /n/data1/hsph/biostat/celehs/lab/SHARE/EHR_DICTIONARY_MAPPING/dictionary/UMLS_2021_clean/main/dictionary.csv
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- UMLS 2020 `MRCONSO.RRF`: 1,986,071,710 bytes.
- UMLS 2020 `MRREL.RRF`: 8,011,425,224 bytes.
- Derived 2021 `dictionary.csv`: 215,730,132 bytes.
- These are three registered files with distinct roles; six other historical UMLS-derived files were explicitly excluded from the offboarding completion gate.

## Access and authority boundary

- UMLS is licence-gated. Current NLM licensing is individual; lab or O2 group membership does not automatically authorize each recipient.
- Do not broaden permissions, copy to a new audience, or redistribute terminology-derived subsets/embeddings without verifying each recipient's licence scope.
- No personal or new handoff data copy is claimed.

## How to use

1. Each user must confirm their own UMLS licence/access before opening the terminology files.
2. Select MRCONSO, MRREL, or the derived dictionary according to the exact code path and record the version.
3. Keep raw terminology, derived dictionaries, and generated embeddings as separate provenance layers.
4. Use the preserved private code only within the verified licence boundary.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private repository `z-x-yang/generel_v2` and preserved CLINES code consume UMLS-derived resources; code preservation does not authorize terminology redistribution.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- Recipient licence status is not established by this README or by O2 path visibility.
- The six historical derived files remain out of scope and must not be inferred present or approved.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/reference-dependencies.md`.
- Fresh paths/sizes and the licence boundary were reconciled on 2026-08-14; the registry row was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
