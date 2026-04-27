#!/usr/bin/env python3
"""Research pipeline run initialization.

Creates research/run-NNN-TIMESTAMP/ with manifest.json.
Detects and offers resume of interrupted runs.

Both importable (for Phase 1 orchestrator) and CLI-invocable.
"""
import argparse
import json
import os
import re
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
    "planning", "collection", "claim_extraction",
    "graph_relationships", "section_brief_synthesis",
    "formatting", "publishing",
]

COLLECTION_MODES = ("web_and_docs", "docs_only", "web_only", "metadata_only")
LEGACY_COLLECTION_MODE_ALIASES = {"none": "metadata_only"}
VALIDATION_MODES = ("normal", "strict")

REQUIRED_ARTIFACTS_BY_PHASE = {
    "collection": ["scope/plan.json", "scope/question_tree.json"],
    "claim_extraction": ["collect/inventory.json", "collect/evidence"],
    "graph_relationships": ["synthesis/claim_bank.json"],
    "section_brief_synthesis": [
        "synthesis/claim_bank.json",
        "synthesis/entity_index.json",
        "synthesis/claim_graph_map.json",
    ],
    "formatting": ["synthesis/section_briefs", "synthesis/claim_slices"],
    "publishing": ["output/report.md"],
}

STRICT_ARTIFACTS_BY_PHASE = {
    "publishing": ["output/formatter_audit.json"],
}

DISPATCH_TABLE = {
    "collection": "run collector",
    "claim_extraction": "run synthesizer claim extraction",
    "graph_relationships": "run graph enrichment",
    "section_brief_synthesis": "run section brief synthesis",
    "formatting": "run formatter",
    "publishing": "run publisher",
}

# Valid state machine transitions for phase_status
_VALID_TRANSITIONS = {
    ("pending", "running"),
    ("running", "running"),
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


def resolve_collection_mode(source_channels: dict, requested_mode: str = "auto") -> str:
    """Resolve a concrete collection mode from source channel intent."""
    requested_mode = LEGACY_COLLECTION_MODE_ALIASES.get(requested_mode, requested_mode)
    if requested_mode != "auto":
        if requested_mode not in COLLECTION_MODES:
            raise ValueError(f"Unknown collection mode: {requested_mode}")
        return requested_mode

    wants_web = bool(source_channels.get("web", True))
    wants_docs = bool(source_channels.get("documents", True))
    if wants_web and wants_docs:
        return "web_and_docs"
    if wants_docs:
        return "docs_only"
    if wants_web:
        return "web_only"
    return "metadata_only"


def missing_dependencies(collection_mode: str, tools: Optional[dict]) -> list[tuple[str, str]]:
    """Return missing dependency names and user-run remediation commands."""
    collection_mode = LEGACY_COLLECTION_MODE_ALIASES.get(collection_mode, collection_mode)
    tools = tools or {}
    missing = []
    needs_web = collection_mode in ("web_and_docs", "web_only")
    needs_docs = collection_mode in ("web_and_docs", "docs_only")

    if needs_web and not tools.get("crawl4ai_python"):
        missing.append(("crawl4ai", "pipx install crawl4ai"))
    if needs_web and not tools.get("playwright_ok", False):
        missing.append(("playwright chromium runtime", "playwright install chromium"))
    if needs_docs and not tools.get("docling_python"):
        missing.append(("docling", "pipx install docling"))
    return missing


def artifact_status(run_dir: Path, artifact: str) -> str:
    """Return a compact validation status for a run artifact."""
    path = run_dir / artifact
    if not path.exists():
        return "missing"
    if path.is_dir():
        try:
            return "valid" if any(path.iterdir()) else "missing"
        except OSError:
            return "invalid"
    if path.suffix == ".json":
        try:
            json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return "invalid"
    return "valid"


def required_artifacts_for_phase(phase: Optional[str], validation_mode: str = "normal") -> list[str]:
    """Return required artifacts for entering a phase."""
    if not phase:
        return []
    artifacts = list(REQUIRED_ARTIFACTS_BY_PHASE.get(phase, []))
    if validation_mode == "strict":
        artifacts.extend(STRICT_ARTIFACTS_BY_PHASE.get(phase, []))
    return artifacts


def create_manifest(
    run_id: str,
    user_request: str,
    budget: dict,
    runtime_profile: Optional[dict] = None,
    *,
    source_channels: Optional[dict] = None,
    collection_mode: str = "web_and_docs",
    validation_mode: str = "normal",
    tools: Optional[dict] = None,
) -> dict:
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
        "pipeline_contract_version": "claim_pipeline_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_request": user_request,
        "task_type": None,
        "run_mode": "normal",
        "collection_mode": collection_mode,
        "validation_mode": validation_mode,
        "source_channels": source_channels or {"web": True, "documents": True},
        "depth": "standard",
        "audience": "external",
        "tone": "professional",
        "render_targets": ["md", "html"],
        "section_depth_overrides": {},
        "environment": {"tinytex_available": False, "tools": tools or {}},
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
      pending -> running, running -> running, running -> complete,
      running -> failed, failed -> running (resume).

    Special cases:
      complete -> running: returns manifest unchanged (RUN-05 skip detection).
      running -> running: returns manifest unchanged (resume re-entry).
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
    if current == "running" and status == "running":
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


def _last_non_pending_phase(statuses: dict) -> Optional[str]:
    """Return the latest phase that has started, respecting PHASES order."""
    last = None
    for phase in PHASES:
        info = statuses.get(phase, {})
        if isinstance(info, dict) and info.get("status") not in (None, "pending"):
            last = phase
    return last


def _next_phase_to_run(statuses: dict) -> Optional[str]:
    """Return the first non-complete phase, respecting PHASES order."""
    for phase in PHASES:
        info = statuses.get(phase, {})
        if info.get("status") != "complete":
            return phase
    return None


def _format_interrupted_runs(interrupted: list) -> None:
    """Print interrupted runs in a stable human-readable format."""
    if not interrupted:
        print("No interrupted runs found.")
        return

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


def resume_run(run_id: str, research_root: Optional[Path] = None) -> dict:
    """Load and validate an interrupted run for resume.

    Args:
        run_id: Run directory name, e.g. run-001-20260427T000000.
        research_root: Override for RESEARCH_ROOT (used by tests).

    Returns:
        Dict with run_id, run_dir, problem_phases, completed_phases,
        last_phase, next_phase, and user_request.

    Raises:
        FileNotFoundError: If the run or manifest does not exist.
        ValueError: If the manifest is malformed or the run is complete.
    """
    root = research_root or RESEARCH_ROOT
    run_dir = root / run_id
    manifest_path = run_dir / "manifest.json"
    if not run_dir.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found for run: {run_id}")

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Manifest is not valid JSON for run: {run_id}") from exc

    statuses = manifest.get("phase_status")
    if not isinstance(statuses, dict):
        raise ValueError(f"Manifest has no phase_status for run: {run_id}")

    problem_phases = {
        name: info for name, info in statuses.items()
        if isinstance(info, dict) and info.get("status") in ("running", "failed")
    }
    if not problem_phases:
        raise ValueError(f"Run is not interrupted: {run_id}")

    next_phase = _next_phase_to_run(statuses)
    validation_mode = manifest.get("validation_mode", "normal")
    required_artifacts = required_artifacts_for_phase(next_phase, validation_mode)
    status = {
        artifact: artifact_status(run_dir, artifact)
        for artifact in required_artifacts
    }

    return {
        "run_id": manifest.get("run_id", run_id),
        "run_dir": str(run_dir),
        "run_mode": "resume",
        "problem_phases": problem_phases,
        "completed_phases": [
            name for name, info in statuses.items()
            if isinstance(info, dict) and info.get("status") == "complete"
        ],
        "last_phase": _last_non_pending_phase(statuses),
        "next_phase": next_phase,
        "required_artifacts": required_artifacts,
        "artifact_status": status,
        "recommended_command": f"/research --resume {run_id}",
        "dispatch": DISPATCH_TABLE.get(next_phase),
        "user_request": manifest.get("user_request", ""),
    }


_BUDGET_SHORTHAND_RE = re.compile(r"^--([^,\s]+),([^,\s]+),([^,\s]+)$")


def expand_budget_shorthand(argv: list[str]) -> list[str]:
    """Expand leading --pages,domain,depth shorthand into long-form flags."""
    if not argv:
        return argv

    match = _BUDGET_SHORTHAND_RE.match(argv[0])
    if not match:
        return argv

    pages, per_domain, depth = match.groups()
    return [
        "--max-pages", pages,
        "--max-per-domain", per_domain,
        "--max-depth", depth,
        *argv[1:],
    ]


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
        "--list-interrupted", action="store_true",
        help="List interrupted runs and exit"
    )
    parser.add_argument(
        "--resume", metavar="RUN_ID",
        help="Load an interrupted run and print resume metadata"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON for resume/inspect output"
    )
    parser.add_argument(
        "--performance-mode",
        choices=["auto", "conservative", "balanced", "aggressive"],
        default=None,
        help="Performance mode for concurrency tuning (default: auto)"
    )
    parser.add_argument(
        "--collection-mode",
        choices=["auto", *COLLECTION_MODES, "none"],
        default="auto",
        help="Collection mode; auto resolves from source channels (legacy alias: none=metadata_only)"
    )
    parser.add_argument(
        "--validation-mode",
        choices=VALIDATION_MODES,
        default="normal",
        help="Artifact validation mode (default: normal)"
    )
    parser.add_argument(
        "--source-web",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include web source channel when resolving collection-mode=auto"
    )
    parser.add_argument(
        "--source-documents",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include document source channel when resolving collection-mode=auto"
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
        help="Override Docling SDK worker parallelism (overrides runtime profile)"
    )
    parser.add_argument(
        "--fixture-dir", default=None,
        help="Fixture directory for replay mode (QUAL-01)"
    )
    args = parser.parse_args(expand_budget_shorthand(sys.argv[1:]))

    # Validate budget values are positive
    for name, val in [("--max-pages", args.max_pages),
                      ("--max-per-domain", args.max_per_domain),
                      ("--max-depth", args.max_depth)]:
        if val <= 0:
            print(f"Error: {name} must be a positive integer, got {val}", file=sys.stderr)
            sys.exit(1)

    if args.list_interrupted:
        interrupted = find_interrupted_runs()
        if args.json:
            print(json.dumps({
                "run_mode": "inspect",
                "interrupted_runs": interrupted,
            }, indent=2))
        else:
            _format_interrupted_runs(interrupted)
        sys.exit(0)

    if args.resume:
        try:
            run = resume_run(args.resume)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(run, indent=2))
        else:
            problems = ", ".join(
                f"{name} ({info['status']})"
                for name, info in run["problem_phases"].items()
            )
            completed = ", ".join(run["completed_phases"]) or "none"
            print(f"Resume run: {run['run_id']}")
            print(f"  Directory: {run['run_dir']}")
            print(f"  Request: {run['user_request'][:80]}")
            print(f"  Problem phases: {problems}")
            print(f"  Completed phases: {completed}")
            print(f"  Last phase: {run['last_phase'] or 'none'}")
            print(f"  Next phase: {run['next_phase'] or 'none'}")
            print(f"  Required artifacts: {', '.join(run['required_artifacts']) or 'none'}")
        sys.exit(0)

    interrupted = find_interrupted_runs()
    if interrupted and not args.user_request:
        _format_interrupted_runs(interrupted)
        print("Use --resume RUN_ID to continue, or provide a new request.")
        sys.exit(0)

    if not args.user_request:
        _format_interrupted_runs(interrupted)
        print("Start a new research run with /research <topic>")
        sys.exit(0)

    # Resolve performance mode. "auto" uses the runtime detector default profile.
    perf_mode = args.performance_mode or os.environ.get("RESEARCH_PERF_MODE", "auto")
    if perf_mode == "auto":
        perf_mode_for_detector = "balanced"
    else:
        perf_mode_for_detector = perf_mode
    if perf_mode_for_detector not in ("conservative", "balanced", "aggressive"):
        perf_mode = "auto"
        perf_mode_for_detector = "balanced"

    source_channels = {
        "web": bool(args.source_web),
        "documents": bool(args.source_documents),
    }
    collection_mode = resolve_collection_mode(source_channels, args.collection_mode)
    if collection_mode == "metadata_only":
        source_channels = {"web": False, "documents": False}

    if args.validation_mode not in VALIDATION_MODES:
        print(f"Error: invalid validation mode: {args.validation_mode}", file=sys.stderr)
        sys.exit(1)

    if perf_mode not in ("auto", "conservative", "balanced", "aggressive"):
        perf_mode = "balanced"

    # Detect runtime (hardware + tools)
    runtime_profile = detect_runtime_profile(perf_mode_for_detector)
    tools = runtime_profile.get("tools") or resolve_tools()

    dependency_errors = missing_dependencies(collection_mode, tools)
    if dependency_errors:
        print("\n" + "="*60, file=sys.stderr)
        print("  Missing dependencies for collection mode", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"  collection_mode: {collection_mode}", file=sys.stderr)
        for name, command in dependency_errors:
            print(f"  - {name}: not found", file=sys.stderr)
            print(f"    install: {command}", file=sys.stderr)
        print("\nFix the environment or choose a collection mode whose requirements are met.", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
        sys.exit(1)

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
    recommended["crawl_user_agent_mode"] = "random" if perf_mode_for_detector == "aggressive" else "http"
    recommended["honor_retry_after"] = True
    recommended["referer_policy"] = "same_site_only"
    recommended["backoff_min_dwell_seconds"] = 30

    # Embed into runtime_profile.resolved
    runtime_profile["resolved"] = recommended
    runtime_profile["performance_mode_used"] = perf_mode

    # Create new run
    counter, run_name = next_run_id()
    budget = {
        "max_pages": args.max_pages,
        "max_per_domain": args.max_per_domain,
        "max_depth": args.max_depth,
        "max_concurrent": recommended.get("max_concurrent", 5),
        "per_domain_cap": recommended.get("per_domain_cap", 2),
    }
    manifest = create_manifest(
        run_name,
        args.user_request,
        budget,
        runtime_profile=runtime_profile,
        source_channels=source_channels,
        collection_mode=collection_mode,
        validation_mode=args.validation_mode,
        tools=tools,
    )

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
    print(f"  Validation mode: {args.validation_mode}")
    if runtime_profile.get("tier"):
        print(f"  Hardware tier: {runtime_profile['tier']} ({runtime_profile.get('cpu_cores', '?')} cores, {runtime_profile.get('memory_gb', '?')} GB)")


if __name__ == "__main__":
    main()
