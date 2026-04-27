# coverage_matrix.md Contract

**Artifact:** `coverage_matrix.md`
**Location:** `research/run-NNN-TIMESTAMP/collect/coverage_matrix.md`
**Format:** Markdown
**Producer:** research-collect
**Consumer(s):** research (checkpoint gate 2)

## Purpose

Maps collected sources to topic categories from `scope.md` / `plan.json`. Shows coverage strength per subtopic to help the orchestrator and user assess whether collection is sufficient before proceeding to synthesis.

## Structure

### Coverage Table

| Topic Category | Sources | Tier Distribution | Coverage |
|----------------|---------|-------------------|----------|
| {subtopic from scope.md/plan.json} | {count} sources | T1:{n} T2:{n} T3:{n} T4:{n} T5:{n} | Strong / Moderate / Weak / None |

### Coverage Rating Criteria

| Rating | Definition |
|--------|------------|
| Strong | 3+ sources with at least 1 tier-1 or tier-2 source |
| Moderate | 2+ sources but no tier-1 or tier-2 sources |
| Weak | 1 source only, regardless of tier |
| None | 0 sources found for this topic |

## Example

```markdown
# Coverage Matrix

## Source Coverage by Topic

| Topic Category | Sources | Tier Distribution | Coverage |
|----------------|---------|-------------------|----------|
| Raft in edge networks | 5 sources | T1:1 T2:2 T3:1 T4:1 T5:0 | Strong |
| Byzantine fault tolerance at the edge | 3 sources | T1:0 T2:1 T3:2 T4:0 T5:0 | Strong |
| Performance benchmarks | 2 sources | T1:0 T2:0 T3:1 T4:1 T5:0 | Moderate |
| Theoretical foundations | 1 source | T1:0 T2:0 T3:0 T4:1 T5:0 | Weak |

## Summary

- **Total sources:** 11
- **Strong coverage:** 2 topics
- **Moderate coverage:** 1 topic
- **Weak coverage:** 1 topic
- **No coverage:** 0 topics
- **Overall assessment:** Collection is sufficient for synthesis with noted weakness in theoretical foundations
```

## Notes

- Topic categories are derived from `plan.json` subtopics
- The orchestrator displays this matrix at checkpoint gate 2 for user review
- "Weak" or "None" coverage areas are flagged for potential additional collection
- Coverage ratings feed into the gap detection phase (gap_analysis.md)
