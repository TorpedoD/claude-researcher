# Architecture Execution Plan

This plan fixes contract drift across dependency modes, checkpoint gates, resume,
depth taxonomy, and README promises. It is the maintainer checklist for keeping
the research pipeline coherent.

## Target Responsibilities

| Component | Owns | Does not own |
|-----------|------|--------------|
| Orchestrator | Phase dispatch, checkpoint gates, manifest updates, resume dispatch | Tool installation, extraction implementation, deep artifact validation logic |
| Preflight | Tool/runtime checks, TinyTeX advisory checks, source-channel-to-mode resolution | User interviews |
| Manifest | Run state machine, normalized user-facing configuration, resolved environment metadata | Freeform settings or duplicated phase-local config |
| Validators | Artifact existence, schema checks, readiness checks | Phase execution |
| Phase skills | Collection, synthesis, formatting, publishing | Cross-phase state machine decisions |

## Execution Order

1. Normalize dependency modes.
   - Persist only `web_and_docs`, `docs_only`, `web_only`, or `metadata_only`.
   - Accept legacy `none` only as an alias that resolves to `metadata_only`.
   - Hard requirements:
     - `web_and_docs`: Crawl4AI, Playwright browser runtime, Docling.
     - `docs_only`: Docling.
     - `web_only`: Crawl4AI and Playwright browser runtime.
     - `metadata_only`: no extraction tools; inventory/resume metadata only.
   - If required tools are missing, stop and show install commands. Do not switch modes automatically.

2. Simplify Gate 1.
   - Ask one combined checkpoint question only.
   - Show scope, budget, source channels, `collection_mode`, global `depth`, `audience`, `tone`, and `render_targets`.
   - Default implementation knobs:
     - `performance_mode=auto`
     - `validation_mode=normal`
     - `section_depth_overrides={}`
   - TinyTeX is an automatic advisory preflight, not a blocking question.

3. Keep Gate 4 as report approval.
   - Gate 4 occurs after `output/report.md` and formatter audit are produced.
   - Gate 4 approves the canonical Markdown report before optional publishing.
   - Post-run diagnostics and improvement notes are non-blocking final summary material, not a gate.

4. Make resume machine-readable and dispatchable.
   - `init_run.py --resume RUN_ID --json` emits `run_id`, `run_dir`, `next_phase`, `completed_phases`, `problem_phases`, `required_artifacts`, `artifact_status`, `dispatch`, and `recommended_command`.
   - Orchestrator dispatch table:
     - `planning`: resume planning and Gate 1 only if artifacts are incomplete.
     - `collection`: run collector unless `collection_mode=metadata_only`, then validate existing metadata and advance.
     - `claim_extraction`: run synthesizer claim extraction.
     - `graph_relationships`: run graph enrichment.
     - `section_brief_synthesis`: run section brief synthesis.
     - `formatting`: run formatter.
     - `publishing`: run publisher.
   - Resume must validate required artifacts before skipping phases.

5. Normalize output taxonomy.
   - Use one global `depth`: `summary`, `standard`, `comprehensive`, or `audit`.
   - Keep separate fields:
     - `audience`: `internal`, `external`, `technical`, `executive`.
     - `tone`: `concise`, `professional`, `explanatory`.
     - `render_targets`: `md`, `qmd`, `html`, `pdf`.
   - Per-section overrides use `section_depth_overrides` with the same depth enum.
   - Do not introduce legacy fallback labels, `full`, `low`, `medium`, or `high` as active configuration values.

6. Keep README promises exact.
   - Resume language must say that prior artifacts are detected and phases continue from the next valid phase when required artifacts pass validation.
   - Avoid absolute resume guarantees unless enforcement exists in code.

## Verification Checklist

- `rg` finds no active fallback collection mode labels.
- Active dependency docs list `metadata_only`, not `none`, except where documenting legacy alias support.
- Gate 1 has one checkpoint question and no separate implementation-knob interview.
- Gate 3 does not ask for output preferences.
- Gate 4 is report approval before optional publishing.
- `--resume RUN_ID --json` includes a dispatchable `next_phase` and `dispatch`.
- Tests cover `metadata_only`, legacy `none` aliasing, and resume JSON dispatch.
