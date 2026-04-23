# Selection Rules for the Research Formatter

These rules govern how the formatter moves content from `synthesis/raw_research.md` into `output/report.md`. No claim may be deleted (PRES-02). Every movement must be logged in `formatter_decisions.md` (FMT-03).

## Claim Movement Hierarchy

Claims flow downward only; they may not be deleted:

```
body prose (L1 Key Points, L2 Detailed Findings)
    ↓ if low salience or overflow
supplementary findings (### Supplementary Findings)
    ↓ if reference-only
section references block (### Section References)
    ↓ if identical to another claim
merged:<target_claim_hash>
    ↓ if numeric/comparative
table:<table_id>
    ↓ if process-step
diagram:<mermaid_id>
```

Formatter may not move claims upward (e.g., cannot promote a supplementary claim to body unless correcting a mistake). Each movement must be logged with reason.

## FMT-01: Salience Movement, Not Deletion

A claim is "low salience" when:
- It restates information already covered more completely by another claim in the same section
- It is a minor procedural detail that does not change the reader's understanding

Low-salience claims MUST be moved to `### Supplementary Findings`, not deleted.

## FMT-02: No Invented Hierarchy

The formatter may reorder sections for narrative flow (e.g., move "Background" before "Mechanism") but MUST NOT:
- Reassign a fact to a different topic section
- Change the reported outcome of a comparison (e.g., reframe A > B as A ≈ B)
- Soften or strengthen contradiction status
- Change source tier labels

## FMT-03: Decisions Log Format

`formatter_decisions.md` must contain one entry per decision. Use this structure:

```markdown
## Claims Merged
| Source Hash (first 12) | Target Hash (first 12) | Reason |
|---|---|---|
| abc123456789 | def456789012 | Semantically identical; same URL, ≥0.8 similarity |

## Claims Moved to Supplementary
| Claim Hash (first 12) | Section | Reason |
|---|---|---|
| abc123456789 | Consensus Mechanisms | Restates Leader Election data already in body |

## Claims Moved to Section References
| Claim Hash (first 12) | Section | Reason |
|---|---|---|

## Claims Collapsed to Tables
| Claim Hash (first 12) | Table ID | Section |
|---|---|---|

## Claims Collapsed to Diagrams
| Claim Hash (first 12) | Diagram ID | Section |
|---|---|---|

## Tables Forced by Hints
| Section | Hint Strength | Justification |
|---|---|---|
| Consensus Mechanisms | strong | 6 numeric comparison lines |

## Tables/Diagrams Rejected
| Section | Type | Reason |
|---|---|---|
| Background | flowchart | Steps are not branching; numbered list is clearer |
```

## Duplicate-Claim Collapse

Two claims qualify for merging when:
1. They cite the same source URL, AND
2. Their normalized text similarity is ≥ 0.8 (can be assessed by the LLM)

When merging: keep the more detailed / complete version in body; record merge in FMT-03; update both claim_index entries (source: `merged:<target_hash>`, target: `body`).

## Table Promotion Rules (DENS-01 aware)

| Condition | Hint Strength | Action |
|-----------|--------------|--------|
| ≥6 lines with numeric values (same unit/dimension) | strong | MUST produce table; log in FMT-03 |
| 3–5 lines with numeric values | moderate | Should produce table; may use prose with justification |
| <3 lines with numeric values | weak/none | Use prose |
| ≥3 parallel items with same structure | moderate | Should produce table |
| ≥5 parallel items with same structure | strong | MUST produce table |

DENS-01: first table is "primary"; subsequent tables in same `##` section go into `### Supplementary Findings` (still visible, not deleted).

## Flowchart Promotion Rules

| Condition | Hint Strength | Action |
|-----------|--------------|--------|
| ≥6 process-step markers + branching | strong | MUST produce mermaid flowchart |
| 4–5 process-step markers | moderate | Should produce flowchart; numbered list acceptable |
| <4 process-step markers | weak/none | Use numbered list or prose |

MERM-01: ≤15 flow nodes / 20 graph edges per diagram. Precede with `<!-- mermaid: N nodes -->`.
DENS-01: first diagram is "primary"; overflow to `### Supplementary Findings`.

## Contradiction Preservation (CONF-01/02)

- Every `## Contradictions` entry from raw_research MUST appear in the final report
- Compression is allowed: combine similar contradictions into one entry
- Preservation is required: always show both sides with their citations
- Placement: keep in a dedicated `## Contradictions` section OR integrate into relevant thematic sections with a clear "Conflicting Evidence" label

## Citation Dedup in Report

Formatter inherits the dedup rule from synthesizer: same URL cited for the same claim within one `##` section → cite once. Different claims citing same URL → cite for each distinct claim.

Section References blocks list each URL cited in that section once, in global `[N]` order.
