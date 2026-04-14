"""Scope directory path helpers (D-05/D-06/D-07).

Runtime copy used by the research-orchestrator skill. The canonical
implementation lives at ``research_orchestrator/paths.py`` in the project
repo; this file mirrors it so the skill can import without the repo package
being on sys.path.
"""
from __future__ import annotations

from pathlib import Path


def scope_path(run_dir) -> Path:
    return Path(run_dir) / "scope"


def scope_md_path(run_dir) -> Path:
    return scope_path(run_dir) / "scope.md"


def plan_json_path(run_dir) -> Path:
    return scope_path(run_dir) / "plan.json"


def question_tree_path(run_dir) -> Path:
    return scope_path(run_dir) / "question_tree.json"


def ensure_scope_dir(run_dir) -> Path:
    p = scope_path(run_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


__all__ = [
    "scope_path",
    "scope_md_path",
    "plan_json_path",
    "question_tree_path",
    "ensure_scope_dir",
]
