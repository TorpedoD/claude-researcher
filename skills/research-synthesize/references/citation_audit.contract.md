# citation_audit.md Contract

**Artifact:** `citation_audit.md`
**Location:** `research/run-NNN-TIMESTAMP/synthesis/citation_audit.md`
**Format:** Markdown
**Producer:** research-synthesize

## Purpose

Verifies the quality and correctness of citations in raw_research.md. Checks that every cited URL exists in inventory.json, that claims semantically match their cited sources, and detects citation quality issues like staleness and over-citation.

## Sections

| Section | Required | Content |
|---------|----------|---------|
| URL Verification | Yes | Check each cited URL in raw_research.md exists in inventory.json. Flag orphan citations (URL not in inventory) and phantom citations (invented URLs) |
| Semantic Alignment | Yes | Check that each claim's content semantically matches the cited source's evidence file. Flag misattributions where claim content does not appear in the cited source |
| Stale Source Detection | Yes | Flag sources with low freshness_score (below 0.3) that are cited for current-state claims. Distinguish historical claims (staleness acceptable) from current-state claims (staleness problematic) |
| Duplication Distortion | Yes | Detect single-source over-citation where one source accounts for more than 40% of all citations. Flag sections where all claims cite the same source (single-perspective risk) |
| Summary | Yes | Pass/fail counts per check category, overall audit score (0-100), and recommendation (pass/review/fail) |

## Example Structure

```markdown
# Citation Audit Report

## URL Verification

| Status | Count |
|--------|-------|
| Verified (URL in inventory) | 45 |
| Orphan (URL not in inventory) | 2 |
| Phantom (URL appears fabricated) | 0 |

### Orphan Citations
- `https://example.com/removed-page` cited in "Consensus Mechanisms" section -- not in inventory.json
- `https://example.com/old-docs` cited in "Edge Constraints" section -- not in inventory.json

## Semantic Alignment

| Status | Count |
|--------|-------|
| Aligned (claim matches source) | 43 |
| Misaligned (claim not in source) | 2 |
| Unable to verify | 2 |

### Misaligned Citations
- Claim: "Raft handles 10k ops/sec at the edge" cites [Source A] -- source discusses throughput but states 5k ops/sec, not 10k

## Stale Source Detection

| Freshness Range | Count | Flagged |
|-----------------|-------|---------|
| 0.8 - 1.0 (fresh) | 30 | 0 |
| 0.5 - 0.79 (moderate) | 12 | 0 |
| 0.3 - 0.49 (aging) | 3 | 0 |
| 0.0 - 0.29 (stale) | 2 | 2 |

### Stale Citations for Current-State Claims
- "CockroachDB uses Raft for consensus" cites 2019 documentation (freshness: 0.15) -- verify current accuracy

## Duplication Distortion

| Source | Citation Count | % of Total | Status |
|--------|---------------|------------|--------|
| etcd Documentation | 12 | 25.5% | OK |
| Edge Raft Study | 8 | 17.0% | OK |
| Cloudflare Blog | 6 | 12.8% | OK |

No single source exceeds 40% threshold.

### Single-Source Sections
- "Theoretical Foundations" -- all 3 claims cite the same source (Edge Raft Study)

## Summary

| Check | Pass | Fail | Score |
|-------|------|------|-------|
| URL Verification | 45 | 2 | 96% |
| Semantic Alignment | 43 | 2 | 91% |
| Stale Sources | 45 | 2 | 96% |
| Duplication | 47 | 0 | 100% |

**Overall Audit Score:** 94/100
**Recommendation:** PASS (minor issues noted above)
```

## Notes

- The citation audit runs after synthesis and before checkpoint gate 3
- Audit failures do not block the pipeline but are surfaced as warnings
- Orphan and phantom citations indicate synthesis quality issues
- Semantic misalignment may indicate hallucinated claims
- The orchestrator shows the Summary section at checkpoint gate 3
