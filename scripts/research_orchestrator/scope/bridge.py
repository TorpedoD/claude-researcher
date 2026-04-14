"""Bridge question generation (REL-09 + D-10/D-11 + T-10-03/T-10-08).

Bridge questions connect the top entities pairwise with the canonical phrasing
"What is the relationship between X and Y?", grouped into the ``relations``
layer of the question tree.

Entity source priority:
  1. ``<run_dir>/collect/graphify-out/central_nodes.json`` (graph centrality)
  2. ``<run_dir>/scope/plan.json`` subtopics sorted by priority (fallback)

``top_n`` is hard-clamped to ``[1, MAX_TOP_N]`` to prevent combinatorial
explosion (C(N,2) grows fast).
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

MAX_TOP_N = 10


def select_bridge_entities(run_dir, top_n: int = 5) -> tuple[list[str], str]:
    """Return (entities, source) for bridge question generation.

    ``source`` is either ``"graph_centrality"`` (central_nodes.json present)
    or ``"subtopic_fallback"`` (plan.json used).
    """
    top_n = max(1, min(MAX_TOP_N, int(top_n)))
    run_dir = Path(run_dir)

    central_path = run_dir / "collect" / "graphify-out" / "central_nodes.json"
    if central_path.exists():
        nodes = json.loads(central_path.read_text())
        names = [n["name"] for n in nodes][:top_n]
        return names, "graph_centrality"

    plan_path = run_dir / "scope" / "plan.json"
    if plan_path.exists():
        plan = json.loads(plan_path.read_text())
        subs = sorted(
            plan.get("subtopics", []),
            key=lambda s: s.get("priority", 10**6),
        )
        names = [s["name"] for s in subs][:top_n]
        return names, "subtopic_fallback"

    raise FileNotFoundError(
        f"No bridge-entity source under {run_dir}: neither "
        f"collect/graphify-out/central_nodes.json nor scope/plan.json exist."
    )


def bridge_questions(entities: list[str]) -> list[dict]:
    """Return one ``relations``-layer node per pair of entities.

    Each node: ``{"question": "What is the relationship between X and Y?",
    "layer": "relations", "depth": 1, ...}``.
    """
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
