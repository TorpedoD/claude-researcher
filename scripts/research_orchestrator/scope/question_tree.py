"""7-layer question tree builder (INV-01, INV-02, D-08..D-16).

Produces ``question_tree.json`` artifacts consumed by the synthesizer for
macro section ordering and by Gate 1 for schema validation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from research_orchestrator.paths import ensure_scope_dir, question_tree_path

# The 7 investigation layers in canonical order (D-08). Order matters: the
# synthesizer uses this sequence for macro section ordering (INV-03 / D-12).
LAYERS: tuple[str, ...] = (
    "identity",
    "purpose",
    "mechanics",
    "relations",
    "comparison",
    "evidence",
    "open questions",
)

# Valid expected_source_types values (D-09 + schema enum).
SOURCE_TYPES: tuple[str, ...] = (
    "docs",
    "paper",
    "blog",
    "code",
    "forum",
    "other",
)


def _l1_node(question: str, layer: str, branch_priority: int,
             expected_source_types: Iterable[str] = ("docs", "blog")) -> dict:
    return {
        "question": question,
        "layer": layer,
        "depth": 1,
        "expected_source_types": list(expected_source_types),
        "branch_priority": branch_priority,
        "children": [],
    }


def build_question_tree(
    topic: str,
    subtopics: list[str],
    bridge_entities: list[str] | None = None,
    generation_method: str = "subtopic_fallback",
    top_n: int = 5,
) -> dict:
    """Build a layered question tree rooted at ``topic`` (D-08/D-09/D-16).

    The root is an L0 identity node. Each subtopic becomes an L1 node whose
    layer is chosen by a deterministic round-robin over ``LAYERS`` so that
    ``layers_populated`` always has at least 3 distinct layers when 3+
    subtopics are provided (D-16 floor).

    ``bridge_entities`` (optional) adds ``relations``-layer bridge questions
    for every pair in the list (REL-09).

    Returns ``{"root": {...}, "layers_populated": [...],
    "generation": {"method", "top_n", "regenerate_attempts": 0}}``.
    """
    children: list[dict] = []

    for i, sub in enumerate(subtopics):
        layer = LAYERS[i % len(LAYERS)]
        children.append(_l1_node(
            question=f"What is {sub}?",
            layer=layer,
            branch_priority=i + 1,
        ))

    if bridge_entities:
        bridges = bridge_questions(bridge_entities)
        # Keep bridge questions after subtopic-driven L1 nodes so they cluster
        # at the end of the relations layer.
        children.extend(bridges)

    root = {
        "question": f"Investigate: {topic}",
        "layer": "identity",
        "depth": 0,
        "expected_source_types": ["docs"],
        "branch_priority": 1,
        "children": children,
    }

    layers_populated = sorted({c["layer"] for c in children})

    return {
        "root": root,
        "layers_populated": layers_populated,
        "generation": {
            "method": generation_method,
            "top_n": int(top_n),
            "regenerate_attempts": 0,
        },
    }


# ---------------------------------------------------------------------------
# Bridge helpers are re-exported here for convenience, but implementation
# lives in ``research_orchestrator.scope.bridge`` per the test contract.
# ---------------------------------------------------------------------------
from research_orchestrator.scope.bridge import (  # noqa: E402,F401  (re-export)
    bridge_questions,
    select_bridge_entities,
)


def write_question_tree(run_dir, tree: dict) -> Path:
    """Write ``tree`` to ``<run_dir>/scope/question_tree.json`` (pretty JSON)."""
    ensure_scope_dir(run_dir)
    path = question_tree_path(run_dir)
    path.write_text(json.dumps(tree, indent=2, sort_keys=False))
    return path
