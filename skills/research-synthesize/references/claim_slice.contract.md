# claim_slices/<section_id>.json Contract

**Location:** `research/run-NNN-TIMESTAMP/synthesis/claim_slices/<section_id>.json`
**Producer:** section brief synthesis phase
**Consumers:** report composition section agents
**Validated by:** `claim_slice.schema.json`

## Purpose

Provides a single section agent with a compact self-contained packet. Required
claims carry full text; optional claims carry briefs and routing metadata.

## Rules

- Contains exactly one `section_id`.
- Contains `required_claims`, `optional_claims`, and `source_records`.
- Contains only claims assigned to, or explicitly referenced by, that section.
- Contains only source records referenced by those claims.
- Includes `boundary_rules` so cross-section reuse is a reference, not a rewritten explanation.
- Section agents must consume this slice instead of full `claim_bank.json`, full `inventory.json`, or full graph files.
