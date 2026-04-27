# claim_graph_map.json Contract

**Location:** `research/run-NNN-TIMESTAMP/synthesis/claim_graph_map.json`
**Producer:** graph relationships phase
**Consumers:** section brief synthesis
**Validated by:** `claim_graph_map.schema.json`

## Purpose

Maps claim IDs to advisory relationship metadata from the graph pass.

## Rules

- Graph metadata enriches relationships between existing claims, sources, entities, and planned categories.
- Graph centrality is advisory. It must not force claim inclusion by itself.
- This file should be sliced or summarized before report composition if it is not tiny: under 20KB or under 300 lines.
