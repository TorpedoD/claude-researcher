# inventory.json Contract

**Artifact:** `inventory.json`
**Location:** `.research/run-NNN-TIMESTAMP/collect/inventory.json`
**Format:** JSON
**Producer:** research-collect
**Consumer(s):** research-synthesize, research-orchestrator
**Validated by:** `validate_artifact.py` against `inventory.schema.json`

## Purpose

Metadata catalog for all non-quarantined collected sources. Each entry describes a source's origin, quality tier, freshness, and links to its evidence file. Used by the synthesis agent to prioritize sources and by the orchestrator at checkpoint gate 2.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sources | array | Yes | Array of source metadata objects |
| sources[].url | string | Yes | Source URL or local file path |
| sources[].source_title | string | Yes | Human-readable title |
| sources[].source_type | string | Yes | `"web"` or `"local"` |
| sources[].content_type | string | Yes | One of: `"docs"`, `"blog"`, `"code"`, `"paper"`, `"forum"`, `"other"` |
| sources[].source_tier | integer | Yes | Quality tier 1-5 (1=official docs, 2=specs/papers, 3=quality writeups, 4=commentary, 5=weak/low-signal) |
| sources[].freshness | object | Yes | Freshness metadata |
| sources[].freshness.publication_date | string or null | Yes | ISO 8601 date or null if unknown |
| sources[].freshness.freshness_score | number | Yes | 0.0 (stale) to 1.0 (very fresh) |
| sources[].fetched_at | string | Yes | ISO 8601 timestamp of when content was fetched |
| sources[].extraction_method | string | Yes | `"crawl4ai"` or `"docling"` |
| sources[].content_hash | string | Yes | SHA-256 hash of content (for deduplication) |
| sources[].evidence_file | string | Yes | Relative path to evidence file (e.g., `"evidence/source-001.md"`) |
| sources[].quality_notes | string | No | Free-form quality notes from the collector |
| sources[].suspicious | boolean | No | `true` if quarantine classifier flagged as suspicious but not quarantined |

## Example

```json
{
  "sources": [
    {
      "url": "https://example.com/docs/consensus-guide",
      "source_title": "Consensus Algorithm Guide",
      "source_type": "web",
      "content_type": "docs",
      "source_tier": 1,
      "freshness": {
        "publication_date": "2025-09-15",
        "freshness_score": 0.85
      },
      "fetched_at": "2026-04-11T14:35:00+00:00",
      "extraction_method": "crawl4ai",
      "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "evidence_file": "evidence/source-001.md",
      "quality_notes": "Official documentation, comprehensive coverage",
      "suspicious": false
    }
  ]
}
```

## Validation

- Validated by: `validate_artifact.py` against `inventory.schema.json`
- Validation timing: After collection phase completes, before checkpoint gate 2
- Validation failures surface as checkpoint warnings, not hard stops

## Notes

- Quarantined sources are NOT included in inventory.json; they are stored in `collect/quarantine/`
- Sources flagged as `suspicious: true` are included but the flag alerts the synthesis agent to treat them with lower confidence
- `content_hash` enables deduplication -- if two sources produce the same hash, the later one is skipped
- `evidence_file` paths are relative to the `collect/` directory
