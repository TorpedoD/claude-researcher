"""7-layer question tree builder + bridge question helpers (Phase 10).

Runtime copy used by the research-orchestrator skill. The canonical
implementation lives in ``research_orchestrator/scope/question_tree.py``
and ``research_orchestrator/scope/bridge.py`` in the project repo; this
file mirrors both so the skill can import without the repo package being
on sys.path.

Exports (per plan 10-02 contract):
  LAYERS, SOURCE_TYPES, MAX_TOP_N,
  build_question_tree, select_bridge_entities, bridge_questions,
  write_question_tree
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Iterable

from scope_paths import ensure_scope_dir, question_tree_path

LAYERS: tuple[str, ...] = (
    "identity",
    "purpose",
    "mechanics",
    "relations",
    "comparison",
    "evidence",
    "open questions",
)

SOURCE_TYPES: tuple[str, ...] = (
    "docs",
    "paper",
    "blog",
    "code",
    "forum",
    "other",
)

MAX_TOP_N = 10


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
    children: list[dict] = []
    for i, sub in enumerate(subtopics):
        layer = LAYERS[i % len(LAYERS)]
        children.append(_l1_node(
            question=f"What is {sub}?",
            layer=layer,
            branch_priority=i + 1,
        ))
    if bridge_entities:
        children.extend(bridge_questions(bridge_entities))

    root = {
        "question": f"Investigate: {topic}",
        "layer": "identity",
        "depth": 0,
        "expected_source_types": ["docs"],
        "branch_priority": 1,
        "children": children,
    }

    return {
        "root": root,
        "layers_populated": sorted({c["layer"] for c in children}),
        "generation": {
            "method": generation_method,
            "top_n": int(top_n),
            "regenerate_attempts": 0,
        },
    }


def select_bridge_entities(run_dir, top_n: int = 5) -> tuple[list[str], str]:
    top_n = max(1, min(MAX_TOP_N, int(top_n)))
    run_dir = Path(run_dir)

    central_path = run_dir / "collect" / "graphify-out" / "central_nodes.json"
    if central_path.exists():
        nodes = json.loads(central_path.read_text())
        return [n["name"] for n in nodes][:top_n], "graph_centrality"

    plan_path = run_dir / "scope" / "plan.json"
    if plan_path.exists():
        plan = json.loads(plan_path.read_text())
        subs = sorted(
            plan.get("subtopics", []),
            key=lambda s: s.get("priority", 10**6),
        )
        return [s["name"] for s in subs][:top_n], "subtopic_fallback"

    raise FileNotFoundError(
        f"No bridge-entity source under {run_dir}: neither "
        f"collect/graphify-out/central_nodes.json nor scope/plan.json exist."
    )


def bridge_questions(entities: list[str]) -> list[dict]:
    nodes: list[dict] = []
    for x, y in itertools.combinations(entities, 2):
        nodes.append({
            "question": f"What is the relationship between {x} and {y}?",
            "layer": "relations",
            "depth": 1,
            "expected_source_types": ["docs", "paper", "blog"],
            "branch_priority": 2,
            "children": [],
        })
    return nodes


def write_question_tree(run_dir, tree: dict) -> Path:
    ensure_scope_dir(run_dir)
    path = question_tree_path(run_dir)
    path.write_text(json.dumps(tree, indent=2, sort_keys=False))
    return path


__all__ = [
    "LAYERS",
    "SOURCE_TYPES",
    "MAX_TOP_N",
    "build_question_tree",
    "select_bridge_entities",
    "bridge_questions",
    "write_question_tree",
]
