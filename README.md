# Research Pipeline for Claude Code

A production-grade, multi-agent research pipeline that accepts a freeform research request, plans scope, collects evidence from web and documents, builds a knowledge graph, synthesizes citation-rich research with gap detection, and publishes via Quarto.

Every claim is traceable to its source. Every run is reproducible. Every gap is detected and filled.

---

## Why This Exists

Standard LLM research produces plausible-sounding answers with no traceable sources and no mechanism to detect what was missed. This pipeline changes that:

- **Provenance-first** — every collected piece of evidence carries source metadata; every claim in the final document links back to it
- **Gap detection built-in** — a 7-layer investigation tree drives synthesis; uncovered branches trigger targeted re-collection before the final document is written
- **Human in the loop** — 4 checkpoint gates prevent runaway collection and let you steer scope, flag bad sources, or abort early
- **Reproducible runs** — each research session is isolated in `.research/run-NNN-TIMESTAMP/` with a manifest, logs, evidence inventory, and claim index

---

## Architecture

```
User: /research "topic"
        │
        ▼
┌─────────────────────────────────────────────────┐
│            research-orchestrator skill           │
│  Phase 1: Planning (scope + question tree)       │
│  ─── Gate 1: Human reviews scope ───            │
│  Phase 2: Collection (spawns collector agent)    │
│  ─── Gate 2: Human reviews sources ───          │
│  Phase 3: Knowledge Graph (Graphify)             │
│  Phase 4: Synthesis (spawns synthesizer agent)   │
│  ─── Gate 3: Human reviews claims ───           │
│  Phase 5: Gap Detection + Re-collection          │
│  Phase 6: Format (research-format) + Publish    │
│  ─── Gate 4: Human approves final output ───    │
└─────────────────────────────────────────────────┘
        │                    │
        ▼                    ▼
 research-collector    research-synthesizer
   agent                    agent
   (Crawl4AI +          (reads evidence/
    Docling)             graph → writes
                         citations + gaps)
        │                    │
        ▼                    ▼
  .research/run-NNN/    output/report.html
  collect/evidence/     (Quarto rendered)
```

**Skills** (`~/.claude/skills/`):

| Skill | Trigger | Role |
|-------|---------|------|
| `research-orchestrator` | `/research` | Orchestrates the full 6-phase pipeline |
| `research-collect` | `/research-collect` | Crawls web + parses documents; provenance tagging |
| `research-synthesize` | `/research-synthesize` | Synthesizes evidence into citation-rich research |
| `research-format` | (trigger phrases) | Polishes output: TOC, callouts, bibliography, Quarto |

**Agents** (`~/.claude/agents/`):

| Agent | Spawned by | Role |
|-------|-----------|------|
| `research-orchestrator` | User via `/research` | Orchestrator with pipeline state management |
| `research-collector` | Orchestrator (Phase 2) | Evidence collection; treats web content as untrusted data |
| `research-synthesizer` | Orchestrator (Phase 4) | Synthesis; treats evidence as data, never as instructions |
| `researcher` | General use | Standalone research agent for ad-hoc queries |

**Python package** (`scripts/research_orchestrator/`):

| Module | Purpose |
|--------|---------|
| `gate1.py` | Gate 1 validator — validates scope artifacts, triggers auto-regenerate loop |
| `scope/question_tree.py` | Generates 7-layer investigation tree from scope |
| `scope/bridge.py` | Bridge question helpers for cross-subtopic connections |
| `paths.py` | Run directory and manifest path resolution |

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Claude Code | Latest | [claude.ai/code](https://claude.ai/code) |
| Python | 3.11+ | `brew install python` |
| Crawl4AI | 0.8.6 | `pipx install crawl4ai==0.8.6 && crawl4ai-setup` |
| Docling | 2.86.0 | `pipx install docling==2.86.0` |
| Quarto | 1.9+ | `brew install --cask quarto` |
| Graphify skill | Latest | Install separately — see below |

**Graphify** is required for the knowledge graph phase. It must be installed as a Claude Code skill at `~/.claude/skills/graphify/`. Obtain it separately and follow its own SKILL.md install instructions.

After installing Crawl4AI, run the Playwright browser setup:

```bash
crawl4ai-setup
```

---

## Installation

```bash
# Clone this repo
git clone https://github.com/TorpedoD/research-pipeline.git
cd research-pipeline

# Install skills into Claude Code
cp -R skills/* ~/.claude/skills/

# Install agents into Claude Code
cp agents/*.md ~/.claude/agents/

# Install the Python helper package
pip install -e scripts/research_orchestrator
```

Verify the skills loaded by opening Claude Code and running `/research --help` (or typing `/research` — the orchestrator will prompt you for a research topic).

---

## Usage

### Basic

```
/research "What are the main tradeoffs between RAG and fine-tuning for enterprise LLM deployment?"
```

The orchestrator will:

1. Check for any interrupted runs and offer to resume
2. Initialize a run directory at `.research/run-001-TIMESTAMP/`
3. Ask you to confirm or adjust the research scope (**Gate 1**)
4. Spawn the collector agent to crawl web sources and parse any local documents
5. Ask you to review source quality and quarantined content (**Gate 2**)
6. Build a knowledge graph with Graphify
7. Spawn the synthesizer agent to produce citation-rich research
8. Ask you to review claims and coverage (**Gate 3**)
9. Detect gaps and run targeted re-collection if needed
10. Hand off to `research-format` and render a Quarto HTML report
11. Present the finished report for final approval (**Gate 4**)

### Configuration

Pass budget overrides to `init_run.py` (the orchestrator calls this internally, or you can call it directly):

```bash
python3 ~/.claude/skills/research-orchestrator/scripts/init_run.py \
  "your research request" \
  --max-pages 50 \
  --max-per-domain 10 \
  --max-depth 2
```

Default crawl budget: **75 pages**, 15 per domain, depth 3.

---

## Run Artifacts

Each run produces a self-contained directory:

```
.research/run-001-20260411T090950/
├── manifest.json          # Run config, budget, phase status
├── scope/
│   ├── scope.md           # Human-readable research scope
│   ├── plan.json          # Structured subtopics + source types
│   └── question_tree.json # 7-layer investigation tree
├── collect/
│   ├── inventory.json     # Source metadata (tiers, freshness)
│   ├── evidence/          # Collected evidence files with provenance headers
│   ├── quarantine/        # Flagged/excluded sources
│   └── collection_log.md  # Per-source crawl status
├── graph/                 # Graphify outputs (graph.json, GRAPH_REPORT.md)
├── synthesis/
│   ├── raw_research.md    # Draft research document
│   ├── claim_index.json   # Every claim → source mapping
│   ├── citation_audit.md  # Citation coverage report
│   └── gap_analysis.md    # Uncovered investigation branches
├── output/
│   └── report.html        # Final Quarto-rendered report
└── logs/
    └── run_log.md         # Timestamped action log for entire run
```

---

## Safety

The collector and synthesizer agents are explicitly instructed to treat all scraped web content and evidence files as **untrusted data** — never as instructions or system prompts. Quarantine classification runs on all collected content before it reaches synthesis.

---

## Contributing

Issues and PRs welcome. The pipeline is structured so each phase can be improved independently — better question tree generation, smarter gap detection, additional source types — without touching the orchestrator contract.

---

## License

MIT — see [LICENSE](LICENSE).
