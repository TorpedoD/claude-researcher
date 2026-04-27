# raw_research.md Contract

> **Deprecated in `claim_pipeline_v1`:** `raw_research.md` is no longer the canonical synthesis handoff. New runs should use `synthesis/claim_bank.json`, `synthesis/section_briefs/*.json`, and `synthesis/claim_slices/*.json`. If prose diagnostics are useful, write `synthesis/research_notes.md`; it is optional and must not be required by report composition.

**Artifact:** `raw_research.md`
**Location:** `research/run-NNN-TIMESTAMP/synthesis/raw_research.md`
**Format:** Markdown
**Producer:** research-synthesize
**Consumer(s):** research-format (downstream), research-orchestrator (checkpoint gate 3)

## Purpose

Citation-rich first-pass research synthesis produced from collected evidence. Structured by graph communities with inline citations at the claim level. This is the primary research output before formatting and polishing.

Raw research is **completeness-first, not readability-first**. Facts are grouped predictably by topic/subtopic and ordered locally per ORDER-01, but prose flow and textblock sizing are NOT required. The research-format skill (downstream) owns readability.

## Evidence Completeness

The synthesizer must enumerate ALL substantive facts found in cluster-relevant evidence:
- Every distinct fact, number, version string, procedure step, comparative data point, edge case, and claim must be captured
- Each fact carries a global `[N](url)` citation
- No fact from evidence files may be dropped for brevity or readability

## Stable Local Ordering (ORDER-01)

Within each `###` subsection, emit facts in this canonical order:
1. Definition / identity
2. Mechanism / process
3. Data / versions / numbers
4. Comparisons
5. Implications / tradeoffs
6. Contradictions / open questions

Missing buckets are skipped. This keeps raw research dense but structurally predictable.

## Claim-Level Preservation (PRES-01)

Each entry in `claim_index.json` includes a `formatter_destination` field (initially `null`) populated by the formatter agent. Valid values:
- `"body"` — surfaced in body prose
- `"supplementary"` — moved to `### Supplementary Findings` within the section
- `"references"` — moved to `### Section References` block
- `"merged:<claim_hash>"` — merged with equivalent claim
- `"table:<table_id>"` — collapsed into a table cell
- `"diagram:<mermaid_id>"` — surfaced via diagram

PRES-02: No claim may have a null `formatter_destination` after formatting completes.

## Citation Dedup Rule

Multiple facts in the same `##` section citing the same URL: cite `[N](url)` at each distinct claim. Same URL cited twice for the same claim → deduplicate. Each URL must be cited ≥1× per `##` section it appears in.

## Sections

| Section | Required | Content |
|---------|----------|---------|
| Title (H1) | Yes | `# [Research Title]` — single H1 reflecting user_request |
| Summary | Yes | `## Summary` — 3–5 substantive sentences; not bullets, not a teaser |
| Table of Contents | Yes | `## Table of Contents` — anchor links to every `##` and `###` heading; generated last, inserted at position 3 |
| Scope | Yes | Research question, subtopics covered, methodology summary |
| Source Quality Overview | Yes | Tier distribution table, average freshness score |
| Key Findings | Yes | Top 3–5 findings with inline `[N](URL)` citations |
| Thematic Sections | Yes | One section per graph community. Each ends with a `### Section References` block listing sources cited in that section in global number order |
| Contradictions | Yes | Explicit conflicts with both `[N](URL)` citations and analysis |
| Missing Evidence | Yes | Topics with insufficient coverage |
| Open Questions | Yes | Unresolved questions for future research |
| Related Topics and Further Exploration | Yes | Concepts connected to main topic but outside defined scope |
| Sources | Yes | Global numbered list: `[N] Source Name — URL — Tier N — Freshness score` |

## Citation Format

Every factual claim MUST use inline `[N](source_url)` format, where N is a monotonically incrementing global integer. The same source URL always receives the same N throughout the document.

### Examples

**Single citation:**
> Raft uses a randomized election timeout to prevent split votes [1](https://example.com/docs/raft).

**Multiple citations:**
> Leader election in Raft takes 150–300ms under normal conditions [1](https://example.com/docs/raft), though edge deployments report latencies up to 2 seconds due to network variability [2](https://example.com/papers/edge-raft).

**Contradiction:**
> One study reports 3× throughput reduction [3](https://example.com/papers/bft-perf), while production deployments claim only 40% overhead with optimized batching [4](https://example.com/blog/bft-production).

### Section References Block

After the body of each `##` section (excluding the document header: `Summary`, `Table of Contents`, `Sources`), append a `### Section References` block listing only sources cited in that section, in global number order:

```markdown
### Section References
[1](https://example.com/docs/raft) — etcd Documentation
[2](https://example.com/papers/edge-raft) — Edge Consensus Study
```

Numbers are the GLOBAL assignments — do not restart per section.

### Citation Registry Artifact

The synthesizer serializes the `{url → number}` registry to `synthesis/citation_registry.json` after writing raw_research.md. See `references/output-quality-spec.md` § Citation Numbering for the full schema.

## Example Structure

```markdown
# Distributed Consensus Algorithms for Edge Computing

## Summary

This research investigates consensus algorithm adaptations for edge computing environments. Raft remains the dominant approach but requires election-timeout tuning for high-latency networks. Byzantine fault tolerance adds meaningful overhead that production deployments mitigate through batching. The practical tradeoffs between strong consistency, availability, and partition tolerance shape deployment decisions at the edge. This document surveys the mechanics, compares approaches, and surfaces open questions.

## Table of Contents

- [Scope](#scope)
- [Source Quality Overview](#source-quality-overview)
- [Key Findings](#key-findings)
- [Consensus Mechanisms](#consensus-mechanisms)
  - [Leader Election](#leader-election)
- [Edge Computing Constraints](#edge-computing-constraints)
- [Contradictions](#contradictions)
- [Missing Evidence](#missing-evidence)
- [Open Questions](#open-questions)
- [Related Topics and Further Exploration](#related-topics-and-further-exploration)
- [Sources](#sources)

## Scope

This research investigates consensus algorithm adaptations for edge computing environments, covering Raft modifications, Byzantine fault tolerance approaches, and production deployment patterns.

### Section References
[1](https://example.com/docs/raft) — etcd Documentation

{{< pagebreak >}}

## Source Quality Overview

| Tier | Count | Description |
|------|-------|-------------|
| 1 | 3 | etcd, CockroachDB, TiKV documentation |
| 2 | 4 | IEEE and ACM publications |

### Section References
[1](https://example.com/docs/raft) — etcd Documentation
[2](https://example.com/papers/edge-raft) — Edge Consensus Study

{{< pagebreak >}}

## Key Findings

1. Raft leader election timeouts need 5–10× increase for edge networks [2](https://example.com/papers/edge-raft).

### Section References
[2](https://example.com/papers/edge-raft) — Edge Consensus Study

{{< pagebreak >}}

## Consensus Mechanisms

Central concept: **Raft Consensus**.

Raft consensus relies on leader election [1](https://example.com/docs/raft). Under high-latency edge networks, the default 150–300 ms election timeout produces excessive churn [2](https://example.com/papers/edge-raft).

### Leader Election

Leader election in Raft uses randomized timeouts to prevent split votes [1](https://example.com/docs/raft).

### Section References
[1](https://example.com/docs/raft) — etcd Documentation
[2](https://example.com/papers/edge-raft) — Edge Consensus Study

{{< pagebreak >}}

## Contradictions

**BFT overhead estimates:** One study reports 3× throughput reduction [3](https://example.com/papers/bft-perf), while production deployments claim 40% overhead [4](https://example.com/blog/bft-production).

### Section References
[3](https://example.com/papers/bft-perf) — BFT Performance Analysis
[4](https://example.com/blog/bft-production) — Cloudflare BFT Blog

{{< pagebreak >}}

## Missing Evidence

No sources found for Paxos modifications under intermittent connectivity.

{{< pagebreak >}}

## Open Questions

How do consensus algorithms perform under network partitions lasting >30 minutes?

{{< pagebreak >}}

## Related Topics and Further Exploration

- CRDT-based eventually-consistent alternatives
- Hybrid logical clocks for edge timestamping

{{< pagebreak >}}

## Sources

[1] etcd Documentation — https://example.com/docs/raft — Tier 1 — Freshness 0.95
[2] Edge Consensus Study — https://example.com/papers/edge-raft — Tier 2 — Freshness 0.80
[3] BFT Performance Analysis — https://example.com/papers/bft-perf — Tier 2 — Freshness 0.70
[4] Cloudflare BFT Blog — https://example.com/blog/bft-production — Tier 3 — Freshness 0.85
```

## Notes

- Thematic sections are ordered by graph community structure (from GRAPH_REPORT.md)
- Section headings come from central_nodes (god nodes) in the knowledge graph
- The synthesis agent must read all evidence files and cross-reference with graph structure
- research-format consumes this file to produce the polished report.md and report.qmd
- Bibliography has been replaced by the Sources section (global numbered list, not a table) as of Phase 12 D-18.
- All inline citations use [N](URL) format — legacy [Source Name](URL) citations are removed as of Phase 12 D-15.
