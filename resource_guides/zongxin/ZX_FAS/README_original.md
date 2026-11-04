# FAS UKB variant–phenotype matrix

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `FAS UKB variant–phenotype matrix`  
**Primary platform:** FAS  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

The large first-version UK Biobank-derived variant–phenotype correlation matrix stored on FAS; this is not the older O2 CRAFT evaluation matrix.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
FAS only (no O2 copy): /n/holystore01/LABS/xlin/Lab/zxyang/derived/ukb_mvp_corr/first_version
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Canonical host and root: FAS `first_version` as recorded below.
- Shape: 33,947 phenotype/concept rows × 29,430,312 autosomal variants; source cohort count 332,423.
- Final manifest: 441,787 unique paths / 3,430,116,749,223 bytes.
- The display name intentionally omits MVP; do not rename or substitute this asset with the separate CRAFT/MVP sources.

## Access and authority boundary

- UK Biobank application/DUA and FAS access requirements apply. A processed-matrix label does not by itself authorize copying or transfer.
- There is no O2 or independent personal full copy. The current user decision is FAS-only unless external continuity is explicitly reopened.
- Do not place rare-row, participant-bearing, or sample-index sidecars in GitHub, Notion, chat, or ordinary cloud storage.

## How to use

1. Confirm the applicable UK Biobank project and FAS authorization before accessing the root.
2. Use the final QA and checksum-summary records under the FAS handoff directory before analysis.
3. Do not reconstruct this matrix from the older O2 signed-correlation file; the two assets have different cohorts, dimensions, and generation pipelines.
4. Use the pinned private pipeline repository for generation/maintenance logic, not the downstream `generel_v2` evaluator.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/ukb-mvp-correlation-matrix
- Private repository `z-x-yang/ukb-mvp-correlation-matrix`, verified commit `ef98526a7fa440e8692764e93a546e48f373bc8e`.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- Post-Harvard independent continuity is not closed; the 3.43 TB tree remains FAS-only under the current hold decision.
- A future external copy requires a disclosure-filtered derivative, an approved funded destination, and source→derivative→destination verification.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 contextual document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/ukb-assets.md`.
- FAS root/final-QA/checksum-summary metadata were freshly read on 2026-08-14; the final registry identity was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
