# Checkpoint Protocol

The research pipeline has 4 human verification gates. Each gate prints its summary table to chat before the `AskUserQuestion` call (TUI menu by default, plain-text fallback with `--text` flag or `workflow.text_mode: true`). Do not embed large tables inside the question payload.

Gates are mandatory unless the run is resuming past a completed phase.

---

## Gate 1: Post-Planning

**Trigger:** After the orchestrator completes scope planning, before spawning the collector agent.

**Data shown (summary table):**

| Field | Source |
|-------|--------|
| Research question | `user_request` from `manifest.json` |
| Subtopics | `subtopics[]` from `plan.json` |
| Source types | `expected_source_types[]` from `plan.json` |
| Source channels | `source_channels` from `manifest.json` or `plan.json` |
| Collection mode | `collection_mode` from `manifest.json` |
| Depth | `depth` from `manifest.json` |
| Audience | `audience` from `manifest.json` |
| Tone | `tone` from `manifest.json` |
| Render targets | `render_targets` from `manifest.json` |
| Validation mode | `validation_mode` from `manifest.json` |
| Performance mode | `runtime_profile.performance_mode_used` from `manifest.json`; default is `auto` |
| Coverage areas | `estimated_coverage_areas[]` from `plan.json` |
| Priority ranking | `priorities[]` from `plan.json` |
| Budget | `budget_config` from `manifest.json` (max_pages, max_per_domain, max_depth) |
| Task type | new / update / expansion / re-audit |
| LaTeX pre-flight | `environment.tinytex_available` from `manifest.json` (boolean; advisory only — populated by the `quarto check` pre-flight step before Gate 1). If `false`, the orchestrator prepends an advisory warning ("⚠️ TinyTeX not detected. PDF output will be unavailable or will render-fail gracefully. Install with: quarto install tinytex") to the Gate 1 summary. This is **advisory, not blocking** — the user may still Confirm. PDF-inclusive output targets are annotated with a "(requires TinyTeX — not detected)" caveat. |

**User options:**

1. **Approve plan** -- Proceed with current scope, depth, output targets, and source channels. The orchestrator writes `scope.md` and `plan.json`, validates `plan.json` against `plan.schema.json`, and marks planning as complete.
2. **Edit scope/depth/output** -- Modify scope, budget, source channels, global depth, audience, tone, render targets, or explicit `section_depth_overrides`. The user provides changes as free text. The orchestrator re-plans with the adjustments and re-displays the summary table for another confirmation round.
3. **Abort** -- Cancel the run. The orchestrator marks planning as `failed` in the manifest and stops.

**Resume behavior:** If the run resumes after planning is already `complete`, skip this gate entirely. The scope and plan artifacts already exist on disk.

---

## Gate 2: Post-Collection

**Trigger:** After the collector agent completes and `inventory.json` is validated, before the graph phase.

**Data shown (summary table):**

| Field | Source |
|-------|--------|
| Total sources collected | Count of `sources[]` in `inventory.json` |
| Sources by tier | Count per tier 1-5 from `inventory.json` |
| Topic coverage | `coverage_matrix.md` summary (Strong/Moderate/Weak/None per topic) |
| Quarantined items | Count of files in `collect/quarantine/` |
| Suspicious items | Count of sources where `suspicious=true` in `inventory.json` |
| Budget usage | pages_used / max_pages from `collection_log.md` |
| Weak areas | Topics with "Weak" or "None" coverage rating |

**User options:**

1. **Proceed** -- Continue to graph construction and synthesis. The orchestrator marks collection as complete and begins the graph phase.
2. **Flag issues** -- Note concerns about collection quality or coverage. Concerns are logged to `logs/run_log.md` with a timestamp. The pipeline proceeds despite flagged issues (they inform the synthesizer's gap analysis).
3. **Abort** -- Cancel the run. The orchestrator marks collection as `failed` in the manifest and stops.

**Resume behavior:** If the run resumes after collection is already `complete`, skip this gate. All collection artifacts exist on disk.

---

## Gate 3: Claim State Review

**Trigger:** After claim extraction, graph relationships, and section brief synthesis complete, before the formatting/report composition phase.

**Data shown (summary table):**

| Field | Source |
|-------|--------|
| Strongest areas | Sections with most high-confidence, high-salience claims from `claim_bank.json` |
| Weakest areas | Sections with missing evidence, low-confidence claims, or weak source tiers from `claim_bank.json` and section briefs |
| Gap-fill status | "Not triggered" / "Triggered: N additional pages collected, M new claims added" |
| Total claims | `metadata.total_claims` from `claim_bank.json` |
| Included claims | Count of claims where `include_in_report=true` |
| Avg sources/claim | Derived from `claims[].source_ids` in `claim_bank.json` |
| Citation audit | Pass/fail summary from `citation_audit.md` |
| Validation warnings | Any warnings from `validate_artifact.py` on `claim_bank.json` and section brief schemas |
| Context slicing | Whether downstream inputs fit the tiny-file rule: under 20KB or under 300 lines |

**User options:**

1. **Proceed to format** -- Continue to formatting/report composition using the normalized output settings approved at Gate 1, then invokes the research-format skill.
2. **Request gap-fill** -- Force a gap-fill iteration even if automatic thresholds were not met. The orchestrator spawns the collector with `--max-pages 20` targeting specific weak areas identified in `gap_analysis.md`, then re-runs the synthesizer for a second pass. Maximum 1 gap-fill iteration total (if gap-fill already ran automatically, this option is unavailable).
3. **Abort** -- Cancel the run. The orchestrator marks synthesis as `failed` in the manifest and stops.

**Output settings:**

Gate 3 does not repeat Gate 1's output settings interview. The orchestrator verifies these normalized fields exist in `manifest.json`; if a resumed or legacy run lacks them, write the defaults before formatting.

| Field | Enum | Default (D-05) |
|-------|------|----------------|
| `depth` | summary / standard / comprehensive / audit | standard |
| `audience` | internal / external / technical / executive | external |
| `tone` | concise / professional / explanatory | professional |
| `render_targets` | md / qmd / html / pdf | md + html |

**TinyTeX caveat:** If `manifest.environment.tinytex_available == false`, PDF-inclusive Gate 1 output targets are shown with the suffix `"(requires TinyTeX — not detected)"` rather than suppressed. The publishing phase graceful render fallback handles any render failure without invalidating `output/report.md`.

Defaults are written to normalized manifest fields if Gate 3 is skipped (e.g., resume past `section_brief_synthesis: complete`) so formatting always has a deterministic configuration.

**Resume behavior:** If the run resumes after `section_brief_synthesis` is already `complete`, skip this gate. Claim bank, graph hints, and section brief artifacts already exist on disk. The orchestrator ensures normalized output fields are populated (defaults if absent) before formatting runs.

---

## Gate 4: Report Approval

**Trigger:** After formatting/report composition writes `output/report.md`, before optional publishing.

**Data shown (summary table):**

| Field | Source |
|-------|--------|
| Canonical report | `output/report.md` |
| Section count | `output/assembly_plan.json` |
| Claims used | `output/sections/*.meta.json` and `output/formatter_audit.json` |
| Source count | Cited source IDs from section metadata |
| Formatter audit | `output/formatter_audit.json` status, warnings, and errors; missing is warning-only in normal validation mode |
| Publishing targets | `manifest.render_targets` |

**User options:**

1. **Approve report** -- Proceed to the publishing phase if any non-Markdown targets were requested.
2. **Skip publishing** -- Finalize with `output/report.md` only.
3. **Abort** -- Preserve `output/report.md` and mark downstream publishing incomplete.

**Resume behavior:** If the run resumes after formatting is already `complete`, skip this gate if `output/report.md` exists. Missing `output/formatter_audit.json` warns in normal validation mode and fails only in strict mode.

---

## UX Modes

### TUI Mode (default)

Use `AskUserQuestion` with concise menu options. Print the summary table to chat immediately before the question, then present numbered options.

**Example pattern:**

```
AskUserQuestion(
  question="Review the post-planning summary above. How would you like to proceed?",
  options=["Confirm", "Adjust", "Abort"]
)
```

### Text Mode (fallback)

Activated by `--text` CLI flag or `workflow.text_mode: true` in Claude Code config.

Display the same summary table as plain text. Present options as a numbered list. The user responds with a number.

**Example pattern:**

```
Post-Planning Review
====================

Research question: How does X work?
Subtopics: A, B, C
Source types: official docs, academic papers
...

Options:
  1. Confirm - proceed to collection
  2. Adjust - modify scope
  3. Abort - cancel run

Enter option number:
```

Same pattern as `gsd-discuss-phase` text mode. The orchestrator checks `workflow.text_mode` config before each gate and selects the appropriate display format.

---

---

## Gate Summary

| Gate | Trigger | Key Data | Options | Phase Affected |
|------|---------|----------|---------|----------------|
| 1 | Post-Planning | Subtopics, source channels, depth, outputs, budget | Approve plan / Edit scope-depth-output / Abort | planning |
| 2 | Post-Collection | Coverage %, tier counts, quarantine | Proceed / Flag issues / Abort | collection |
| 3 | Claim State Review | Claim bank, section briefs, coverage, slicing status | Proceed to format / Request gap-fill / Abort | section_brief_synthesis |
| 4 | Report Approval | report.md, assembly plan, formatter audit, publishing targets | Approve report / Skip publishing / Abort | formatting |
