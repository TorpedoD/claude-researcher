# collection_log.md Contract

**Artifact:** `collection_log.md`
**Location:** `research/run-NNN-TIMESTAMP/collect/collection_log.md`
**Format:** Markdown
**Producer:** research-collect

## Purpose

Comprehensive log of all collection operations, errors, skips, and quarantine decisions. Provides an audit trail for the collection phase and feeds the orchestrator's checkpoint gate 2 summary.

## Sections

| Section | Required | Content |
|---------|----------|---------|
| Operations Log | Yes | Timestamped entries for each URL crawled or document parsed, including method used (crawl4ai/docling) and result (success/error/skip/quarantined) |
| Budget Status | Yes | Current consumption: pages used vs max_pages, per-domain page counts vs max_per_domain, depth levels reached |
| Quarantine Decisions | Yes | Items processed by the quarantine classifier with classification result (safe/suspicious/quarantined) and reason |
| Errors | Yes | Failed URLs with error messages, HTTP status codes, and whether retries were attempted |
| Skips | Yes | Skipped URLs with reason (duplicate content_hash, budget exceeded, robots.txt disallowed, domain limit reached) |

## Example Structure

```markdown
# Collection Log

## Operations Log

| Timestamp | URL | Method | Result | Evidence File |
|-----------|-----|--------|--------|---------------|
| 2026-04-11T14:30:22Z | https://example.com/docs/guide | crawl4ai | success | source-001.md |
| 2026-04-11T14:30:45Z | https://example.com/docs/api | crawl4ai | success | source-002.md |
| 2026-04-11T14:31:02Z | https://example.com/blog/old-post | crawl4ai | skip | -- |
| 2026-04-11T14:31:15Z | /local/paper.pdf | docling | success | source-003.md |

## Budget Status

- Pages used: 42 / 75
- Domains crawled: 5
- Per-domain breakdown:
  - example.com: 12 / 15
  - docs.example.org: 8 / 15
  - research.example.edu: 7 / 15
- Max depth reached: 2 / 3

## Quarantine Decisions

| Source | Classification | Reason |
|--------|---------------|--------|
| https://example.com/docs/guide | safe | Official documentation, consistent structure |
| https://example.com/sketchy/post | quarantined | Prompt injection patterns detected in content |
| https://example.com/forum/thread | suspicious | Low-quality forum thread, but contains relevant data |

## Errors

| Timestamp | URL | Error |
|-----------|-----|-------|
| 2026-04-11T14:32:00Z | https://example.com/broken | HTTP 404 Not Found |
| 2026-04-11T14:32:30Z | https://example.com/timeout-page | Connection timeout after 30s |

## Skips

| URL | Reason |
|-----|--------|
| https://example.com/docs/guide (duplicate) | Content hash matches source-001.md |
| https://example.com/admin | robots.txt disallowed |
| https://example.com/deep/page | Budget exceeded (max_pages reached) |
```

## Notes

- The operations log is append-only during collection
- Budget status is updated after each operation
- The orchestrator reads this log to populate the checkpoint gate 2 summary table
- Quarantine decisions are logged here AND quarantined files are placed in `collect/quarantine/`
