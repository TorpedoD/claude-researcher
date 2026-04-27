# scope.md Contract

> As of Phase 10, this artifact lives under `scope/` in the run directory.

**Artifact:** `scope.md`
**Location:** `research/run-NNN-TIMESTAMP/scope/scope.md`
**Format:** Markdown
**Producer:** research
**Consumer(s):** research-collect, research-synthesize

## Purpose

Defines the research scope after the orchestrator processes the user's request. This is the human-readable planning output shown at checkpoint gate 1 (post-planning) for user confirmation before collection begins.

## Sections

| Section | Type | Required | Description |
|---------|------|----------|-------------|
| Title | heading (H1) | Yes | Research title derived from user request |
| Subtopics | section | Yes | Bulleted list of subtopics and specific questions to investigate |
| Source Types | section | Yes | Expected source types to collect (e.g., official docs, academic papers, blog posts, code repositories, forum discussions) |
| Coverage Areas | section | Yes | Estimated coverage areas -- broad topic domains the research should span |
| Priorities | section | Yes | Priority ranking of subtopics (highest priority investigated first, receives more crawl budget) |
| Constraints | section | No | Budget limits, domain restrictions, date ranges, excluded sources |

## Example

```markdown
# Distributed Consensus Algorithms for Edge Computing

## Subtopics

- How does Raft perform in high-latency edge networks?
- What modifications to Paxos exist for intermittent connectivity?
- Comparison of Byzantine fault tolerance approaches at the edge
- Real-world deployments and case studies

## Source Types

- Official documentation (etcd, CockroachDB, TiKV)
- Academic papers (IEEE, ACM Digital Library)
- Engineering blog posts (Cloudflare, Fly.io)
- Code repositories with implementation examples

## Coverage Areas

- Consensus algorithm fundamentals
- Edge computing constraints and network models
- Production deployments and operational experience
- Performance benchmarks and trade-offs

## Priorities

1. Real-world edge deployments (highest -- most actionable)
2. Algorithm modifications for edge constraints
3. Performance benchmarks
4. Theoretical foundations (lowest -- well-established)

## Constraints

- Focus on publications from 2020 onwards
- Maximum 75 pages crawl budget
- Exclude Stack Overflow answers (low signal for this topic)
```

## Notes

- `scope.md` is a planning artifact, not validated by JSON Schema
- The structured counterpart is `plan.json` which contains the machine-readable version
- Both are produced by the orchestrator during the planning phase
- User reviews scope.md at checkpoint gate 1 and may request adjustments
