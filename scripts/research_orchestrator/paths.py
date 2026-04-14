"""Scope directory path helpers (D-05/D-06/D-07).

Every run directory now has a ``scope/`` subdirectory that holds ``scope.md``,
``plan.json``, and ``question_tree.json``. These helpers centralise the path
construction so every caller uses the same convention.
"""
from __future__ import annotations

from pathlib import Path


def scope_path(run_dir) -> Path:
    """Return ``<run_dir>/scope`` as a Path (does not create the directory)."""
    return Path(run_dir) / "scope"


def scope_md_path(run_dir) -> Path:
    """Return ``<run_dir>/scope/scope.md``."""
    return scope_path(run_dir) / "scope.md"


def plan_json_path(run_dir) -> Path:
    """Return ``<run_dir>/scope/plan.json``."""
    return scope_path(run_dir) / "plan.json"


def question_tree_path(run_dir) -> Path:
    """Return ``<run_dir>/scope/question_tree.json``."""
    return scope_path(run_dir) / "question_tree.json"


def ensure_scope_dir(run_dir) -> Path:
    """Create ``<run_dir>/scope/`` if absent and return the Path."""
    p = scope_path(run_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p
