# gap_analysis.md Contract

**Artifact:** `gap_analysis.md`
**Location:** `research/run-NNN-TIMESTAMP/synthesis/gap_analysis.md`
**Format:** Markdown
**Producer:** research-synthesize
**Consumer(s):** research Gate 3

## Purpose

Identifies weak or missing claim coverage before report composition. Gap
analysis is based on planner-defined sections, `claim_bank.json`,
`section_briefs/*.json`, source tiers, contradictions, and compact graph hints.

## Sections

| Section | Required | Content |
|---------|----------|---------|
| Empty Planned Sections | Yes | Planned sections with no claims and explicit missing-evidence reasons |
| Under-Supported Sections | Yes | Sections with too few tier 1-2 supporting sources |
| Weak-Sourced Claims | Yes | Claims supported only by tier 4-5 or stale sources |
| Missing Topic Categories | Yes | Planner subtopics with no claim coverage |
| Unresolved Contradictions | Yes | Conflict IDs or claim pairs that remain unresolved |
| Graph-Detected Gaps | Yes | Isolated claims/entities from `section_graph_hints.json` |
| Gap-Fill Triggers | Yes | Threshold checks for targeted re-collection |

## Gate 3 Failure Rule

Gate 3 must fail if any planned section has no claims and no explicit
missing-evidence reason in either:

- the section brief `missing` field, or
- this `gap_analysis.md` file.

## Gap-Fill Trigger Thresholds

| Trigger | Threshold | Description |
|---------|-----------|-------------|
| Uncovered topics | > 25% | More than 25% of planner sections have no claim coverage |
| Isolated graph hints | > 20% | More than 20% of claims or entities are isolated |
| Low-confidence claims | > 30% | More than 30% of claims are low confidence |

## Example Structure

```markdown
# Gap Analysis

## Empty Planned Sections

- Security Model: no claims extracted; missing evidence reason: no strong source found for current validator security assumptions.

## Under-Supported Sections

| Section | Tier 1-2 Sources | Total Sources | Status |
|---------|------------------|---------------|--------|
| Consensus Mechanism | 2 | 3 | OK |
| Security Model | 0 | 0 | Missing |

## Weak-Sourced Claims

| Claim ID | Section | Best Source Tier | Sources |
|----------|---------|------------------|---------|
| claim_031 | Ecosystem | 4 | src_014 |

## Missing Topic Categories

- Security Model: 0 claims.

## Unresolved Contradictions

- conflict_002: claim_011 and claim_018 disagree on throughput assumptions.

## Graph-Detected Gaps

- claim_088: isolated from related consensus claims.

## Gap-Fill Triggers

| Trigger | Value | Threshold | Status |
|---------|-------|-----------|--------|
| Uncovered topics | 1/8 (12.5%) | > 25% | OK |
| Isolated graph hints | 3/47 (6%) | > 20% | OK |
| Low-confidence claims | 3/47 (6%) | > 30% | OK |

**Recommendation:** Proceed with noted missing evidence.
```

## Notes

- This document feeds Gate 3 and targeted gap-fill.
- It must not depend on `raw_research.md`.
- Weak-source findings warn unless gap-fill thresholds are triggered.
