# Selection Rules for the Claim-Sliced Research Formatter

These rules apply to `claim_pipeline_v1`. The formatter composes
`output/report.md` from `output/assembly_plan.json`,
`synthesis/section_briefs/*.json`, and `synthesis/claim_slices/*.json`.
It does not use `synthesis/raw_research.md`, `synthesis/claim_index.json`, or
numeric citation registries.

## Section Boundaries

- Use the section order and section IDs from `output/assembly_plan.json`.
- Do not create, delete, or reorder sections during report composition.
- Each section may use only its matching section brief, claim slice, graph hints,
  and format preferences.
- Graph hints may inform relationship language and cross-links inside existing
  sections, but they cannot create new topics or move claims between sections.

## Claim Selection

- Include every `must_include_claim_id` from the section brief.
- Optional claims may be omitted when they are low salience for the selected
  depth, audience, or tone.
- If optional claims are skipped, record the reason in the section metadata
  `warnings` field when the omission could affect reader interpretation.
- Do not invent claims, statistics, URLs, source titles, graph relationships, or
  source-quality labels.
- Do not rewrite a claim so that it changes the reported outcome, comparison,
  contradiction status, confidence, or source support.

## Source and Citation Rules

- Cite factual content with Markdown title links:

  ```markdown
  [Source Title](url)
  ```

- The source title and URL must come from the active section claim slice.
- Numeric citations such as `[1]` and `[1](url)` are invalid.
- External URLs in section output must be present in that section's claim-slice
  sources.
- External URLs in the final assembled report must be present in the union of all
  section claim-slice sources.
- Internal Markdown anchors such as `#sources` are navigation links, not source
  citations.

## Tables and Diagrams

- Prefer tables for three or more comparable items, repeated units, or parallel
  attributes.
- Prefer Mermaid diagrams only when they clarify a process, dependency, or
  relationship that prose would make harder to scan.
- Tables and diagrams still consume claims: include their claim IDs in
  `claim_ids_used` and their source IDs in `source_ids_used`.
- Keep every table or diagram grounded in the active section slice.

## Metadata and Audit

- `output/sections/<section_id>.meta.json` is the formatter's audit handoff.
- `claim_ids_used` must include every claim rendered in prose, tables, or
  diagrams.
- `source_ids_used` must be a subset of the active section claim slice.
- `cross_links` must reference planned section IDs only.
- Formatting is not complete until `report_composer.py audit` writes
  `output/formatter_audit.json` with no errors.
