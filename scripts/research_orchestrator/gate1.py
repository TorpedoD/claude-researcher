"""Gate 1 validator with auto-regenerate loop (D-16/D-17/D-18/D-19).

Validates ``question_tree.json`` against the JSON Schema under
``~/.claude/skills/research-orchestrator/references/question_tree.schema.json``
and enforces the D-16 floor of ``len(layers_populated) >= 3``.

On invalid detection, calls ``regenerate()`` (if supplied) up to
``max_attempts`` times (default 2 per D-19). After the cap is exhausted, the
validator downgrades to ``warn`` and emits a ``question_tree_validated``
warn log entry so the user can confirm manually.

``append_log`` is deliberately defined at module level so tests can
``unittest.mock.patch("research_orchestrator.gate1.append_log")``.
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

MIN_LAYERS = 3  # D-16 floor
DEFAULT_MAX_ATTEMPTS = 2  # D-19


def append_log(run_dir, phase: str, action: str, status: str, detail: str) -> None:
    """Append a structured log entry to ``<run_dir>/logs/run_log.md``.

    Kept at module level so ``unittest.mock.patch`` can swap it in tests.
    """
    log_dir = Path(run_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "run_log.md", "a", encoding="utf-8") as f:
        f.write(f"- [{phase}] {action}: {status} -- {detail}\n")


def _is_valid(tree_path) -> tuple[bool, str]:
    """Run the schema validator + D-16 layer-count check.

    Returns ``(ok, detail_message)``.
    """
    tree_path = Path(tree_path)
    if not tree_path.exists():
        return False, f"tree not found: {tree_path}"

    result = subprocess.run(
        ["python3", str(VALIDATOR), str(tree_path), str(SCHEMA)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # rc 1 = warn (schema errors); rc 2 = error (bad input)
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
    """Validate ``tree_path`` against the question_tree schema + D-16 floor.

    Parameters
    ----------
    tree_path : PathLike
        Path to ``question_tree.json`` to validate.
    run_dir : PathLike
        Run directory (used for log file path).
    regenerate : callable, optional
        Zero-arg callback that rewrites ``tree_path`` in place to produce a
        new tree. If ``None`` and validation fails, the validator skips the
        regenerate loop and immediately downgrades to ``warn``.
    max_attempts : int
        Maximum number of regenerate attempts (D-19, default 2).

    Returns
    -------
    dict
        ``{"status": "ok" | "warn", "attempts": int}``.
    """
    ok, detail = _is_valid(tree_path)
    if ok:
        append_log(
            run_dir=run_dir,
            phase="planning",
            action="question_tree_validated",
            status="ok",
            detail=detail,
        )
        return {"status": "ok", "attempts": 0}

    # Invalid on first check; enter regenerate loop.
    append_log(
        run_dir=run_dir,
        phase="planning",
        action="question_tree_validated",
        status="error",
        detail=detail,
    )

    attempts = 0
    if regenerate is not None:
        while attempts < max_attempts:
            attempts += 1
            append_log(
                run_dir=run_dir,
                phase="planning",
                action="question_tree_regenerated",
                status="ok",
                detail=f"attempt {attempts}",
            )
            regenerate()
            ok, detail = _is_valid(tree_path)
            if ok:
                append_log(
                    run_dir=run_dir,
                    phase="planning",
                    action="question_tree_validated",
                    status="ok",
                    detail=f"passed on attempt {attempts}",
                )
                return {"status": "ok", "attempts": attempts}
            append_log(
                run_dir=run_dir,
                phase="planning",
                action="question_tree_validated",
                status="error",
                detail=f"attempt {attempts}: {detail}",
            )

    # Cap exhausted (or no regenerate callback): downgrade to warn.
    append_log(
        run_dir=run_dir,
        phase="planning",
        action="question_tree_validated",
        status="warn",
        detail=(
            f"Validation failed after {attempts} auto-regenerations; "
            "proceeding with manual confirmation"
        ),
    )
    return {"status": "warn", "attempts": attempts if regenerate else 0}
