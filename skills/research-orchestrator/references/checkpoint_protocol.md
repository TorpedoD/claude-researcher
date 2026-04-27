# Checkpoint Protocol

The research pipeline has 4 human verification gates. Each gate presents a summary table via `AskUserQuestion` (TUI menu by default, plain-text fallback with `--text` flag or `workflow.text_mode: true`).

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
| Coverage areas | `estimated_coverage_areas[]` from `plan.json` |
| Priority ranking | `priorities[]` from `plan.json` |
| Budget | `budget_config` from `manifest.json` (max_pages, max_per_domain, max_depth) |
| Task type | new / update / refresh / expansion / re-audit |
| LaTeX pre-flight | `environment.tinytex_available` from `manifest.json` (boolean; advisory only — populated by the `quarto check` pre-flight step before Gate 1). If `false`, the orchestrator prepends an advisory warning ("⚠️ TinyTeX not detected. PDF output will be unavailable at Gate 3 (or will render-fail gracefully). Install with: quarto install tinytex") to the Gate 1 summary. This is **advisory, not blocking** — the user may still Confirm. Gate 3 consumes this field to either suppress PDF options or annotate them with a "(requires TinyTeX — not detected)" caveat. |

**User options:**

1. **Confirm** -- Proceed to collection with current scope. The orchestrator writes `scope.md` and `plan.json`, validates `plan.json` against `plan.schema.json`, and marks planning as complete.
2. **Adjust** -- Modify subtopics, priorities, or budget. The user provides changes as free text. The orchestrator re-plans with the adjustments and re-displays the summary table for another confirmation round.
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

1. **Proceed to format** -- Continue to formatting/report composition. The orchestrator marks section brief synthesis as complete, collects **format preferences (Part B)**, then invokes the research-format skill.
2. **Request gap-fill** -- Force a gap-fill iteration even if automatic thresholds were not met. The orchestrator spawns the collector with `--max-pages 20` targeting specific weak areas identified in `gap_analysis.md`, then re-runs the synthesizer for a second pass. Maximum 1 gap-fill iteration total (if gap-fill already ran automatically, this option is unavailable).
3. **Abort** -- Cancel the run. The orchestrator marks synthesis as `failed` in the manifest and stops.

**Part B — Format preferences (D-03, only if "Proceed to format"):**

Collected via AskUserQuestion (controlled enum responses only — no freeform input). Written to `manifest.json` under `format_preferences`.

| Field | Enum | Default (D-05) |
|-------|------|----------------|
| `mode` | Full Report / Summary / Documentation | Full Report |
| `audience` | External / Personal | External |
| `tone` | Professional / Teachy | Professional |
| `quarto_output` | none / html / pdf / both | html |

**TinyTeX caveat:** If `manifest.environment.tinytex_available == false`, PDF and Both options are shown with the suffix `"(requires TinyTeX — not detected)"` rather than suppressed. The publishing phase graceful render fallback handles any render failure without invalidating `output/report.md`.

Defaults are written to `manifest.format_preferences` if Gate 3 is skipped (e.g., resume past `section_brief_synthesis: complete`) so formatting always has a deterministic configuration.

**Resume behavior:** If the run resumes after `section_brief_synthesis` is already `complete`, skip this gate. Claim bank, graph hints, and section brief artifacts already exist on disk. The orchestrator ensures `manifest.format_preferences` is populated (defaults if absent) before formatting runs.

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
| Formatter audit | `output/formatter_audit.json` status, warnings, and errors |
| Publishing targets | `manifest.publish_preferences.targets` or defaults derived from format preferences |

**User options:**

1. **Approve report** -- Proceed to the publishing phase if any non-Markdown targets were requested.
2. **Skip publishing** -- Finalize with `output/report.md` only.
3. **Abort** -- Preserve `output/report.md` and mark downstream publishing incomplete.

**Resume behavior:** If the run resumes after formatting is already `complete`, skip this gate only if `output/report.md` and `output/formatter_audit.json` exist.

---

## UX Modes

### TUI Mode (default)

Use `AskUserQuestion` with formatted menu options. Display the summary table as a formatted text block within the question prompt, then present numbered options.

**Example pattern:**

```
AskUserQuestion(
  question="## Post-Planning Review\n\n| Field | Value |\n|---|---|\n| Research question | How does X work? |\n| Subtopics | A, B, C |\n| ... | ... |\n\nSelect an option:\n1. Confirm - proceed to collection\n2. Adjust - modify scope\n3. Abort - cancel run",
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
| 1 | Post-Planning | Subtopics, source types, budget | Confirm / Adjust / Abort | planning |
| 2 | Post-Collection | Coverage %, tier counts, quarantine | Proceed / Flag issues / Abort | collection |
| 3 | Claim State Review | Claim bank, section briefs, coverage, slicing status | Proceed to format / Request gap-fill / Abort | section_brief_synthesis |
| 4 | Report Approval | report.md, assembly plan, formatter audit, publishing targets | Approve report / Skip publishing / Abort | formatting |
