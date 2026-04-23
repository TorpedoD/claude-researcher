# Evidence File Contract

**Artifact:** `evidence/*.md` (individual files)
**Location:** `research/run-NNN-TIMESTAMP/collect/evidence/`
**Format:** Markdown with YAML frontmatter (provenance header)
**Producer:** research-collect
**Consumer(s):** research-synthesize

## Purpose

Individual evidence files containing source content in markdown format, each prefixed with a YAML provenance header. The provenance header provides metadata for the synthesis agent to assess source quality, freshness, and origin without consulting inventory.json.

## Naming Convention

Files use type-prefixed naming with descriptive slugs:
- Web sources: `web-NNN-descriptive-slug.md` (e.g., `web-001-crawl4ai-docs.md`, `web-002-async-config.md`)
- Local documents: `doc-NNN-descriptive-slug.md` (e.g., `doc-001-architecture-paper.md`)
- NNN is zero-padded within each type (web and doc have separate sequences).

## Provenance Header Format

Every evidence file MUST begin with a YAML frontmatter block containing the following fields:

```yaml
---
source_title: "Title of the source"
url: "https://example.com/page"
source_type: web
content_type: docs
source_tier: 1
freshness:
  publication_date: "2025-01-15"
  freshness_score: 0.9
fetched_at: "2026-04-11T14:30:22+00:00"
extraction_method: crawl4ai
content_hash: "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
quality_notes: ""
suspicious: false
---

# Source content below in markdown...
```

## Provenance Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source_title | string | Yes | Human-readable title of the source |
| url | string | Yes | Source URL or local file path |
| source_type | string | Yes | `"web"` or `"local"` |
| content_type | string | Yes | One of: `"docs"`, `"blog"`, `"code"`, `"paper"`, `"forum"`, `"other"` |
| source_tier | integer | Yes | Quality tier 1-5 |
| freshness | object | Yes | Contains `publication_date` (string or null) and `freshness_score` (0.0-1.0) |
| fetched_at | string | Yes | ISO 8601 timestamp |
| extraction_method | string | Yes | `"crawl4ai"` or `"docling"` |
| content_hash | string | Yes | SHA-256 hash of content body (below the frontmatter) |
| quality_notes | string | No | Free-form quality notes |
| suspicious | boolean | No | `true` if quarantine classifier flagged but did not quarantine |

## Body Content

After the YAML frontmatter closing `---`, the file contains the source content converted to markdown:

- Headings preserved from original document structure
- Code blocks preserved with language annotations
- Tables converted to markdown tables
- Images referenced as placeholders (not embedded)
- Links preserved as markdown links

## Notes

- Provenance fields mirror the corresponding entry in `inventory.json`
- The `content_hash` is computed from the body content only (excluding the frontmatter)
- Quarantined items are stored in `collect/quarantine/` with the same format but are excluded from synthesis
- The synthesis agent reads provenance headers to weight claims by source quality
