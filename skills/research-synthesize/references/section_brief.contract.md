# section_briefs/<section_id>.json Contract

**Location:** `research/run-NNN-TIMESTAMP/synthesis/section_briefs/<section_id>.json`
**Producer:** section brief synthesis phase
**Consumers:** report composition parent and section agents
**Validated by:** `section_brief.schema.json`

## Purpose

Compact AI-readable memory for one planned section.

## Rules

- References claims by ID only through `must_include_claim_ids` and `optional_claim_ids`.
- Does not duplicate full claim text.
- May include a short summary, missing evidence notes, avoid instructions, and visual recommendations.
- Must include section boundary rules.
