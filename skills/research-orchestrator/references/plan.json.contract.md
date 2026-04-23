# plan.json Contract

> As of Phase 10, this artifact lives under `scope/` in the run directory.

**Artifact:** `plan.json`
**Location:** `research/run-NNN-TIMESTAMP/scope/plan.json`
**Format:** JSON
**Producer:** research-orchestrator
**Consumer(s):** research-collect, research-synthesize
**Validated by:** `validate_artifact.py` against `plan.schema.json`

## Purpose

Machine-readable research plan used by the collection agent to guide source discovery and by the synthesis agent to structure output. Created alongside `scope.md` during the planning phase.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| subtopics | array of objects | Yes | Research subtopics with priority and guiding questions |
| subtopics[].name | string | Yes | Subtopic name (human-readable) |
| subtopics[].priority | integer | Yes | Priority ranking (1 = highest priority) |
| subtopics[].questions | array of strings | Yes | Specific questions to investigate for this subtopic |
| priorities | array of strings | Yes | Ordered list of subtopic names by priority (highest first) |
| expected_source_types | array of strings | Yes | Source types to seek (e.g., "docs", "paper", "blog", "code", "forum") |
| estimated_coverage_areas | array of strings | Yes | Broad topic domains the research should span |

## Example

```json
{
  "subtopics": [
    {
      "name": "Raft in edge networks",
      "priority": 1,
      "questions": [
        "How does Raft handle high-latency leader election?",
        "What are the failure modes in intermittent connectivity?"
      ]
    },
    {
      "name": "Byzantine fault tolerance at the edge",
      "priority": 2,
      "questions": [
        "Which BFT variants are practical for edge deployments?",
        "What is the overhead compared to crash-fault-tolerant algorithms?"
      ]
    }
  ],
  "priorities": [
    "Raft in edge networks",
    "Byzantine fault tolerance at the edge"
  ],
  "expected_source_types": ["docs", "paper", "blog", "code"],
  "estimated_coverage_areas": [
    "Consensus algorithms",
    "Edge computing constraints",
    "Production deployments"
  ]
}
```

## Validation

- Validated by: `validate_artifact.py` against `plan.schema.json`
- Validation timing: After orchestrator creates plan.json, before checkpoint gate 1
- Validation failures surface as checkpoint warnings, not hard stops

## Notes

- The collection agent uses `subtopics[].questions` to generate search queries
- The synthesis agent uses `subtopics` ordering to structure thematic sections
- `priorities` array provides a flat ordering for quick priority lookups
- `expected_source_types` guides the collector on which extraction methods to prefer
