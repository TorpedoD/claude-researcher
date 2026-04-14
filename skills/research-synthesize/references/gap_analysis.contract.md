# gap_analysis.md Contract

**Artifact:** `gap_analysis.md`
**Location:** `.research/run-NNN-TIMESTAMP/synthesis/gap_analysis.md`
**Format:** Markdown
**Producer:** research-synthesize
**Consumer(s):** research-orchestrator (gap-fill decision)

## Purpose

Identifies gaps, weaknesses, and unresolved issues in the research synthesis. Feeds the orchestrator's gap-fill decision: whether to trigger targeted re-collection and second-pass synthesis.

## Sections

| Section | Required | Content |
|---------|----------|---------|
| Under-Supported Sections | Yes | Sections in raw_research.md with fewer than 2 tier-1 or tier-2 sources |
| Weak-Sourced Claims | Yes | Claims supported only by tier 4-5 sources (low confidence) |
| Missing Topic Categories | Yes | Topics from scope.md / plan.json with no evidence collected |
| Unresolved Contradictions | Yes | Conflicts between sources that could not be resolved during synthesis |
| Graph-Detected Gaps | Yes | isolated_nodes from graphify output (GRAPH-04) -- concepts with low connectivity indicating under-researched areas |
| Shallow Areas | Yes | Topics with only surface-level coverage (single source, no depth) |
| Gap-Fill Triggers | Yes | Threshold checks that determine whether gap-fill loop should activate |

## Gap-Fill Trigger Thresholds

| Trigger | Threshold | Description |
|---------|-----------|-------------|
| Uncovered topics | > 25% | More than 25% of plan.json subtopics have no evidence |
| Isolated nodes | > 20% | More than 20% of graph nodes are isolated_nodes |
| Low-confidence claims | > 30% | More than 30% of claims supported only by tier 4-5 sources |

If ANY trigger threshold is exceeded, the orchestrator should recommend gap-fill to the user at the checkpoint.

## Example Structure

```markdown
# Gap Analysis

## Under-Supported Sections

| Section | Tier 1-2 Sources | Total Sources | Status |
|---------|-----------------|---------------|--------|
| Theoretical Foundations | 0 | 1 | Under-supported |
| Performance Benchmarks | 1 | 2 | Borderline |

## Weak-Sourced Claims

| Claim | Section | Best Source Tier | Sources |
|-------|---------|-----------------|---------|
| "Paxos overhead is 5x in edge networks" | Edge Constraints | Tier 4 | 1 forum post |

## Missing Topic Categories

- Paxos modifications for intermittent connectivity (0 sources)
- Energy-efficient consensus for battery-powered edge nodes (0 sources)

## Unresolved Contradictions

1. **BFT overhead:** 3x (Source A, tier 2) vs 1.4x (Source B, tier 3) -- cannot determine without benchmark reproduction

## Graph-Detected Gaps

Isolated nodes from graphify analysis:
- "Obscure Protocol" (degree: 1) -- mentioned once, no connections to main research themes
- "Energy Harvesting" (degree: 0) -- appeared in one source, completely disconnected

## Shallow Areas

- Container orchestration at the edge: 1 blog post, no technical depth
- Sensor network consensus: 1 paper abstract only

## Gap-Fill Triggers

| Trigger | Value | Threshold | Status |
|---------|-------|-----------|--------|
| Uncovered topics | 2/8 (25%) | > 25% | BORDERLINE |
| Isolated nodes | 2/15 (13%) | > 20% | OK |
| Low-confidence claims | 3/47 (6%) | > 30% | OK |

**Recommendation:** Borderline -- consider targeted collection for "Paxos modifications" and "Energy-efficient consensus"
```

## Notes

- The orchestrator reads gap-fill triggers to decide whether to recommend re-collection
- If gap-fill activates, the collector runs a targeted pass and the synthesizer produces a second-pass synthesis
- Graph-detected gaps (isolated_nodes) are particularly valuable because they reveal structural holes in the knowledge graph
- This document feeds the checkpoint gate 3 summary table
