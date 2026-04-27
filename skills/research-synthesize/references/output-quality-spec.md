# Claim Pipeline Output Quality Specification

**Purpose:** Active quality rules for `claim_pipeline_v1` synthesis artifacts.
The synthesizer creates exhaustive structured research memory; the formatter
turns selected claims into final prose.

**Consumers:** research-synthesize SKILL.md and claim-pipeline validation.

## Canonical Research Memory

`synthesis/claim_bank.json` is exhaustive. It should preserve every supported
atomic claim that is relevant to the approved research scope, including low
salience, diagnostic, contradictory, or non-final claims.

Each claim records:

- stable `id`
- full `text`
- `content_hash`
- one `primary_section_id`
- supporting `source_ids`
- `confidence`
- `salience`
- `include_in_report`
- optional `entities` and contradiction links

`synthesis/entity_index.json` is derived from extracted claim entities and is
the normal graph input together with `claim_bank.json`.

## Report Inclusion

`output/report.md` is selective final communication, not a dump of research
memory. Inclusion is controlled by:

- `include_in_report`
- claim `salience`
- approved section depth
- section purpose and audience
- required-vs-optional placement in `section_briefs/*.json`

Do not require final prose to enumerate every distinct fact at medium or high
depth. Completeness belongs in `claim_bank.json`; report usefulness comes from
selection, structure, and faithful citation of the selected claims.

## Claim Slices

`synthesis/claim_slices/<section_id>.json` is a compact self-contained working
packet for one section writer. It contains:

- `required_claims`: compact full claim objects with text
- `optional_claims`: compact briefs with claim IDs and routing metadata
- `source_records`: only sources allowed for that section
- `boundary_rules`

Section writers must not read global claim state during normal report
composition.

## Citation Ownership

Synthesis owns claim-to-source linkage. The formatter owns citation rendering.
Formatter audit owns citation validation.

Final report citations use title links:

```markdown
[Source Title](url)
```

## Legacy Raw-Research Notes

Older raw-research handoff rules are deprecated for `claim_pipeline_v1`. If a
prose diagnostic is useful, write `synthesis/research_notes.md`; it is not a
formatter input and is not the canonical report source.
