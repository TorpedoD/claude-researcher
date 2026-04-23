---
name: research-resume
description: Resume an interrupted research pipeline run from its last completed phase
trigger: /research-resume
allowed-tools: [Read, Bash, Task]
---

# Research Resume

Resume an interrupted research pipeline run from its last completed phase without having to remember the run ID or the original request. Scans `research/` for runs whose `manifest.json` shows at least one `phase_status` value other than `complete`, lists them, and hands off to the research-orchestrator agent via `init_run.py --resume`.

---

## Quick Start

Scan `research/` for interrupted runs, let the user pick one (or auto-select if only one exists), and resume from the last completed phase via `init_run.py --resume <run_id>`.

---

## Behavior

Follow these steps literally — every branch below is required.

### Step 1 — Detect interrupted runs

Invoke the existing helper that ships with `research-orchestrator`:

```bash
python3 ~/.claude/skills/research-orchestrator/scripts/init_run.py --list-interrupted
```

Or, equivalently, import and call `find_interrupted_runs()` from `init_run.py`. An **interrupted run** is any `research/run-NNN-TIMESTAMP/` whose `manifest.json` contains at least one `phase_status` value of `running` or `failed` (i.e., not every phase is `complete`). If the `research/` directory does not exist, treat the result as zero interrupted runs.

### Step 2 — Zero interrupted runs

If the detection step returns nothing, print exactly:

```
No interrupted runs found.
Start a new research run with /research
```

Then exit the skill. Do not prompt, do not spawn any agent.

### Step 3 — Exactly one interrupted run

If exactly one run is found, skip the selection menu and jump straight to Step 5 (Confirmation) with that run pre-selected.

### Step 4 — Multiple interrupted runs

If two or more runs are found, sort them newest-to-oldest by run start timestamp and display each one using this exact per-row format:

```
[N] run-NNN-TIMESTAMP | "TRUNCATED_REQUEST" | Last: PHASE_NAME | Started: TIMESTAMP
```

Where:
- `N` is a 1-based selection index
- `TRUNCATED_REQUEST` is `user_request` from `manifest.json` truncated to ~80 characters
- `PHASE_NAME` is the last non-pending phase name from `phase_status` (the most recent phase marked `running`, `failed`, or `complete`)
- `TIMESTAMP` is the run start time from the manifest

After the list, prompt the user to select a run by number.

### Step 5 — Confirmation

Display the selected run's summary (run id, original request, last phase, start time) and ask:

```
Resume this run? (y/n)
```

### Step 6 — Resume handoff

On confirmation, invoke the existing resume path:

```bash
python3 ~/.claude/skills/research-orchestrator/scripts/init_run.py --resume <run_id>
```

Then spawn the `research-orchestrator` agent via `Task()` so it continues the pipeline from the last completed phase.

---

## Scripts

This skill ships **no new scripts**. It wraps existing infrastructure:

- `~/.claude/skills/research-orchestrator/scripts/init_run.py`
  - `find_interrupted_runs()` — scans `research/` and returns interrupted runs
  - `--resume <run_id>` — loads an existing run and prepares it for continuation

If either function is missing, upgrade research-orchestrator before using this skill.

---

## Edge Cases

- **No `research/` directory** — treat as zero interrupted runs (Step 2).
- **Manifest unreadable / malformed** — skip that run silently and continue scanning.
- **All phases already `complete`** — the run is not interrupted; exclude it from the list.
- **User declines confirmation** — exit cleanly without modifying any files.
