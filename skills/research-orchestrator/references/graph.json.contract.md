# graph.json Contract

**Artifact:** `graph.json`
**Location:** `research/run-NNN-TIMESTAMP/collect/graphify-out/graph.json`
**Format:** JSON
**Producer:** graphify (invoked by research-orchestrator)
**Consumer(s):** research-synthesize, research-orchestrator

## Purpose

Knowledge graph built from collected evidence by graphify. Contains nodes (concepts/entities), edges (relationships), and community structure. Used by the synthesis agent for section ordering and gap detection.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| nodes | array | Yes | Graph nodes representing concepts and entities |
| nodes[].id | string | Yes | Unique node identifier |
| nodes[].label | string | Yes | Human-readable node label |
| nodes[].type | string | Yes | Node type (e.g., "concept", "entity", "tool") |
| nodes[].community | integer | Yes | Community cluster ID assigned by graphify |
| edges | array | Yes | Graph edges representing relationships |
| edges[].source | string | Yes | Source node ID |
| edges[].target | string | Yes | Target node ID |
| edges[].weight | number | Yes | Edge weight (relationship strength) |
| edges[].confidence | string | Yes | One of: "EXTRACTED", "INFERRED", "AMBIGUOUS" |
| communities | array | Yes | Community clusters with metadata |
| central_nodes | array | Yes | Nodes with highest betweenness/degree centrality (god nodes) |
| isolated_nodes | array | Yes | Nodes with low connectivity (potential gaps) |
| cluster_map | object | Yes | Mapping of community_id to member node list |

## Example Structure

```json
{
  "nodes": [
    {"id": "n1", "label": "Raft Consensus", "type": "concept", "community": 0},
    {"id": "n2", "label": "Leader Election", "type": "concept", "community": 0}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "weight": 0.85, "confidence": "EXTRACTED"}
  ],
  "communities": [
    {"id": 0, "label": "Consensus Mechanisms", "size": 12}
  ],
  "central_nodes": [
    {"id": "n1", "label": "Raft Consensus", "degree": 15, "betweenness": 0.42}
  ],
  "isolated_nodes": [
    {"id": "n99", "label": "Obscure Protocol", "degree": 1}
  ],
  "cluster_map": {
    "0": ["n1", "n2"]
  }
}
```

## Notes

- graphify produces this file in its own format; this contract documents the expected shape
- No JSON Schema validation is applied (graphify owns the format)
- `central_nodes` inform section ordering in synthesis (most-connected concepts become section headings)
- `isolated_nodes` feed gap detection (GRAPH-04) -- topics with low connectivity may need additional evidence
- `cluster_map` provides community membership for grouping related concepts into thematic sections
- Additional graphify outputs in the same directory: `GRAPH_REPORT.md`, `graph.html`, `central_nodes.json`, `isolated_nodes.json`, `cluster_map.json`
