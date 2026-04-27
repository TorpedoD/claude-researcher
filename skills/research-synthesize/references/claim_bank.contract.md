# claim_bank.json Contract

**Location:** `research/run-NNN-TIMESTAMP/synthesis/claim_bank.json`
**Producer:** claim extraction phase
**Consumers:** section brief synthesis, report composition through per-section slices
**Validated by:** `claim_bank.schema.json`

## Purpose

Canonical research state. Every downstream artifact points back to `claim_id`s from this file.

## Required Claim Fields

- `id`
- `text`
- `content_hash`
- `primary_section_id`
- `source_ids`
- `confidence`
- `salience`
- `include_in_report`

## Rules

- Each `claim_id` has exactly one `primary_section_id`.
- Claims include normalized SHA-256 `content_hash` values for dedupe detection.
- `claim_bank.json` is the canonical claim artifact.
- Downstream formatter agents consume `synthesis/claim_slices/<section_id>.json` instead of this global file.
