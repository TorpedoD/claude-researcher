#!/usr/bin/env python3
"""Graph post-processing helper (GRAPH-02).

Normalizes graphify output to contract shape and writes standalone JSONs.
Guards against empty corpora (0 nodes or 0 edges): writes stub files
(empty arrays / empty object) and appends an `empty_corpus_guard` warning
row to run_log.md rather than silently propagating a malformed graph.

Invoked from `research` SKILL.md Phase 3 Step 2d.
Covered by tests/test_graph_postprocessing.py.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Optional


def _append_log(run_dir: Path, phase: str, action: str, status: str, detail: str) -> None:
    """Mirror of SKILL.md append_log helper for standalone invocation.

    Writes a markdown-table row to <run_dir>/logs/run_log.md, creating the
    file with a header if it does not yet exist.
    """
    log_path = Path(run_dir) / "logs" / "run_log.md"
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = f"| {ts} | {phase} | {action} | {status} | {detail} |"
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "## Run Log\n\n"
            "| Timestamp | Phase | Action | Status | Detail |\n"
            "|---|---|---|---|---|\n"
        )
        log_path.write_text(header + row + "\n")
    else:
        with open(log_path, "a") as f:
            f.write(row + "\n")


def post_process(
    graphify_out: Path,
    run_dir: Path,
    central: Optional[list] = None,
    isolated: Optional[list] = None,
    cluster_map: Optional[dict] = None,
    communities_list: Optional[list] = None,
) -> dict:
    """Normalize graphify output and write standalone JSONs.

    Reads `<graphify_out>/graph.json` (networkx-native shape with `links`),
    renames `links` → `edges`, injects `communities[]`, and writes
    central_nodes.json, isolated_nodes.json, cluster_map.json.

    Empty corpus guard (GRAPH-02 / D-01, D-02): if the graph has 0 nodes
    or 0 links, stub files are written (empty arrays / empty object), a
    warning row is appended to run_log.md, and the function returns early.

    Args:
        graphify_out: Directory holding graph.json (usually <run_dir>/collect/graphify-out).
        run_dir: Run directory (for run_log.md path).
        central: Central nodes list (god nodes metadata). Defaults to [].
        isolated: Isolated nodes list. Defaults to [].
        cluster_map: Community -> member list map. Defaults to {}.
        communities_list: Already-shaped communities array for graph.json.
            If omitted, derived from cluster_map.

    Returns:
        The final graph_data dict that was written to graph.json.
    """
    graphify_out = Path(graphify_out)
    run_dir = Path(run_dir)
    graph_path = graphify_out / "graph.json"
    graph_data = json.loads(graph_path.read_text())

    # Empty corpus guard (GRAPH-02 / D-01, D-02)
    if len(graph_data.get("nodes", [])) == 0 or len(graph_data.get("links", [])) == 0:
        empty: dict[str, Any] = {"nodes": [], "edges": [], "communities": []}
        graph_path.write_text(json.dumps(empty, indent=2))
        (graphify_out / "central_nodes.json").write_text(json.dumps([], indent=2))
        (graphify_out / "isolated_nodes.json").write_text(json.dumps([], indent=2))
        (graphify_out / "cluster_map.json").write_text(json.dumps({}, indent=2))
        _append_log(
            run_dir,
            "graph",
            "empty_corpus_guard",
            "warn",
            "Graph has 0 edges — stub files written, synthesis will fall back to alphabetical ordering",
        )
        return empty

    # Normal path: rename links → edges and inject communities[]
    central = central if central is not None else []
    isolated = isolated if isolated is not None else []
    cluster_map = cluster_map if cluster_map is not None else {}
    if communities_list is None:
        communities_list = [
            {"id": int(k), "members": v} for k, v in cluster_map.items()
        ]

    graph_data["edges"] = graph_data.pop("links")
    graph_data["communities"] = communities_list
    graph_data["central_nodes"] = central
    graph_data["isolated_nodes"] = isolated
    graph_data["cluster_map"] = cluster_map
    graph_path.write_text(json.dumps(graph_data, indent=2))

    (graphify_out / "central_nodes.json").write_text(json.dumps(central, indent=2))
    (graphify_out / "isolated_nodes.json").write_text(json.dumps(isolated, indent=2))
    (graphify_out / "cluster_map.json").write_text(json.dumps(cluster_map, indent=2))

    return graph_data
