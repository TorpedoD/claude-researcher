# GRAPH_REPORT.md Contract

**Artifact:** `GRAPH_REPORT.md`
**Location:** `.research/run-NNN-TIMESTAMP/collect/graphify-out/GRAPH_REPORT.md`
**Format:** Markdown
**Producer:** graphify (invoked by research-orchestrator)
**Consumer(s):** research-synthesize, research-orchestrator

## Purpose

Plain-language report of the knowledge graph analysis. Provides human-readable summaries of communities, central concepts, surprising connections, and auto-generated research questions. Used by the synthesis agent to inform section ordering and by the orchestrator at checkpoint gates.

## Sections

| Section | Required | Content |
|---------|----------|---------|
| Communities | Yes | Numbered clusters with member concepts, descriptions, and inter-community connections |
| God Nodes | Yes | Highest-connected concepts with degree/betweenness metrics and significance |
| Surprising Connections | Yes | Cross-community edges that reveal unexpected relationships between concepts |
| Suggested Questions | Yes | Auto-generated questions derived from graph structure (gaps, bridges, isolated areas) |

## Example Structure

```markdown
# Knowledge Graph Report

## Communities

### Community 1: Consensus Mechanisms (12 nodes)
- **Central concept:** Raft Consensus
- **Members:** Leader Election, Log Replication, Term Numbers, ...
- **Description:** Core consensus algorithm concepts and their relationships

### Community 2: Edge Computing (8 nodes)
- **Central concept:** Network Latency
- **Members:** Intermittent Connectivity, Edge Nodes, ...

## God Nodes

1. **Raft Consensus** (degree: 15, betweenness: 0.42) -- Hub connecting consensus theory to practical implementations
2. **Network Latency** (degree: 11, betweenness: 0.31) -- Bridge between edge computing constraints and algorithm design

## Surprising Connections

- **Raft Consensus** <-> **Container Orchestration**: Edge Raft implementations appearing in Kubernetes edge distributions
- **Byzantine Fault Tolerance** <-> **IoT Sensors**: BFT variants designed for sensor network consensus

## Suggested Questions

1. How does the connection between Raft and container orchestration affect edge deployment patterns?
2. Why are IoT sensor networks adopting Byzantine fault tolerance despite the overhead?
3. What explains the isolation of "Obscure Protocol" from the main graph?
```

## Notes

- graphify produces this file in its standard format; this contract documents the expected structure
- The synthesis agent reads this report to determine section ordering (communities map to sections, god nodes become section headings)
- Suggested questions feed gap detection -- questions without answers in collected evidence indicate research gaps
- The orchestrator may show a summary of this report at checkpoint gate 2 (post-collection)
