# Run Directory Schema

**Version:** 2.0
**Owner:** research
**Created by:** `init_run.py` (manifest.json and top-level directory only)

## Directory Tree

```
research/run-NNN-TIMESTAMP/
  manifest.json                # Run metadata, budget config, phase status
  scope/                       # Planning artifacts (added Phase 10, D-05/D-07)
    scope.md                   # Human-readable research scope
    plan.json                  # Machine-readable research plan
    question_tree.json         # 7-layer question tree with bridge questions
  collect/
    evidence/                  # Individual *.md files with YAML provenance headers
    quarantine/                # Items excluded from synthesis by quarantine classifier
    graphify-out/              # graph.json, GRAPH_REPORT.md, graph.html, central_nodes.json, isolated_nodes.json, cluster_map.json
    inventory.json             # Metadata for all non-quarantined sources
    collection_log.md          # All operations, errors, skips, quarantine decisions
    coverage_matrix.md         # Maps sources to topic categories from scope
  synthesis/
    global_id_registry.json    # Stable source_id, claim_id, section_id, and content_hash registry
    claim_bank.json            # Canonical claim state
    entity_index.json          # Entity-to-claim lookup for graph relationship hints
    claim_slices/              # Per-section claim/source slices for report composition
    section_briefs/            # Compact per-section briefs that reference claim IDs
    claim_graph_map.json       # Claim-to-graph relationship metadata
    section_graph_hints.json   # Advisory graph hints for planned sections
    research_notes.md          # Optional diagnostics; not a canonical handoff
    citation_audit.md          # Citation verification report
    gap_analysis.md            # Gap detection output
  output/
    report.md                  # Polished markdown (from research-format)
    assembly_plan.json         # Lightweight report composition plan
    formatter_audit.json       # Formatter/assembler validation audit
    publish_log.md             # Publishing/render log
    sections/                  # Section markdown and section metadata
    report.qmd                 # Optional publishing source generated from report.md
    report.html                # Optional rendered output
    report.pdf                 # Optional rendered output
  checkpoints/                 # Durable intermediate state for resume
  logs/
    run_log.md                 # Timestamped action log
```

## Required Subdirectories

The following 9 subdirectories MUST exist within a run directory. They are created on first use by the phase that owns them (not by `init_run.py`).

| # | Path | Created By | Purpose |
|---|------|-----------|---------|
| 1 | `scope/` | research (at Step 8 of scope planning, lazily via mkdir(exist_ok=True)) | Holds scope.md, plan.json, question_tree.json |
| 2 | `collect/` | research-collect | Root for all collection artifacts |
| 3 | `collect/evidence/` | research-collect | Individual evidence markdown files with provenance headers |
| 4 | `collect/quarantine/` | research-collect | Quarantined items excluded from synthesis |
| 5 | `collect/graphify-out/` | research (legacy graphify invocation) | Raw Graphify outputs and diagnostics |
| 6 | `synthesis/` | research-synthesize | Root for claim bank, slices, graph hints, and briefs |
| 7 | `synthesis/claim_slices/` | research-synthesize | Per-section claim/source slices |
| 8 | `synthesis/section_briefs/` | research-synthesize | Per-section compact briefs |
| 9 | `output/` | research-format | Canonical report, composition metadata, and publishing outputs |
| 10 | `output/sections/` | research-format | Section-level markdown and metadata |
| 11 | `checkpoints/` | research | Durable intermediate state for run resume |
| 12 | `logs/` | research | Timestamped action logs |

## Initialization

`init_run.py` creates:
- The run directory `research/run-NNN-TIMESTAMP/`
- `manifest.json` with run metadata, budget config, and all phases set to `pending`

Subdirectories are created lazily by downstream phases on first use. This avoids creating empty directories for phases that may not execute (e.g., if a run is aborted after collection).

## File Ownership

| File | Producer | Consumer(s) |
|------|----------|-------------|
| `manifest.json` | init_run.py / orchestrator | All phases (read phase_status) |
| `collect/inventory.json` | research-collect | research-synthesize, orchestrator |
| `collect/evidence/*.md` | research-collect | research-synthesize |
| `collect/collection_log.md` | research-collect | orchestrator (checkpoint gate 2) |
| `collect/coverage_matrix.md` | research-collect | orchestrator (checkpoint gate 2) |
| `collect/graphify-out/*` | graphify (via orchestrator) | graph_relationships phase |
| `synthesis/global_id_registry.json` | research-synthesize | research-synthesize, research-format |
| `synthesis/claim_bank.json` | research-synthesize | orchestrator (checkpoint gate 3), section brief synthesis |
| `synthesis/entity_index.json` | research-synthesize | graph_relationships phase |
| `synthesis/claim_slices/*.json` | research-synthesize | research-format section agents |
| `synthesis/section_briefs/*.json` | research-synthesize | research-format |
| `synthesis/claim_graph_map.json` | graph_relationships phase | section brief synthesis |
| `synthesis/section_graph_hints.json` | graph_relationships / section brief synthesis | research-format |
| `synthesis/research_notes.md` | research-synthesize | Optional diagnostics only |
| `synthesis/raw_research.md` | legacy research-synthesize | Deprecated; optional compatibility artifact only |
| `synthesis/claim_index.json` | legacy research-synthesize | Deprecated; compatibility artifact derived from claim_bank.json if needed |
| `synthesis/citation_audit.md` | research-synthesize | orchestrator (checkpoint gate 3) |
| `synthesis/gap_analysis.md` | research-synthesize | orchestrator (gap-fill decision) |
| `synthesis/evidence_routing.json` | orchestrator (pre-synthesis) | Per-evidence-file cluster assignments with routing_confidence |
| `output/assembly_plan.json` | research-format | Section agents, final assembler |
| `output/sections/*.md` | research-format | final assembler |
| `output/sections/*.meta.json` | research-format | final assembler, formatter audit |
| `output/report.md` | research-format | End user, publishing phase |
| `output/formatter_audit.json` | research-format | orchestrator (Gate 4), publishing phase |
| `output/report.qmd` | publishing phase | Quarto source generated from canonical `output/report.md` |
| `output/report.html` | publishing phase | End user |
| `output/report.pdf` | publishing phase | End user |
| `output/publish_log.md` | publishing phase | End user, orchestrator |
| `checkpoints/*` | research | research (resume) |
| `logs/run_log.md` | research | End user (audit trail) |

## Context Slicing Rule

A global file is considered tiny only if it is under 20KB or under 300 lines. If `claim_bank.json`, `inventory.json`, graph outputs, or all section briefs exceed that limit, downstream agents must consume per-section slices instead of reading the global file.

`claim_bank.json` is canonical. `categorized_evidence.json` is not a required artifact in this contract version.
