"""Layer-first section ordering for research-synthesize (INV-03).

Implements D-12 (7-layer macro order), D-13 (graph centrality intra-layer),
D-14 (fallback to centrality ordering when question_tree.json is absent,
with auditable warn-level log), and D-15 (silently skip empty layers).

Public API:
    compute_section_order(run_dir) -> list[dict]
        Returns ordered list of {"layer": str, "question": str, "centrality": float}.

Module-level `append_log` is used for the D-14 fallback log event. It is a
thin wrapper that delegates to the orchestrator's append_log helper when
available and otherwise writes to <run_dir>/logs/run_log.md.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

LAYERS = (
    "identity",
    "purpose",
    "mechanics",
    "relations",
    "comparison",
    "evidence",
    "open questions",
)

_FALLBACK_MSG = (
    "question_tree.json absent — falling back to graph centrality ordering"
)


def append_log(run_dir, phase, action, status, detail):
    """Append a structured log line to <run_dir>/logs/run_log.md.

    Tests patch this symbol (`research_synthesize.section_order.append_log`)
    to assert the D-14 fallback event fires. Keep it top-level.
    """
    try:  # Prefer the orchestrator's helper when importable.
        from log import append_log as _orch_append  # type: ignore
    except Exception:
        log_dir = Path(run_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "run_log.md", "a", encoding="utf-8") as f:
            f.write(f"- [{phase}] {action}: {status} — {detail}\n")
        return
    _orch_append(run_dir, phase, action, status, detail)


def _flatten_nodes(node: dict, out: list) -> list:
    out.append(node)
    for child in node.get("children", []) or []:
        _flatten_nodes(child, out)
    return out


def _load_centrality(run_dir: Path) -> dict[str, float]:
    """Load central_nodes.json as {name: centrality}. Missing/invalid => {}."""
    path = Path(run_dir) / "collect" / "graphify-out" / "central_nodes.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    out: dict[str, float] = {}
    if isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue
            name = row.get("name") or row.get("concept") or row.get("question")
            cent = row.get("centrality", row.get("score", 0.0))
            if name is not None:
                try:
                    out[str(name)] = float(cent)
                except (TypeError, ValueError):
                    out[str(name)] = 0.0
    elif isinstance(data, dict):
        for name, cent in data.items():
            try:
                out[str(name)] = float(cent)
            except (TypeError, ValueError):
                out[str(name)] = 0.0
    return out


def _fallback_ordering(run_dir: Path) -> list[dict]:
    """D-14 fallback: order by centrality alone; emit warn log."""
    append_log(
        run_dir,
        "synthesis",
        "section_order_fallback",
        "warn",
        _FALLBACK_MSG,
    )
    centrality = _load_centrality(run_dir)
    ordered = sorted(centrality.items(), key=lambda kv: -kv[1])
    return [
        {"layer": None, "question": name, "centrality": cent}
        for name, cent in ordered
    ]


def compute_section_order(run_dir) -> list[dict]:
    """Return concepts ordered layer-first then by centrality (D-12/D-13/D-14/D-15).

    - Walks scope/question_tree.json, bucketing every node (root + children)
      under its declared `layer`.
    - Within each layer, orders by centrality from
      collect/graphify-out/central_nodes.json (descending). Unknown concepts
      receive centrality 0.0 and preserve insertion order.
    - Layers with no questions produce no entries (D-15).
    - Missing question_tree.json => fallback + warn log (D-14).
    """
    run_dir = Path(run_dir)
    tree_path = run_dir / "scope" / "question_tree.json"
    if not tree_path.exists():
        return _fallback_ordering(run_dir)

    try:
        tree = json.loads(tree_path.read_text())
    except Exception:
        return _fallback_ordering(run_dir)

    root = tree.get("root") if isinstance(tree, dict) else None
    if not isinstance(root, dict):
        return _fallback_ordering(run_dir)

    centrality = _load_centrality(run_dir)

    # Bucket tree descendants (children and below) by their declared layer.
    # The root is the topic itself and is NOT emitted as its own section —
    # sections are the investigative questions beneath it.
    buckets: dict[str, list[dict]] = {layer: [] for layer in LAYERS}
    descendants: list[dict] = []
    for child in root.get("children", []) or []:
        _flatten_nodes(child, descendants)
    for node in descendants:
        layer = node.get("layer")
        question = node.get("question")
        if layer not in buckets or not question:
            continue
        cent = centrality.get(question, 0.0)
        buckets[layer].append(
            {"layer": layer, "question": question, "centrality": cent}
        )

    result: list[dict] = []
    for layer in LAYERS:
        bucket = buckets[layer]
        if not bucket:
            continue  # D-15: silently skip layers with no evidence.
        # D-13: intra-layer sort by centrality descending; stable for ties.
        bucket.sort(key=lambda row: -row["centrality"])
        result.extend(bucket)
    return result


__all__ = ["compute_section_order", "append_log", "LAYERS"]
