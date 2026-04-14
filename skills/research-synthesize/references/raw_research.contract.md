# raw_research.md Contract

**Artifact:** `raw_research.md`
**Location:** `.research/run-NNN-TIMESTAMP/synthesis/raw_research.md`
**Format:** Markdown
**Producer:** research-synthesize
**Consumer(s):** research-format (downstream), research-orchestrator (checkpoint gate 3)

## Purpose

Citation-rich first-pass research synthesis produced from collected evidence. Structured by graph communities with inline citations at the claim level. This is the primary research output before formatting and polishing.

## Sections

| Section | Required | Content |
|---------|----------|---------|
| Scope | Yes | Research question, subtopics covered, methodology summary |
| Source Quality Overview | Yes | Tier distribution table showing source counts per tier, average freshness score |
| Key Findings | Yes | Top 3-5 findings with inline citations, each supported by at least one source |
| Thematic Sections | Yes | One section per graph community/cluster. Headings derived from central_nodes (god nodes). Each section contains claims with inline `[Source Name](URL)` citations at the claim level |
| Contradictions | Yes | Explicitly stated conflicts: "Source A says X [link], Source B says Y [link]" with analysis |
| Missing Evidence | Yes | Topics from the research plan with insufficient evidence coverage |
| Open Questions | Yes | Unresolved questions identified during synthesis for potential future research |
| Bibliography | Yes | All cited sources with title, URL, tier, freshness score, and content type |

## Citation Format

Every factual claim MUST use inline `[Source Name](URL)` format. Multiple citations per paragraph where claims come from different sources.

### Examples

**Single citation:**
> Raft uses a randomized election timeout to prevent split votes [etcd Documentation](https://example.com/docs/raft).

**Multiple citations:**
> Leader election in Raft takes 150-300ms under normal conditions [etcd Documentation](https://example.com/docs/raft), though edge deployments report latencies up to 2 seconds due to network variability [Edge Consensus Study](https://example.com/papers/edge-raft).

**Contradiction:**
> The overhead of Byzantine fault tolerance varies significantly by implementation. One study reports 3x throughput reduction [BFT Performance Analysis](https://example.com/papers/bft-perf), while production deployments claim only 40% overhead with optimized batching [Cloudflare BFT Blog](https://example.com/blog/bft-production).

## Example Structure

```markdown
# Distributed Consensus Algorithms for Edge Computing

## Scope

This research investigates consensus algorithm adaptations for edge computing environments,
covering Raft modifications, Byzantine fault tolerance approaches, and production deployment patterns.

## Source Quality Overview

| Tier | Count | Description |
|------|-------|-------------|
| 1 (Official docs) | 3 | etcd, CockroachDB, TiKV documentation |
| 2 (Papers/specs) | 4 | IEEE and ACM publications |
| 3 (Quality writeups) | 5 | Engineering blogs from infrastructure companies |
| 4 (Commentary) | 2 | Developer forum discussions |
| 5 (Weak) | 0 | -- |

Average freshness score: 0.78

## Key Findings

1. Raft leader election timeouts need 5-10x increase for edge networks [Edge Raft Study](URL)
2. ...

## Consensus Mechanisms (Community 1)

Central concept: **Raft Consensus**

Raft consensus relies on leader election... [Source](URL)

## Edge Computing Constraints (Community 2)

Central concept: **Network Latency**

...

## Contradictions

- **BFT overhead estimates:** Source A reports 3x [link], Source B reports 1.4x [link]

## Missing Evidence

- No sources found for "Paxos modifications for intermittent connectivity"

## Open Questions

- How do consensus algorithms perform under network partitions lasting >30 minutes?

## Bibliography

| Source | URL | Tier | Freshness | Type |
|--------|-----|------|-----------|------|
| etcd Documentation | https://example.com/docs | 1 | 0.95 | docs |
```

## Notes

- Thematic sections are ordered by graph community structure (from GRAPH_REPORT.md)
- Section headings come from central_nodes (god nodes) in the knowledge graph
- The synthesis agent must read all evidence files and cross-reference with graph structure
- research-format consumes this file to produce the polished report.md and report.qmd
