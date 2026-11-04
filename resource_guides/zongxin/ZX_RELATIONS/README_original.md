# Biomedical relation datasets (indication→drug; indication→gene; disease→gene; pathway→gene)

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `Biomedical relation datasets (indication→drug; indication→gene; disease→gene; pathway→gene)`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

Four text-relation dataset families used for indication→drug, indication→gene, disease→gene, and pathway→gene evaluation or task construction.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/hongyi/biollm/data/drug_indication_for_eval/indication2drug; /n/data1/hsph/biostat/celehs/lab/hongyi/biollm/data/drug_indication_for_eval/indication2gene; /n/data1/hsph/biostat/celehs/lab/zoy043/My works/generel_v2/data/langlang_gene_eval_genefullname/lm_test_dis_gene.jsonl; /n/data1/hsph/biostat/celehs/lab/zoy043/My works/generel_v2/data/langlang_gene_eval_genefullname/lm_test_path_gene.jsonl
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Indication mappings are the registered `indication2drug` and `indication2gene` O2 directories.
- Disease→gene and pathway→gene sources are the registered `lm_test_dis_gene.jsonl` and `lm_test_path_gene.jsonl` files.
- These four roles are grouped into one dataset-family row; preserve the role-to-path mapping and do not collapse the relations into one unlabeled file set.

## Access and authority boundary

- Exact portable authorization for the indication mapping directories was not established; they remain O2-only under their current source boundary.
- Do not infer that text-format or transformed mappings are freely redistributable.
- The indication mappings were deliberately excluded from the EXP-193 portable package.

## How to use

1. Choose the relation direction required by the task and use only the matching registered path.
2. Record the relation family, source path, and code/config that built the evaluation set.
3. Use the private `generel_v2` repository for task construction and scoring.
4. Do not claim all four relation families are portable or covered by the exact EXP-193 reproduction package.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private repository `z-x-yang/generel_v2` is preserved; bind the exact task builder/scorer and experiment commit before use.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- The indication mapping directories lack an approved portable route in the current handoff.
- Additional text-relation evaluation is not claimed by the frozen EXP-193 portable package.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 context: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/reference-dependencies.md` and `gene-phenotype-train-test.md`.
- Fresh O2 locators were reconciled on 2026-08-14; the four-path registry row was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
