# section_graph_hints.json Contract

**Location:** `research/run-NNN-TIMESTAMP/synthesis/section_graph_hints.json`
**Producer:** graph relationships / section brief synthesis
**Consumers:** report composition parent and section agents
**Validated by:** `section_graph_hints.schema.json`

## Purpose

Provides advisory graph hints for planner-defined sections.

## Rules

- Section existence and order come from the planner.
- Graph hints may suggest central entities, bridge entities, related sections, isolated claims, and cross-links.
- Graph hints may not create sections, reorder sections, override source quality, or force claim inclusion only because centrality is high.
- Section agents receive only the hints relevant to their own section unless the whole file is tiny: under 20KB or under 300 lines.
