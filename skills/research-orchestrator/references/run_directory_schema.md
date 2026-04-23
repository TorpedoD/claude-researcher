# Run Directory Schema

**Version:** 1.0
**Owner:** research-orchestrator
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
    raw_research.md            # Citation-rich first-pass research
    claim_index.json           # Claim-to-source mapping
    citation_audit.md          # Citation verification report
    gap_analysis.md            # Gap detection output
  output/
    report.md                  # Polished markdown (from research-format)
    report.qmd                 # Quarto-ready output
  checkpoints/                 # Durable intermediate state for resume
  logs/
    run_log.md                 # Timestamped action log
```

## Required Subdirectories

The following 9 subdirectories MUST exist within a run directory. They are created on first use by the phase that owns them (not by `init_run.py`).

| # | Path | Created By | Purpose |
|---|------|-----------|---------|
| 1 | `scope/` | research-orchestrator (at Step 8 of scope planning, lazily via mkdir(exist_ok=True)) | Holds scope.md, plan.json, question_tree.json |
| 2 | `collect/` | research-collect | Root for all collection artifacts |
| 3 | `collect/evidence/` | research-collect | Individual evidence markdown files with provenance headers |
| 4 | `collect/quarantine/` | research-collect | Quarantined items excluded from synthesis |
| 5 | `collect/graphify-out/` | research-orchestrator (graphify invocation) | Knowledge graph outputs |
| 6 | `synthesis/` | research-synthesize | Root for all synthesis artifacts |
| 7 | `output/` | research-format | Formatted research outputs |
| 8 | `checkpoints/` | research-orchestrator | Durable intermediate state for run resume |
| 9 | `logs/` | research-orchestrator | Timestamped action logs |

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
| `collect/graphify-out/*` | graphify (via orchestrator) | research-synthesize |
| `synthesis/raw_research.md` | research-synthesize | research-format, orchestrator |
| `synthesis/claim_index.json` | research-synthesize | orchestrator (checkpoint gate 3) |
| `synthesis/citation_audit.md` | research-synthesize | orchestrator (checkpoint gate 3) |
| `synthesis/gap_analysis.md` | research-synthesize | orchestrator (gap-fill decision) |
| `synthesis/citation_registry.json` | orchestrator (pre-synthesis) | Frozen global `[N]`→URL mapping built from inventory.json |
| `synthesis/evidence_routing.json` | orchestrator (pre-synthesis) | Per-evidence-file cluster assignments with routing_confidence |
| `synthesis/density_hints.json` | research-formatter | Per-section advisory hints from density_scan.py |
| `synthesis/assembly_overlaps.md` | research-synthesizer (assemble mode) | Fan-out runs only: duplicate subsections resolved, cross-ref repairs |
| `output/report.md` | research-format | End user |
| `output/report.qmd` | research-format | Quarto rendering |
| `output/formatter_decisions.md` | research-formatter | Audit log of claim movements, table/diagram decisions |
| `checkpoints/*` | research-orchestrator | research-orchestrator (resume) |
| `logs/run_log.md` | research-orchestrator | End user (audit trail) |
