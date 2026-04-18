"""Gate 1 validator with auto-regenerate loop (D-16/D-17/D-18/D-19).

Runtime copy used by the research-orchestrator skill. Canonical implementation
lives at ``research_orchestrator/gate1.py`` in the project repo; this file
mirrors it so the skill can import without the repo package being on
sys.path.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable, Optional

VALIDATOR = (
    Path.home()
    / ".claude"
    / "skills"
    / "research-orchestrator"
    / "scripts"
    / "validate_artifact.py"
)
SCHEMA = (
    Path.home()
    / ".claude"
    / "skills"
    / "research-orchestrator"
    / "references"
    / "question_tree.schema.json"
)

MIN_LAYERS = 3
DEFAULT_MAX_ATTEMPTS = 2


def append_log(run_dir, phase: str, action: str, status: str, detail: str) -> None:
    log_dir = Path(run_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "run_log.md", "a", encoding="utf-8") as f:
        f.write(f"- [{phase}] {action}: {status} -- {detail}\n")


def _is_valid(tree_path) -> tuple[bool, str]:
    tree_path = Path(tree_path)
    if not tree_path.exists():
        return False, f"tree not found: {tree_path}"
    result = subprocess.run(
        ["python3", str(VALIDATOR), str(tree_path), str(SCHEMA)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, (result.stdout or result.stderr or "schema validation failed").strip()
    try:
        tree = json.loads(tree_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"failed to read tree: {exc}"
    if len(tree.get("layers_populated", [])) < MIN_LAYERS:
        return False, f"layers_populated < {MIN_LAYERS}"
    return True, "ok"


def run_gate1_validator(
    tree_path,
    run_dir,
    regenerate: Optional[Callable[[], None]] = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> dict:
    ok, detail = _is_valid(tree_path)
    if ok:
        append_log(run_dir=run_dir, phase="planning",
                   action="question_tree_validated", status="ok", detail=detail)
        return {"status": "ok", "attempts": 0}

    append_log(run_dir=run_dir, phase="planning",
               action="question_tree_validated", status="error", detail=detail)

    attempts = 0
    if regenerate is not None:
        while attempts < max_attempts:
            attempts += 1
            append_log(run_dir=run_dir, phase="planning",
                       action="question_tree_regenerated", status="ok",
                       detail=f"attempt {attempts}")
            regenerate()
            ok, detail = _is_valid(tree_path)
            if ok:
                append_log(run_dir=run_dir, phase="planning",
                           action="question_tree_validated", status="ok",
                           detail=f"passed on attempt {attempts}")
                return {"status": "ok", "attempts": attempts}
            append_log(run_dir=run_dir, phase="planning",
                       action="question_tree_validated", status="error",
                       detail=f"attempt {attempts}: {detail}")

    append_log(
        run_dir=run_dir, phase="planning",
        action="question_tree_validated", status="warn",
        detail=(f"Validation failed after {attempts} auto-regenerations; "
                "proceeding with manual confirmation"),
    )
    return {"status": "warn", "attempts": attempts if regenerate else 0}


def check_tool_resolution(manifest: dict, run_dir) -> dict:
    """Check that crawl4ai resolved correctly in manifest.runtime_profile.

    Returns {"status": "ok"} if resolved or degraded mode.
    Returns {"status": "warn", "detail": "..."} if crawl4ai_python is missing.
    """
    runtime = manifest.get("runtime_profile", {})
    tools = runtime.get("tools", {})
    crawl4ai_python = tools.get("crawl4ai_python")
    collection_mode = manifest.get("collection_mode", "full")

    if not crawl4ai_python and collection_mode != "degraded":
        detail = "crawl4ai_python not resolved — web collection will fail. Run with --i-understand-degraded to proceed in docs-only mode."
        append_log(run_dir=run_dir, phase="planning",
                   action="tool_resolution_check", status="warn", detail=detail)
        return {"status": "warn", "detail": detail}

    append_log(run_dir=run_dir, phase="planning",
               action="tool_resolution_check", status="ok",
               detail=f"crawl4ai_python={crawl4ai_python}, collection_mode={collection_mode}")
    return {"status": "ok"}


def check_collection_warnings(manifest: dict, run_dir) -> list:
    """Surface post-collection quality warnings from manifest if present.

    Looks for BACKOFF_LOCK, DOMAIN_CONCENTRATION, DEVICE_FALLBACK flags
    in manifest.collection_warnings list.

    Returns list of warning dicts.
    """
    warnings = manifest.get("collection_warnings", [])
    for w in warnings:
        append_log(run_dir=run_dir, phase="collection",
                   action=w.get("type", "warning"), status="warn",
                   detail=w.get("detail", str(w)))
    return warnings


__all__ = ["run_gate1_validator", "append_log", "MIN_LAYERS", "DEFAULT_MAX_ATTEMPTS",
           "check_tool_resolution", "check_collection_warnings"]
