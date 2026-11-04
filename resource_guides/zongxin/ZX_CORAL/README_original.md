# CORAL (Breast + PDAC)

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `CORAL (Breast + PDAC)`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

Restricted CORAL breast-cancer and pancreatic-ductal-adenocarcinoma source-note and reviewed-annotation datasets for clinical extraction and evaluation.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
O2 root: /n/data1/hsph/biostat/celehs/lab/zoy043/My works/longwood_backup/LLM_Info_Extract/language-into-clinical-data; sources: data/coral_annotated_breastca and data/coral_annotated_pdac; reviewed/evaluation variants are under outputs/reviewed and outputs/reviewed_updated2
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Breast source: `data/coral_annotated_breastca/`; 20 raw files / 278,152 bytes, 13 reviewed files, and 13 evaluation files.
- PDAC source: `data/coral_annotated_pdac/`; 20 raw files / 276,135 bytes, 16 complete reviewed files, and 15 evaluation files.
- PDAC 19 is intentionally absent from the evaluation derivative; do not add it or merge archive/evaluation roles.

## Access and authority boundary

- CORAL source-specific authorization is required; O2 path visibility alone does not authorize use or disclosure.
- Do not place note/annotation payloads in GitHub, Notion, chat, ordinary cloud storage, or a broader group share.
- O2 remains the canonical restricted source. The personal continuity copies are encrypted and do not widen the audience.

## How to use

1. Confirm CORAL authorization before opening either disease subset.
2. Choose the complete reviewed archive for annotation preservation or the evaluation derivative for reproducing the existing evaluation denominator.
3. Keep breast and PDAC identifiers and denominators separate; do not infer a missing PDAC evaluation file is accidental.
4. Use `scripts/eval_predictions.py` from the verified private code checkout.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/language-into-clinical-data
- Private repository `z-x-yang/language-into-clinical-data`, verified commit `cb32ecb3db2d2e80bcc8867d65ee743365d695d0`; evaluation entrypoint `scripts/eval_predictions.py`.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- This README contains only aggregate-safe metadata and paths, not clinical content.
- The complete archive and evaluation derivative are semantically distinct versions and must not be synthesized into a hybrid.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/clinical-annotations.md`.
- Fresh source, encrypted-copy, code, and document evidence were reconciled on 2026-08-14; the registry path was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
