# global_id_registry.json Contract

**Location:** `research/run-NNN-TIMESTAMP/synthesis/global_id_registry.json`
**Producer:** claim extraction phase
**Consumers:** claim extraction, graph relationships, section brief synthesis, report composition
**Validated by:** `global_id_registry.schema.json`

## Purpose

Stores stable IDs for sources, claims, sections, and normalized content hashes. IDs are generated once and never regenerated during a run.

## Rules

- `source_ids` maps source identity keys to `src_NNN` IDs.
- `claim_ids` maps normalized claim hashes to `claim_NNN` IDs.
- `section_ids` maps planner-defined section names to stable section IDs.
- `content_hashes` records duplicate-detection keys.
- This file is global state. Downstream agents may read it only when it is tiny: under 20KB or under 300 lines.
