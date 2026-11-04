# PrimeKG v2.1 biomedical knowledge graph

**Handoff package:** `DATASET_HANDOFF_20260817_V4`  
**Dataset-family identity:** `PrimeKG v2.1 biomedical knowledge graph`  
**Primary platform:** O2  
**Contact:** Zongxin Yang  
**Documentation status:** current per-dataset README for the 14-row Google handoff denominator

## What this dataset is

The PrimeKG v2.1 biomedical knowledge-graph CSV used by preserved CRAFT downstream code.

## Canonical data location

The following value is copied exactly from the verified 2026-08-16 Google dataset-registry payload:

```text
/n/data1/hsph/biostat/celehs/lab/hongyi/biollm/data/primekg/kg.csv
```

A visible path is a locator, not an access grant. Follow the authority boundary below before opening payloads.

## Files and dataset identity

- Canonical O2 file: `kg.csv` at the registered path below; 981,751,236 bytes.
- Previously verified as an exact Dataverse PrimeKG v2.1 match.
- Related `primekg_index_to_string.json` exists separately and is not part of the `kg.csv` byte identity.

## Access and authority boundary

- PrimeKG v2.1 is available from its public CC0 source; preserve version/source attribution and do not conflate local derived files with the official release.
- A duplicate personal data copy is not required because exact public reconstruction is available.
- Private code/repositories remain private even when the upstream dataset is public.

## How to use

1. Verify that the experiment requires PrimeKG v2.1 and record the exact file/version.
2. Use the exact official v2.1 reconstruction route if the O2 copy becomes unavailable.
3. Keep index/mapping sidecars separate from the official `kg.csv` identity.
4. Bind the private `generel_v2` code/config used to transform or evaluate against the graph.

## Related code

- Registered repository from the final Google dataset registry: https://github.com/z-x-yang/generel_v2
- Private repository `z-x-yang/generel_v2` consumes PrimeKG; record the exact downstream commit/config independently of the public data version.
- Code availability and data authority are separate: a reachable repository does not authorize copying or opening restricted data.

## Known limitations and open gaps

- The official `kg.csv` and locally generated index/mapping sidecars have different provenance.
- This handoff records v2.1; do not silently substitute later PrimeKG or CRAFT KG variants.

## Contact

- **Zongxin Yang** — dataset routing, preserved-code pointer, and handoff context.
- For DUA/licence/platform authorization, contact the applicable institutional steward or platform support; do not ask Zongxin's README to stand in for an authorization decision.

## Last verified and evidence

- O2 V3 topic document: `DATASET_HANDOFF_20260814_V3/dataset-handoffs/reference-dependencies.md`.
- Fresh O2 size and exact public-source-match evidence were reconciled by 2026-08-14; the registry row was read back on 2026-08-16.
- This README was generated on 2026-08-17 from the frozen 14-row payload and validated as part of `DATASET_HANDOFF_20260817_V4`.
