# Information Levels (L0 / L1 / L2)

The formatter applies a three-tier progressive disclosure taxonomy to every `##` section.

## Tier Definitions

| Level | Name | Purpose | Word budget / section (Full Report) | Word budget / section (Summary) |
|-------|------|---------|-------------------------------------|---------------------------------|
| L0 | Skim | Headline claim + single-sentence takeaway | ≤80 words | ≤40 words |
| L1 | Study | Short Summary + Key Points + one primary visual | 200–450 words | 120–250 words |
| L2 | Reference | Detailed Findings with all surfaced claims, supplementary visuals | No upper bound; formatter-selected | Collapsed into L1 |

## Level Assignment

Every section gets at minimum L0 + L1.

L2 is added when:
- `density_hints.json` reports `suggested_level == "reference"` for this section, OR
- `manifest.format_preferences.mode == "Full Report"`

In Summary mode, L2 is collapsed: Detailed Findings are moved to `### Supplementary Findings` (still visible, per FMT-01, but below the fold).

## Per-Level Content Contracts

### L0 (Skim)
- One bold headline sentence (the most important single fact)
- One sentence: why this matters

### L1 (Study)
- **Short Summary**: 2–3 sentences covering the what/why/how
- **Key Points**: 3–6 bullet points, each ≤25 words, each with a citation
- **Primary Visual** (if density hints suggest one): one table OR one diagram per DENS-01 budget
- **Teaching Layer** (if tone=teachy): one analogy + "why this matters" paragraph

### L2 (Reference)
- **Detailed Findings**: prose + all cited claims not surfaced in L1
- **Supplementary Findings** (`###`): claims moved here from body per FMT-01
- **Additional visuals**: up to DENS-01 secondary cap
- **Cross-references**: `(See [Other Section](#anchor))`

## Structural Example

```markdown
## Consensus Mechanisms

**L0:** Raft achieves consensus through leader-based log replication with randomized election timeouts.

### Short Summary (L1)

Raft separates leader election from log replication to simplify reasoning about correctness... [2–3 sentences]

### Key Points (L1)

- Election timeouts range from 150–300 ms by default [1](url)
- A candidate needs majority votes to become leader [2](url)
- Log entries are committed only after majority acknowledgment [1](url)

### Leader Election (L2)

[Detailed Findings — all remaining cited claims]

### Supplementary Findings (L2 — moved claims)

[Lower-salience claims moved here per FMT-01]

### Section References

[1](url) — etcd Documentation
[2](url) — Raft Paper
```
