#!/usr/bin/env python3
"""Research pipeline run initialization.

Creates research/run-NNN-TIMESTAMP/ with manifest.json.
Detects and offers resume of interrupted runs.

Both importable (for Phase 1 orchestrator) and CLI-invocable.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

RESEARCH_ROOT = Path("research")
COUNTER_FILE = RESEARCH_ROOT / ".run-counter"

DETECT_RUNTIME = (
    Path.home() / ".claude" / "skills" / "research-collect" / "scripts" / "detect_runtime.py"
)
RESOLVE_ENV = (
    Path.home() / ".claude" / "skills" / "research-collect" / "scripts" / "resolve_env.py"
)


def detect_runtime_profile(performance_mode: str = "balanced") -> dict:
    """Run detect_runtime.py and return its JSON output as a dict.

    Returns empty dict on failure (non-fatal; caller uses hardcoded defaults).
    """
    if not DETECT_RUNTIME.exists():
        return {}
    try:
        result = subprocess.run(
            ["python3", str(DETECT_RUNTIME), "--performance-mode", performance_mode],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return {}


def resolve_tools() -> dict:
    """Run resolve_env.py and return its JSON output as a dict.

    Returns empty dict on failure.
    """
    if not RESOLVE_ENV.exists():
        return {}
    try:
        result = subprocess.run(
            ["python3", str(RESOLVE_ENV)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return {}

PHASES = [
    "planning", "collection", "graph",
    "synthesis", "gap_detection", "formatting",
]

# Valid state machine transitions for phase_status
_VALID_TRANSITIONS = {
    ("pending", "running"),
    ("running", "complete"),
    ("running", "failed"),
    ("failed", "running"),
}


def _scan_max_counter(research_root: Optional[Path] = None) -> int:
    """Fallback: scan existing run dirs for highest counter."""
    root = research_root or RESEARCH_ROOT
    max_c = 0
    if not root.exists():
        return max_c
    for d in root.iterdir():
        if d.is_dir() and d.name.startswith("run-"):
            try:
                c = int(d.name.split("-")[1])
                max_c = max(max_c, c)
            except (IndexError, ValueError):
                continue
    return max_c


def next_run_id() -> tuple:
    """Allocate next run ID. Returns (counter, run_dir_name).

    Reads and increments .run-counter. Falls back to directory scan
    if counter file is corrupted.
    """
    RESEARCH_ROOT.mkdir(exist_ok=True)

    if COUNTER_FILE.exists():
        try:
            counter = int(COUNTER_FILE.read_text().strip()) + 1
        except (ValueError, OSError):
            # Corrupted counter -- fall back to directory scan
            counter = _scan_max_counter() + 1
    else:
        counter = 1

    # Write new counter
    COUNTER_FILE.write_text(str(counter))

    # Format: run-001-20260411T143022
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_name = f"run-{counter:03d}-{ts}"
    return counter, run_name


def create_manifest(run_id: str, user_request: str, budget: dict, runtime_profile: Optional[dict] = None) -> dict:
    """Create initial manifest with all phases pending.

    Args:
        run_id: The run directory name (e.g., run-001-20260411T143022).
        user_request: The user's research request text.
        budget: Dict with max_pages, max_per_domain, max_depth.
        runtime_profile: Optional runtime/hardware profile dict.

    Returns:
        Manifest dict ready to be written as JSON.
    """
    return {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_request": user_request,
        "task_type": None,
        "collection_mode": "full",
        "environment": {"tinytex_available": False},
        "runtime_profile": runtime_profile or {},
        "budget_config": {
            "max_pages": budget.get("max_pages", 75),
            "max_per_domain": budget.get("max_per_domain", 15),
            "max_depth": budget.get("max_depth", 3),
            "max_concurrent": budget.get("max_concurrent", 5),
            "per_domain_cap": budget.get("per_domain_cap", 2),
        },
        "phase_status": {
            phase: {"status": "pending", "started_at": None, "completed_at": None}
            for phase in PHASES
        },
    }


def update_phase_status(manifest_path: Path, phase: str, status: str) -> dict:
    """Update a phase's status in manifest.json. Returns updated manifest.

    Validates state machine transitions:
      pending -> running, running -> complete, running -> failed,
      failed -> running (resume).

    Special cases:
      complete -> running: returns manifest unchanged (RUN-05 skip detection).
      Any other invalid transition: raises ValueError.

    Args:
        manifest_path: Path to manifest.json file.
        phase: Phase name (e.g., 'planning', 'collection').
        status: Target status ('running', 'complete', 'failed').

    Returns:
        The (possibly updated) manifest dict.

    Raises:
        ValueError: On invalid state transition.
        KeyError: If phase name is not recognized.
    """
    manifest = json.loads(manifest_path.read_text())
    ts = datetime.now(timezone.utc).isoformat()

    if phase not in manifest["phase_status"]:
        raise KeyError(f"Unknown phase: {phase}")

    phase_info = manifest["phase_status"][phase]
    current = phase_info["status"]

    # Check for skip detection (RUN-05)
    if current == "complete" and status == "running":
        return manifest

    # Validate transition
    if (current, status) not in _VALID_TRANSITIONS:
        raise ValueError(
            f"Invalid transition: {current} -> {status} for phase '{phase}'"
        )

    phase_info["status"] = status
    if status == "running":
        phase_info["started_at"] = ts
    elif status in ("complete", "failed"):
        phase_info["completed_at"] = ts

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def find_interrupted_runs(research_root: Optional[Path] = None) -> list:
    """Scan research/ for runs with 'running' or 'failed' phases.

    Args:
        research_root: Override for RESEARCH_ROOT (used by tests).

    Returns:
        List of dicts with run_id, run_dir, problem_phases,
        completed_phases, user_request for each interrupted run.
    """
    root = research_root or RESEARCH_ROOT
    interrupted = []
    if not root.exists():
        return interrupted

    for run_dir in sorted(root.iterdir()):
        if not run_dir.is_dir() or not run_dir.name.startswith("run-"):
            continue
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        statuses = manifest.get("phase_status", {})
        problem_phases = {
            name: info for name, info in statuses.items()
            if info.get("status") in ("running", "failed")
        }
        if problem_phases:
            interrupted.append({
                "run_id": manifest.get("run_id", run_dir.name),
                "run_dir": str(run_dir),
                "problem_phases": problem_phases,
                "completed_phases": [
                    name for name, info in statuses.items()
                    if info.get("status") == "complete"
                ],
                "user_request": manifest.get("user_request", ""),
            })

    return interrupted


def main():
    """CLI entry point for run initialization."""
    parser = argparse.ArgumentParser(
        description="Initialize a research pipeline run directory"
    )
    parser.add_argument(
        "user_request", nargs="?",
        help="Research request text (omit to check for interrupted runs)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=75,
        help="Maximum pages to crawl (default: 75)"
    )
    parser.add_argument(
        "--max-per-domain", type=int, default=15,
        help="Maximum pages per domain (default: 15)"
    )
    parser.add_argument(
        "--max-depth", type=int, default=3,
        help="Maximum crawl depth (default: 3)"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Show interrupted runs and exit"
    )
    parser.add_argument(
        "--performance-mode",
        choices=["conservative", "balanced", "aggressive"],
        default=None,
        help="Performance mode for concurrency tuning (default: balanced)"
    )
    parser.add_argument(
        "--max-concurrent", type=int, default=None,
        help="Override max concurrent crawl sessions (overrides runtime profile)"
    )
    parser.add_argument(
        "--per-domain-cap", type=int, default=None,
        help="Override max concurrent sessions per domain (overrides runtime profile)"
    )
    parser.add_argument(
        "--docling-parallelism", type=int, default=None,
        help="Override docling xargs -P value (overrides runtime profile)"
    )
    parser.add_argument(
        "--i-understand-degraded", action="store_true",
        help="Confirm continuation in docs-only mode when crawl4ai is unresolved"
    )
    parser.add_argument(
        "--fixture-dir", default=None,
        help="Fixture directory for replay mode (QUAL-01)"
    )
    args = parser.parse_args()

    # Validate budget values are positive
    for name, val in [("--max-pages", args.max_pages),
                      ("--max-per-domain", args.max_per_domain),
                      ("--max-depth", args.max_depth)]:
        if val <= 0:
            print(f"Error: {name} must be a positive integer, got {val}", file=sys.stderr)
            sys.exit(1)

    # Check for interrupted runs
    interrupted = find_interrupted_runs()
    if interrupted:
        print(f"\n{'='*60}")
        print(f"  {len(interrupted)} interrupted run(s) found:")
        print(f"{'='*60}\n")
        for run in interrupted:
            problems = ", ".join(
                f"{name} ({info['status']})"
                for name, info in run["problem_phases"].items()
            )
            completed = ", ".join(run["completed_phases"]) or "none"
            print(f"  Run: {run['run_id']}")
            print(f"  Request: {run['user_request'][:80]}")
            print(f"  Problem phases: {problems}")
            print(f"  Completed phases: {completed}")
            print()

        if args.resume or not args.user_request:
            print("Use --resume with a specific run to continue, or provide a new request.")
            sys.exit(0)

    if args.resume:
        print("No interrupted runs found.")
        sys.exit(0)

    if not args.user_request:
        parser.error("user_request is required when starting a new run")

    # Resolve performance mode
    perf_mode = args.performance_mode or os.environ.get("RESEARCH_PERF_MODE", "balanced")
    if perf_mode not in ("conservative", "balanced", "aggressive"):
        perf_mode = "balanced"

    # Detect runtime (hardware + tools)
    runtime_profile = detect_runtime_profile(perf_mode)
    tools = runtime_profile.get("tools") or resolve_tools()

    # Gate-1: fail if crawl4ai unresolved
    crawl4ai_python = tools.get("crawl4ai_python") if tools else None
    if not crawl4ai_python:
        print("\n" + "="*60, file=sys.stderr)
        print("  Gate-1: Missing dependencies detected", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print("  - crawl4ai:  not found  (searched: CRAWL4AI_PYTHON, pipx, .venv, PATH, system python3)", file=sys.stderr)
        docling_python = (tools or {}).get("docling_python")
        status = f"found  {docling_python}" if docling_python else "not found"
        print(f"  - docling:   {status}", file=sys.stderr)
        playwright_ok = (tools or {}).get("playwright_ok", False)
        print(f"  - playwright: {'found' if playwright_ok else 'not found'}", file=sys.stderr)
        print("\nOptions:", file=sys.stderr)
        print("  1. Abort", file=sys.stderr)
        print("  2. Continue without web collection (docs-only)  [pass --i-understand-degraded]", file=sys.stderr)
        print("  3. Fix environment and retry", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
        if not args.i_understand_degraded:
            sys.exit(1)
        # Degraded mode: set collection_mode
        collection_mode = "degraded"
    else:
        collection_mode = "full"

    # Apply CLI overrides to resolved knobs
    recommended = (runtime_profile.get("recommended") or {}).copy()
    if args.max_concurrent is not None:
        recommended["max_concurrent"] = args.max_concurrent
    if args.per_domain_cap is not None:
        recommended["per_domain_cap"] = args.per_domain_cap
    if args.docling_parallelism is not None:
        recommended["docling_parallelism"] = args.docling_parallelism
    if args.fixture_dir is not None:
        recommended["fixture_dir"] = args.fixture_dir

    # New collection pipeline fields
    _default_cache = str(Path.home() / ".cache" / "research-collect" / "docling")
    recommended["docling_cache_dir"] = os.environ.get("RESEARCH_CACHE_DIR", _default_cache)
    recommended["docling_format_whitelist"] = [".pdf", ".docx", ".pptx", ".xlsx"]
    recommended["crawl_user_agent_mode"] = "random" if perf_mode == "aggressive" else "http"
    recommended["honor_retry_after"] = True
    recommended["referer_policy"] = "same_site_only"
    recommended["backoff_min_dwell_seconds"] = 30

    # Embed into runtime_profile.resolved
    runtime_profile["resolved"] = recommended
    runtime_profile["performance_mode_used"] = perf_mode
    if tools:
        runtime_profile["tools"] = tools

    # Create new run
    counter, run_name = next_run_id()
    budget = {
        "max_pages": args.max_pages,
        "max_per_domain": args.max_per_domain,
        "max_depth": args.max_depth,
        "max_concurrent": recommended.get("max_concurrent", 5),
        "per_domain_cap": recommended.get("per_domain_cap", 2),
    }
    manifest = create_manifest(run_name, args.user_request, budget, runtime_profile=runtime_profile)
    manifest["collection_mode"] = collection_mode

    run_dir = RESEARCH_ROOT / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"Created run: {run_name}")
    print(f"  Directory: {run_dir}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Budget: {budget}")
    print(f"  Performance mode: {perf_mode}")
    print(f"  Collection mode: {collection_mode}")
    if runtime_profile.get("tier"):
        print(f"  Hardware tier: {runtime_profile['tier']} ({runtime_profile.get('cpu_cores', '?')} cores, {runtime_profile.get('memory_gb', '?')} GB)")


if __name__ == "__main__":
    main()
