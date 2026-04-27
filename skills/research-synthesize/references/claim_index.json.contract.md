# claim_index.json Contract

> **Legacy compatibility only in `claim_pipeline_v1`:** `claim_bank.json` is the canonical claim artifact. If older consumers still need `claim_index.json`, emit it as a small compatibility artifact derived from `claim_bank.json`; do not make it the source of truth.

**Artifact:** `claim_index.json`
**Location:** `research/run-NNN-TIMESTAMP/synthesis/claim_index.json`
**Format:** JSON
**Producer:** research-synthesize
**Consumer(s):** research-orchestrator (checkpoint gate 3), gap analysis
**Validated by:** `validate_artifact.py` against `claim_index.schema.json`

## Purpose

Maps every factual claim in raw_research.md to its supporting sources. Enables citation audit, gap detection, and quality assessment. The orchestrator reads the metadata block at checkpoint gate 3 to display claim coverage statistics.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| claims | array | Yes | Array of claim objects |
| claims[].claim_text | string | Yes | The factual claim text as it appears in raw_research.md |
| claims[].claim_hash | string | Yes | SHA-256 hash of normalized claim text (lowercased, whitespace-collapsed) |
| claims[].section | string | Yes | Section heading where the claim appears |
| claims[].sources | array | Yes | Array of supporting source objects |
| claims[].sources[].url | string | Yes | Source URL matching inventory.json entry |
| claims[].sources[].source_title | string | Yes | Source title for display |
| claims[].sources[].tier | integer | Yes | Source quality tier (1-5) |
| claims[].sources[].freshness | string | Yes | Freshness score or publication date |
| metadata | object | Yes | Aggregate statistics |
| metadata.total_claims | integer | Yes | Total number of claims indexed |
| metadata.citation_coverage_pct | number | Yes | Percentage of claims with at least one citation (0-100) |
| metadata.avg_sources_per_claim | number | Yes | Average number of supporting sources per claim |

## Example

```json
{
  "claims": [
    {
      "claim_text": "Raft leader election timeouts need 5-10x increase for edge networks",
      "claim_hash": "sha256:a1b2c3d4e5f6...",
      "section": "Consensus Mechanisms",
      "subsection": "Leader Election",
      "formatter_destination": null,
      "sources": [
        {
          "url": "https://example.com/papers/edge-raft",
          "source_title": "Edge Raft Study",
          "tier": 2,
          "freshness": "0.82"
        },
        {
          "url": "https://example.com/docs/raft-tuning",
          "source_title": "Raft Tuning Guide",
          "tier": 1,
          "freshness": "0.95"
        }
      ]
    }
  ],
  "metadata": {
    "total_claims": 47,
    "citation_coverage_pct": 95.7,
    "avg_sources_per_claim": 1.8
  }
}
```

## Validation

- Validated by: `validate_artifact.py` against `claim_index.schema.json`
- Validation timing: After synthesis phase completes, before checkpoint gate 3
- Validation failures surface as checkpoint warnings, not hard stops

## Notes

- `claim_hash` enables deduplication of claims across synthesis passes (gap-fill re-synthesis)
- Claims with 0 sources indicate unsupported assertions that should be flagged
- The orchestrator shows `citation_coverage_pct` and `avg_sources_per_claim` at checkpoint gate 3
- Gap analysis uses this index to identify weak-sourced claims (only tier 4-5 sources)
- A `citation_coverage_pct` below 90% triggers a warning at checkpoint gate 3
- `formatter_destination` is null when raw_research is produced; the formatter agent populates it with one of: `body`, `supplementary`, `references`, `merged:<hash>`, `table:<id>`, `diagram:<id>`. PRES-02 requires all claims have a non-null destination after formatting.
