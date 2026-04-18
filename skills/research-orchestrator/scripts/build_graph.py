#!/usr/bin/env python3
"""
Build the Graphify knowledge graph for a research run.

Reads .graphify_detect.json and .graphify_extract.json from the run directory,
builds the graph, writes all contract-required output files to
collect/graphify-out/, and prints a summary line for the orchestrator to log.

Usage:
    python3 build_graph.py --run-dir <path>

Outputs (all under <run_dir>/collect/graphify-out/):
    graph.json         full graph with injected edges/communities/central/isolated/cluster_map
    graph.html         interactive HTML visualization
    central_nodes.json top-connected nodes with betweenness
    isolated_nodes.json nodes with degree <= 1
    cluster_map.json   community membership map
    GRAPH_REPORT.md    plain-language report
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run-dir", required=True, help="Path to the research run directory")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    extract_path = run_dir / ".graphify_extract.json"
    detect_path = run_dir / ".graphify_detect.json"

    if not extract_path.exists():
        print(f"ERROR: {extract_path} not found", file=sys.stderr)
        sys.exit(1)
    if not detect_path.exists():
        print(f"ERROR: {detect_path} not found", file=sys.stderr)
        sys.exit(1)

    from graphify.build import build_from_json
    from graphify.cluster import cluster, score_all
    from graphify.analyze import god_nodes
    from graphify.export import to_json, to_html
    from graphify.report import generate
    import networkx as nx

    extraction = json.loads(extract_path.read_text())
    detection = json.loads(detect_path.read_text())

    G = build_from_json(extraction)
    communities = cluster(G)
    gods = god_nodes(G)

    out = run_dir / "collect" / "graphify-out"
    out.mkdir(parents=True, exist_ok=True)
    to_json(G, communities, str(out / "graph.json"))
    to_html(G, communities, str(out / "graph.html"))

    central = [{"id": g["id"], "label": g["label"], "degree": g["edges"],
                "betweenness": nx.betweenness_centrality(G).get(g["id"], 0.0)}
               for g in gods]
    (out / "central_nodes.json").write_text(json.dumps(central, indent=2))

    isolated = [{"id": n, "label": G.nodes[n].get("label", n), "degree": d}
                for n, d in G.degree() if d <= 1]
    (out / "isolated_nodes.json").write_text(json.dumps(isolated, indent=2))

    cmap = {str(k): v for k, v in communities.items()}
    (out / "cluster_map.json").write_text(json.dumps(cmap, indent=2))

    graph_data = json.loads((out / "graph.json").read_text())

    if len(graph_data.get("nodes", [])) == 0 or len(graph_data.get("links", [])) == 0:
        empty = {"nodes": [], "edges": [], "communities": []}
        (out / "graph.json").write_text(json.dumps(empty, indent=2))
        (out / "central_nodes.json").write_text(json.dumps([], indent=2))
        (out / "isolated_nodes.json").write_text(json.dumps([], indent=2))
        (out / "cluster_map.json").write_text(json.dumps({}, indent=2))
        print("EMPTY_CORPUS_GUARD: 0 nodes/edges — stub files written")
    else:
        graph_data["edges"] = graph_data.pop("links")
        graph_data["communities"] = [{"id": int(k), "members": v} for k, v in cmap.items()]
        graph_data["central_nodes"] = central
        graph_data["isolated_nodes"] = isolated
        graph_data["cluster_map"] = cmap
        (out / "graph.json").write_text(json.dumps(graph_data, indent=2))

    labels = {cid: f"Community {cid}" for cid in communities}
    cohesion = score_all(G, communities)
    report = generate(G, communities, cohesion, labels, gods, [], detection,
                      {"input": 0, "output": 0}, str(run_dir / "collect" / "evidence"))
    (out / "GRAPH_REPORT.md").write_text(report)

    extract_path.unlink(missing_ok=True)
    detect_path.unlink(missing_ok=True)

    print(f"Graph: {len(G.nodes)} nodes, {len(G.edges)} edges, {len(communities)} communities")
    print(f"Central: {len(central)} nodes, Isolated: {len(isolated)} nodes")


if __name__ == "__main__":
    main()
