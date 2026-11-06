# Data described inside project READMEs

A project README can describe inputs that do not have their own README or a prepared fake CSV. Register these as `readme_topics` in the dataset's `catalog_record.json`. They stay inside the parent dataset entry. Original README bytes remain unchanged.

The adapter in `readme_topics.py` reads named sections and file-table rows. It does not infer file columns, open source-server files or generate examples. Invalid source references fail during loading.

## Registration

Register the source Markdown in `original_readmes` first. Then add a topic:

```json
{
  "id": "followup_labels",
  "name": "Example project follow-up labels",
  "resource_type": "Registry outcomes",
  "readme_kind": "project_source",
  "aliases": ["follow-up labels", "registry"],
  "overview": {"heading": "Registry population and known fields", "paragraphs": 2},
  "files_section": "Registry population and known fields",
  "link_target": "EHR",
  "views": {
    "linkage": [{"heading": "Recommended current alignment"}],
    "outcomes": [{"heading": "Outcome definitions"}],
    "columns": [{"heading": "Known fields"}],
    "statistics": [{"heading": "Cohort counts"}]
  }
}
```

Use exact headings from the actual source. The example above is a configuration example, not an existing dataset. Available selectors are a full `heading`, its first `paragraphs`, or a paragraph beginning with `paragraph_prefix`. A field overview is not automatically a complete column dictionary.

The files section supports lines such as `Cohort file: ` followed by a backtick-enclosed absolute `//server/...` or `/n/...` path. Paths are shown in expandable controls. Files registered this way have no payload download or preview endpoint.

To include a documented mapping file, add `linkage_files` with the source table's `key_column`, `row`, `path_column`, optional `columns_column` and source `heading`. The IBD registration demonstrates this with the exact EMPI-to-patient mapping row.

## Search and follow-ups

Plain questions naming the topic retrieve its source sections directly. A single-topic dataset can resolve an EHR-linkage follow-up from the previous dataset context. Extra undocumented subjects or sites and analysis-execution requests stay with the main interpreter. Multiple matching topics are not silently merged.

For a project with several label sources or several linkages, use distinct topic names and aliases. Add focused questions and context tests before relying on ambiguous follow-ups. A new dataset group still needs the existing dataset registration and folder setup described in `README.md`.

## IBD source scope

The `ibd_registry` topic uses Enci's MAJOR IBD README, Aim 3. Its two registry cohorts and current linkage method are source excerpts. The original README does not name Ashwin. That search alias comes from Enci's clarification and is recorded as such in `alias_notes`; it does not establish source ownership.

The README refers to week-14/week-52 labels and labels the outcome summary table as 3-month/12-month outcomes. Display the original labels. Do not silently rewrite those table labels or transfer historical first-cohort linkage counts to the later 338-patient cohort.

## Checks when adding a topic

- Confirm section excerpts and file paths against the actual README.
- Keep counts attached to their cohort and denominator.
- Keep current linkage rules separate from historical checks.
- Test an overview, locations, fields, outcomes and linkage query.
- Test a short follow-up and an unsupported site or variable.
- Keep generated examples separate from observed data. Add previews only through the existing explicit synthetic-file registration.
