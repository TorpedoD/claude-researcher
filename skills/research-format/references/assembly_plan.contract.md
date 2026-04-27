# assembly_plan.json Contract

**Location:** `research/run-NNN-TIMESTAMP/output/assembly_plan.json`
**Producer:** report composition parent
**Consumers:** section formatter agents, final assembler
**Validated by:** `assembly_plan.schema.json`

## Purpose

Lightweight report assembly index. It tells the composer which section slices to process, where section outputs go, and where the canonical report must be written.

## Rules

- `canonical_report_path` is always `output/report.md`.
- The parent composer reads indexes and section metadata, not full evidence.
- Section agents get one section entry, one section brief, one claim slice, and relevant graph hints.
- Publishing cannot start until `output/report.md` exists.
