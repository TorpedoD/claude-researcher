# citation_audit.md Contract

**Artifact:** `citation_audit.md`
**Location:** `research/run-NNN-TIMESTAMP/synthesis/citation_audit.md`
**Format:** Markdown
**Producer:** research-synthesize

## Purpose

Verifies claim-to-source coverage in the claim-based pipeline. The audit checks
that every `source_id` referenced by `claim_bank.json` resolves to
`collect/inventory.json`, flags weak source quality, and identifies source
concentration before report composition renders citations.

## Sections

| Section | Required | Content |
|---------|----------|---------|
| Claim Coverage | Yes | Total claims, claims with sources, unsupported/dropped claim deltas |
| Source ID Verification | Yes | Unknown source IDs, orphan inventory sources, source registry consistency |
| Semantic Alignment | Yes | Spot-check that claim text is supported by referenced evidence files |
| Weak Source Detection | Yes | Claims supported only by tier 4-5 or stale sources |
| Duplication Distortion | Yes | Claims or sections over-relying on one source |
| Summary | Yes | Pass/fail counts, warnings, recommendation |

## Example Structure

```markdown
# Citation Audit Report

## Claim Coverage

| Metric | Value |
|--------|-------|
| Total claims | 47 |
| Claims with >=1 source_id | 47 |
| Dropped unsupported deltas | 2 |

## Source ID Verification

| Status | Count |
|--------|-------|
| Resolved source_ids | 18 |
| Unknown source_ids | 0 |
| Orphan inventory sources | 3 |

## Semantic Alignment

- claim_014: supported by src_003 evidence excerpt.
- claim_022: REVIEW -- referenced source discusses the topic but not the exact numeric claim.

## Weak Source Detection

| Claim ID | Section | Best Source Tier | Status |
|----------|---------|------------------|--------|
| claim_031 | ecosystem | 4 | weak |

## Duplication Distortion

No single source supports more than 40% of included claims.

## Summary

**Recommendation:** PASS
```

## Notes

- This audit runs before Gate 3.
- Audit warnings are surfaced at Gate 3.
- Final citation rendering happens later in report composition from claim and
  source IDs.
