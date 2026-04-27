# sections/<section_id>.meta.json Contract

**Location:** `research/run-NNN-TIMESTAMP/output/sections/<section_id>.meta.json`
**Producer:** section formatter agent
**Consumers:** final assembler, formatter audit
**Validated by:** `section_meta.schema.json`

## Purpose

Small metadata sidecar for a composed section.

## Required Fields

- `section_id`
- `title`
- `claim_ids_used`
- `source_ids_used`
- `word_count`
- `cross_links`
- `warnings`

## Rules

- The assembler reads metadata first and opens full section Markdown only to concatenate or lightly repair approved sections.
- Repeated-claim detection is enforced during Slice 3 composition, not by this Slice 1 contract alone.
