# Content Rules Contract (Phase 11)

Consumed by: `scripts/check_content_rules.py` for Markdown checks. Claim coverage
in `claim_pipeline_v1` is enforced by
`~/.claude/skills/research-format/scripts/report_composer.py audit`.

## Scope

"Section" = content between one `##` heading and the next `##` heading.
Subsections (`###`, `####`) roll UP into their parent `##` section for RULE-02 and CONS-02 counts.
CONS-01 applies to BOTH `##` and `###` headings (every heading needs a body).

## Rules

| Rule | Requirement | Threshold | Severity | Source |
|------|-------------|-----------|----------|--------|
| HIER-04 | Code fences must have language annotation | bare ``` → violation | warn | D-10 |
| RULE-02 | Source citation cap per section | >3 occurrences of same URL in one ## section | warn | D-15 |
| CONS-01 | No heading without content body | heading immediately followed by next heading | warn | D-17 |
| CONS-02 (min) | Minimum substantive content | <2 sentences in one ## section | warn | D-18 |
| CONS-02 (guidance) | Subsection-split guidance | >800 words in one ## section | info | D-18 |

**CONS-02 scope:** Applies to `output/report.md` only. `synthesis/raw_research.md` is EXEMPT — no word-count ceiling applies to raw research. Use `--target=raw` to skip this check on raw_research.md.

## Violation Payload

Every violation in the output JSON has these fields:

| Field | Type | Values |
|-------|------|--------|
| `rule` | string | `"HIER-04"` \| `"RULE-02"` \| `"CONS-01"` \| `"CONS-02"` |
| `line` | int | 1-indexed line number of the offending heading or fence |
| `severity` | string | `"warn"` (default) \| `"info"` (CONS-02 >800 words only) |
| `detail` | string | Human-readable description including relevant values (URL, count, word count) |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | pass (no violations) |
| 1 | warn (≥1 violation) |
| 2 | error (bad input: missing file, path traversal `..`, oversized file >10MB) |

## Full Output Shape

```json
{
  "status": "pass" | "warn" | "error",
  "file": "<absolute path>",
  "violations": [...],
  "summary": {
    "total": <int>,
    "by_rule": {"HIER-04": N, "RULE-02": N, "CONS-01": N, "CONS-02": N},
    "by_severity": {"warn": N, "info": N}
  }
}
```

## MERM-01 — Mermaid Diagram Constraints (Phase 12 — D-23, D-24)

**Severity:** warn (advisory only — does not block Gate 3)

**Behavior:**
- Every ` ```mermaid ` code fence MUST be preceded on the immediately prior non-blank line by a node-count comment: `<!-- mermaid: N nodes -->` (case-insensitive, singular/plural `node`/`nodes`).
- If the declared node count N exceeds 15 (flow-diagram cap per D-23), emit a MERM-01 violation on the fence line with detail `"Mermaid diagram declares {N} nodes (cap=15): consider splitting"`.
- If no such comment precedes the fence, emit MERM-01 with detail `"Mermaid block missing node-count comment <!-- mermaid: N nodes -->"`.

**Rationale:** PDF rendering truncates oversized diagrams. Synthesizer instructions require splitting diagrams with >15 nodes or using structured text instead.

**Source:** `~/.claude/skills/research-synthesize/references/output-quality-spec.md` § Mermaid Diagram Constraints.

## RULE-02 Exemption — Section References (Phase 12)

URLs appearing inside a `### Section References` block do NOT count toward the RULE-02 3×-per-section cap. Rationale: the block is a metadata summary that mirrors the inline citations already counted in the section body. Without this exemption, every legitimate multi-cite section produces a spurious RULE-02 warning after Phase 12's new citation format (`### Section References` blocks per D-17).

**Scope of exemption:** starts when a `### Section References` heading is encountered; ends at the next `##` heading (new section) or another `###` heading (other subsection). URLs inside the block are ignored for RULE-02 only — CONS-01 and CONS-02 still apply.

## What This Does NOT Check

- HIER-01, HIER-02, HIER-03, HIER-05, RULE-01, LINK-01: LLM-instruction compliance only, enforced in synthesizer SKILL.md.
- Anchor resolution for cross-section links: cosmetic; Phase 16 QA may add.
- Paragraph length (HIER-04 ≤5 sentences): not machine-checked in Phase 11. **Scope: `output/report.md` only. `synthesis/raw_research.md` is EXEMPT** — the formatter owns paragraph-length enforcement.
- CONS-02 sentence counting uses `[.!?](?:\s|$)` — counts punctuation-terminated sentence boundaries.

## Claim coverage and citation style

- **Target**: `output/report.md`, `output/sections/*.meta.json`, `output/formatter_audit.json`
- **Rule**: Every required claim in `synthesis/section_briefs/*.json` must appear in the matching section metadata.
- **Rule**: Claim and source IDs used by a section must come from that section's `synthesis/claim_slices/<section_id>.json`.
- **Rule**: Citations must use `[Source Title](url)`; numeric or mixed citation styles are errors.
- **Severity**: error (blocking at Gate 3)
- **Checker**: `~/.claude/skills/research-format/scripts/report_composer.py audit`

## CONF-01 — Contradiction visibility

- **Target**: `output/report.md`
- **Rule**: Every contradiction surfaced in `## Contradictions` of raw_research must appear somewhere in the report (dedicated section or "Conflicting Evidence" subsection)
- **Severity**: warn
- **Checker**: manual diff or scripted grep

## Legacy Coverage Helpers

`coverage_audit.py` and old registry/index artifacts are deprecated helper
mechanisms. They are not used by `claim_pipeline_v1` report composition.

## Invocation

```bash
python3 ~/.claude/skills/research-orchestrator/scripts/check_content_rules.py --target=report <run_dir>/output/report.md
python3 ~/.claude/skills/research-format/scripts/report_composer.py audit --run-dir <run_dir>
```

## Integration in Pipeline

After formatting produces `output/report.md`, the orchestrator runs the report
scanner and formatter audit. Content-rule violations are warnings unless the
formatter audit reports errors. Formatter audit errors block publishing unless
the user explicitly acknowledges the violation.
