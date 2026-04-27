---
name: research-format
description: Claim-sliced report composer for research-orchestrator Phase 6. Writes canonical output/report.md from section briefs and claim slices; publishing renders optional formats later.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# Research Format Skill

Composes the canonical Markdown report for `claim_pipeline_v1`.

This skill is a report composer, not a researcher and not a publisher. It writes
`output/report.md` from compact structured research state. HTML, PDF, and QMD
outputs are generated later by the publishing phase from `output/report.md`.

## Required Inputs

When invoked by `research-orchestrator`, use only:

| Input | Path | Purpose |
|---|---|---|
| Format preferences | `manifest.json` | mode, audience, tone, publish preference |
| Section briefs | `synthesis/section_briefs/<section_id>.json` | section title, summary, required claim IDs, boundaries |
| Claim slices | `synthesis/claim_slices/<section_id>.json` | only claim text and source records available to a section |
| Graph hints | `synthesis/section_graph_hints.json` | advisory per-section relationships only |

The formatter must not read these files in the main path:

- `synthesis/raw_research.md`
- `synthesis/claim_bank.json`
- `collect/inventory.json`
- full Graphify outputs
- `collect/graphify-out/GRAPH_REPORT.md`

Missing claim slices are fatal. Do not fall back to `claim_bank.json`.

## Required Outputs

- `output/assembly_plan.json`
- `output/sections/<section_id>.md`
- `output/sections/<section_id>.meta.json`
- `output/report.md`
- `output/formatter_audit.json`

Do not write `output/report.qmd`, `output/report.html`, or `output/report.pdf`.
Those belong to publishing.

## Citation Contract

All citations use one global format:

```markdown
[Source Title](url)
```

Numeric citations such as `[1](url)` or `[1]` are disallowed. Mixed citation
styles fail the formatter audit.

## Composition Flow

1. Build the assembly plan:

   ```bash
   python3 ~/.claude/skills/research-format/scripts/report_composer.py \
     build-plan --run-dir "$run_dir"
   ```

2. For each assembly-plan section, read only:
   - `section_brief_path`,
   - `claim_slice_path`,
   - graph hints matching the same `section_id`,
   - format preferences.

3. Compose `output/sections/<section_id>.md`.
   - Start with `## <Section Title>`.
   - Open with a short summary.
   - Include every `must_include_claim_id`.
   - Include optional claims only when useful for the selected depth.
   - Preserve missing-evidence notes and contradictions.
   - Use graph hints only for central entities, cross-links, and relationship language inside the existing planned section.
   - Do not let graph hints create, remove, or reorder sections.

4. Emit `output/sections/<section_id>.meta.json`.
   - `claim_ids_used` must include all required claims used in prose, tables, or diagrams.
   - `source_ids_used` must be a subset of the section claim slice.
   - `cross_links` must reference existing planned section IDs only.
   - `warnings` should record skipped optional claims, weak evidence, or unresolved overlap.

5. Assemble the canonical report:

   ```bash
   python3 ~/.claude/skills/research-format/scripts/report_composer.py \
     assemble --run-dir "$run_dir"
   ```

6. Run the audit:

   ```bash
   python3 ~/.claude/skills/research-format/scripts/report_composer.py \
     audit --run-dir "$run_dir"
   ```

   Formatting is not complete until `formatter_audit.json` has no errors.

## Writing Rules

- The report must be useful as Markdown without any rendered format.
- Every factual sentence must be grounded in claims from the active section slice.
- The formatter may omit low-salience optional claims unless depth is comprehensive or audit-oriented.
- Do not invent claims, URLs, source titles, statistics, or graph relationships.
- Tables are preferred for comparisons of three or more comparable items.
- Mermaid diagrams are allowed only when they clarify a process or relationship.
- Paragraphs longer than five sentences should be split into bullets, tables, or subheadings.

## Assembler Rules

The assembler may:

- concatenate sections in approved order,
- normalize heading levels,
- build the table of contents,
- generate a source list from actually used source IDs,
- remove duplicate intros,
- fix light transitions,
- flag or lightly merge obvious overlaps.

The assembler may not:

- reread evidence,
- reinterpret claims,
- rewrite whole sections,
- add uncited factual content,
- silently drop unique claims.

## Legacy Raw-Research Mode

`density_scan.py`, `coverage_audit.py`, `raw_research.md`, and
`claim_index.json` are legacy compatibility mechanisms. They are not used for
new `claim_pipeline_v1` runs.
