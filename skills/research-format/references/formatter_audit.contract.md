# formatter_audit.json Contract

**Location:** `research/run-NNN-TIMESTAMP/output/formatter_audit.json`
**Producer:** report composition validator / assembler
**Consumers:** orchestrator Gate 4, publishing phase
**Validated by:** `formatter_audit.schema.json`

## Purpose

Records report composition validation status and issues found during assembly.

## Rules

- `canonical_report_path` is always `output/report.md`.
- Records warnings and errors without rereading full evidence.
- Tracks repeated claim IDs and missing required claims once Slice 3 implements assembler validation.
- Publishing reads this audit and `output/report.md`; it does not reinterpret research claims.
