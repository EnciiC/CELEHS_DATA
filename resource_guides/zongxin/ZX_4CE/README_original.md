# 4CE

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `4CE`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

Restricted clinical source-note and reviewed-annotation data used for clinical information-extraction development and evaluation.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
O2 root: /n/data1/hsph/biostat/celehs/lab/zoy043/My works/longwood_backup/LLM_Info_Extract/language-into-clinical-data; source: data/4CE; reviewed archive: outputs/reviewed (4CE CSVs); evaluation derivative: outputs/reviewed_updated2 (4CE CSVs)
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Raw source directory: `data/4CE/` under the registered O2 project root.
- Fresh metadata denominator: 63 raw files / 5,177,655 bytes.
- Complete reviewed archive role: 21 canonical 4CE CSVs under `outputs/reviewed/`.
- Evaluation derivative role: 21 4CE CSVs under `outputs/reviewed_updated2/`.
- One space-before-extension filename is a byte-identical duplicate; do not count or analyze both copies.

## Access and authority boundary

- 4CE authorization and the applicable institutional/project data-use rules are required; an O2 account or path visibility alone is not authorization.
- Do not copy note-level or annotation-level content to GitHub, Notion, chat, ordinary cloud storage, or a broader O2 audience.
- The O2 source is the canonical restricted source. No new broad group-readable data copy was created by this handoff.

## How to use

1. Confirm that the intended user and analysis are covered by the 4CE authorization before opening any payload.
2. Use the raw source for source preservation, `outputs/reviewed/` for the complete reviewed archive, or `outputs/reviewed_updated2/` for the preserved evaluation denominator; do not merge these roles.
3. Exclude the documented byte-identical duplicate filename from counts and analysis.
4. Use the preserved evaluation entrypoint `scripts/eval_predictions.py` from the registered private repository.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/language-into-clinical-data
- Private repository `z-x-yang/language-into-clinical-data`, verified serving commit `cb32ecb3db2d2e80bcc8867d65ee743365d695d0`; evaluation entrypoint `scripts/eval_predictions.py`.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- This README does not grant 4CE access and intentionally contains no clinical text or participant-level values.
- The reviewed archive and evaluation derivative have different roles and denominators; combining them would create an undocumented hybrid.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/clinical-annotations.md`.
- Fresh metadata and continuity evidence were last reconciled on 2026-08-14; the Google registry path was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
