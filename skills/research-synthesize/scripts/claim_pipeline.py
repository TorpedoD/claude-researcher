#!/usr/bin/env python3
"""Helpers for the claim-based research pipeline.

The synthesizer still performs semantic extraction, but this script owns the
mechanical invariants: stable IDs, claim-delta merging, per-section slices,
compact graph hints, and Gate 3 readiness checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


BOUNDARY_RULES = [
    "Each claim_id has exactly one primary_section_id.",
    "Claims primary to another section may be referenced only as cross-links, not rewritten.",
    "Do not read global claim_bank.json or inventory.json during section composition.",
]

SCRIPT_DIR = Path(__file__).resolve().parent
SYNTH_REFS = SCRIPT_DIR.parent / "references"


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(normalize_text(text).encode()).hexdigest()


def source_key(source: dict[str, Any]) -> str:
    return str(source.get("url") or source.get("evidence_file") or source.get("source_title") or "").rstrip("/")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_text(value)).strip("-")
    return slug or "section"


def next_numbered_id(existing: list[str], prefix: str) -> str:
    max_n = 0
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
    for value in existing:
        match = pattern.match(value)
        if match:
            max_n = max(max_n, int(match.group(1)))
    return f"{prefix}_{max_n + 1:03d}"


def planned_sections(run_dir: Path) -> list[dict[str, str]]:
    plan = load_json(run_dir / "scope" / "plan.json")
    names: list[str] = []

    for entry in plan.get("subtopics", []) or []:
        name = entry.get("name")
        if name:
            names.append(str(name))

    seen: set[str] = set()
    sections: list[dict[str, str]] = []
    registry = load_json(run_dir / "synthesis" / "global_id_registry.json", default={
        "source_ids": {},
        "claim_ids": {},
        "section_ids": {},
        "content_hashes": {},
    })
    for name in names:
        key = normalize_text(name)
        section_id = registry.get("section_ids", {}).get(key, slugify(name))
        if section_id in seen:
            continue
        seen.add(section_id)
        sections.append({"section_id": section_id, "title": name, "key": key})
    return sections


def init_registry(run_dir: Path) -> dict[str, Any]:
    synth_dir = run_dir / "synthesis"
    synth_dir.mkdir(parents=True, exist_ok=True)
    registry = load_json(synth_dir / "global_id_registry.json", default={
        "source_ids": {},
        "claim_ids": {},
        "section_ids": {},
        "content_hashes": {},
    })

    inventory = load_json(run_dir / "collect" / "inventory.json")
    existing_sources = list(registry["source_ids"].values())
    for source in inventory.get("sources", []):
        key = source_key(source)
        if not key or key in registry["source_ids"]:
            continue
        new_id = next_numbered_id(existing_sources, "src")
        registry["source_ids"][key] = new_id
        existing_sources.append(new_id)

    plan = load_json(run_dir / "scope" / "plan.json")
    names = [entry.get("name") for entry in plan.get("subtopics", []) or [] if entry.get("name")]
    used_section_ids = set(registry["section_ids"].values())
    for name in names:
        key = normalize_text(str(name))
        if key in registry["section_ids"]:
            continue
        base = slugify(str(name))
        section_id = base
        i = 2
        while section_id in used_section_ids:
            section_id = f"{base}-{i}"
            i += 1
        registry["section_ids"][key] = section_id
        used_section_ids.add(section_id)

    write_json(synth_dir / "global_id_registry.json", registry)
    return registry


def source_lookup(run_dir: Path, registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    inventory = load_json(run_dir / "collect" / "inventory.json")
    out: dict[str, dict[str, Any]] = {}
    for source in inventory.get("sources", []):
        sid = registry["source_ids"].get(source_key(source))
        if not sid:
            continue
        out[sid] = {
            "source_id": sid,
            "title": source.get("source_title", sid),
            "url": source.get("url", source.get("evidence_file", sid)),
            "tier": source.get("source_tier", 5),
        }
    return out


def _claim_source_ids(delta: dict[str, Any], registry: dict[str, Any]) -> list[str]:
    ids = list(delta.get("source_ids", []) or [])
    for key in delta.get("source_keys", []) or []:
        sid = registry["source_ids"].get(str(key).rstrip("/"))
        if sid:
            ids.append(sid)
    return sorted(set(ids))


def merge_claim_deltas(run_dir: Path) -> dict[str, Any]:
    registry = init_registry(run_dir)
    sections_by_key = registry["section_ids"]
    section_ids = set(sections_by_key.values())
    delta_dir = run_dir / "synthesis" / "claim_deltas"
    claims_by_hash: dict[str, dict[str, Any]] = {}
    existing_claim_ids = list(registry["claim_ids"].values())

    for path in sorted(delta_dir.glob("*.json")):
        payload = load_json(path)
        deltas = payload.get("claims", payload if isinstance(payload, list) else [])
        for delta in deltas:
            text = str(delta.get("text") or delta.get("claim") or "").strip()
            if not text:
                continue
            h = delta.get("content_hash") or content_hash(text)
            claim_id = registry["claim_ids"].get(h)
            if not claim_id:
                claim_id = next_numbered_id(existing_claim_ids, "claim")
                registry["claim_ids"][h] = claim_id
                registry["content_hashes"][h] = claim_id
                existing_claim_ids.append(claim_id)

            section_id = delta.get("primary_section_id")
            if not section_id:
                section_name = str(delta.get("section") or delta.get("section_title") or "")
                section_id = sections_by_key.get(normalize_text(section_name), slugify(section_name))
            if section_id not in section_ids:
                section_id = next(iter(section_ids), "unassigned")

            source_ids = _claim_source_ids(delta, registry)
            if not source_ids:
                continue

            existing = claims_by_hash.get(h)
            if existing:
                existing["source_ids"] = sorted(set(existing["source_ids"]) | set(source_ids))
                existing["entities"] = sorted(set(existing.get("entities", [])) | set(delta.get("entities", []) or []))
                continue

            claim = {
                "id": claim_id,
                "text": text,
                "content_hash": h,
                "primary_section_id": section_id,
                "source_ids": source_ids,
                "confidence": delta.get("confidence", "medium"),
                "salience": delta.get("salience", "medium"),
                "include_in_report": bool(delta.get("include_in_report", True)),
            }
            if delta.get("entities"):
                claim["entities"] = sorted(set(delta["entities"]))
            if delta.get("contradiction_ids"):
                claim["contradiction_ids"] = sorted(set(delta["contradiction_ids"]))
            claims_by_hash[h] = claim

    claim_bank = {
        "claims": sorted(claims_by_hash.values(), key=lambda row: row["id"]),
        "metadata": {"total_claims": len(claims_by_hash), "schema_version": "claim_bank.v1"},
    }
    write_json(run_dir / "synthesis" / "global_id_registry.json", registry)
    write_json(run_dir / "synthesis" / "claim_bank.json", claim_bank)
    return claim_bank


def write_legacy_claim_index(run_dir: Path, claim_bank: dict[str, Any]) -> None:
    legacy = {
        "claims": [
            {
                "claim_text": claim["text"],
                "claim_hash": claim["content_hash"],
                "section": claim["primary_section_id"],
                "sources": [{"source_id": sid} for sid in claim["source_ids"]],
            }
            for claim in claim_bank.get("claims", [])
        ],
        "metadata": {
            "total_claims": claim_bank.get("metadata", {}).get("total_claims", 0),
            "compatibility_only": True,
        },
    }
    write_json(run_dir / "synthesis" / "claim_index.json", legacy)


def build_entity_index(run_dir: Path, claim_bank: dict[str, Any] | None = None) -> dict[str, Any]:
    claim_bank = claim_bank or load_json(run_dir / "synthesis" / "claim_bank.json")
    entities: dict[str, dict[str, Any]] = {}
    for claim in claim_bank.get("claims", []):
        for entity in claim.get("entities", []) or []:
            normalized = normalize_text(entity)
            row = entities.setdefault(
                normalized,
                {
                    "entity": entity,
                    "normalized": normalized,
                    "claim_ids": [],
                    "section_ids": [],
                    "source_ids": [],
                },
            )
            row["claim_ids"].append(claim["id"])
            row["section_ids"].append(claim["primary_section_id"])
            row["source_ids"].extend(claim.get("source_ids", []))

    entity_index = {
        "entities": [
            {
                "entity": row["entity"],
                "normalized": row["normalized"],
                "claim_ids": sorted(set(row["claim_ids"])),
                "section_ids": sorted(set(row["section_ids"])),
                "source_ids": sorted(set(row["source_ids"])),
            }
            for row in sorted(entities.values(), key=lambda item: item["normalized"])
        ],
        "metadata": {"total_entities": len(entities), "schema_version": "entity_index.v1"},
    }
    write_json(run_dir / "synthesis" / "entity_index.json", entity_index)
    return entity_index


def build_graph_artifacts(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    claim_bank = load_json(run_dir / "synthesis" / "claim_bank.json")
    entity_index = load_json(run_dir / "synthesis" / "entity_index.json", default=None)
    if entity_index is None:
        entity_index = build_entity_index(run_dir, claim_bank)
    sections = planned_sections(run_dir)
    planned_ids = [section["section_id"] for section in sections]
    claims = claim_bank.get("claims", [])

    by_entity: dict[str, set[str]] = {}
    for entity in entity_index.get("entities", []):
        by_entity[entity["normalized"]] = set(entity.get("claim_ids", []))

    graph_claims = []
    for claim in claims:
        related: set[str] = set()
        for entity in claim.get("entities", []) or []:
            related |= by_entity.get(normalize_text(entity), set())
        related.discard(claim["id"])
        graph_claims.append({
            "claim_id": claim["id"],
            "related_claim_ids": sorted(related),
            "entities": claim.get("entities", []),
            "relationship_type": "context",
            "graph_cluster": claim["primary_section_id"],
            "centrality": 0 if not claims else min(1.0, len(related) / max(1, len(claims) - 1)),
        })

    section_rows = []
    for section in sections:
        section_claims = [claim for claim in claims if claim["primary_section_id"] == section["section_id"]]
        entity_counts: dict[str, int] = {}
        related_sections: set[str] = set()
        for claim in section_claims:
            for entity in claim.get("entities", []) or []:
                entity_counts[entity] = entity_counts.get(entity, 0) + 1
            for graph_claim in graph_claims:
                if graph_claim["claim_id"] != claim["id"]:
                    continue
                related_sections |= {
                    other["primary_section_id"]
                    for other in claims
                    if other["id"] in graph_claim["related_claim_ids"]
                    and other["primary_section_id"] != section["section_id"]
                }
        related_sections &= set(planned_ids)
        section_rows.append({
            "section_id": section["section_id"],
            "graph_cluster": section["section_id"],
            "central_entities": [entity for entity, _ in sorted(entity_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:8]],
            "bridge_entities": [],
            "related_sections": sorted(related_sections),
            "isolated_claims": [
                claim["id"] for claim in section_claims
                if not next((row for row in graph_claims if row["claim_id"] == claim["id"]), {}).get("related_claim_ids")
            ],
            "recommended_cross_links": [
                {"to": target, "reason": f"Claims share entities with {target}."}
                for target in sorted(related_sections)
            ],
        })

    claim_graph_map = {"claims": graph_claims}
    section_graph_hints = {
        "planned_section_ids": planned_ids,
        "sections": section_rows,
        "graph_rules": {
            "advisory_only": True,
            "cannot_create_sections": True,
            "cannot_reorder_sections": True,
        },
    }
    write_json(run_dir / "synthesis" / "claim_graph_map.json", claim_graph_map)
    write_json(run_dir / "synthesis" / "section_graph_hints.json", section_graph_hints)
    return claim_graph_map, section_graph_hints


def required_slice_claim(claim: dict[str, Any]) -> dict[str, Any]:
    row = {
        "id": claim["id"],
        "text": claim["text"],
        "primary_section_id": claim["primary_section_id"],
        "source_ids": claim["source_ids"],
        "confidence": claim["confidence"],
        "salience": claim["salience"],
        "include_in_report": claim["include_in_report"],
    }
    if claim.get("entities"):
        row["entities"] = claim["entities"]
    if claim.get("contradiction_ids"):
        row["contradiction_ids"] = claim["contradiction_ids"]
    return row


def optional_slice_claim(claim: dict[str, Any]) -> dict[str, Any]:
    brief = re.sub(r"\s+", " ", claim["text"]).strip()
    if len(brief) > 180:
        brief = brief[:177].rstrip() + "..."
    row = {
        "id": claim["id"],
        "brief": brief,
        "primary_section_id": claim["primary_section_id"],
        "source_ids": claim["source_ids"],
        "confidence": claim["confidence"],
        "salience": claim["salience"],
        "include_in_report": claim["include_in_report"],
    }
    if claim.get("entities"):
        row["entities"] = claim["entities"]
    return row


def build_section_artifacts(run_dir: Path) -> None:
    registry = init_registry(run_dir)
    claim_bank = load_json(run_dir / "synthesis" / "claim_bank.json")
    source_by_id = source_lookup(run_dir, registry)
    sections = planned_sections(run_dir)
    brief_dir = run_dir / "synthesis" / "section_briefs"
    slice_dir = run_dir / "synthesis" / "claim_slices"
    brief_dir.mkdir(parents=True, exist_ok=True)
    slice_dir.mkdir(parents=True, exist_ok=True)

    for section in sections:
        section_id = section["section_id"]
        claims = [claim for claim in claim_bank.get("claims", []) if claim["primary_section_id"] == section_id]
        must = [claim["id"] for claim in claims if claim.get("include_in_report") and claim.get("salience") != "low"]
        optional = [claim["id"] for claim in claims if claim["id"] not in must]
        brief_path = brief_dir / f"{section_id}.json"
        existing = load_json(brief_path, default={})
        missing = existing.get("missing", [])
        brief = {
            "section_id": section_id,
            "title": section["title"],
            "summary": existing.get("summary") or (
                f"Section has {len(claims)} extracted claim(s)." if claims else "No claims extracted for this planned section."
            ),
            "must_include_claim_ids": must,
            "optional_claim_ids": optional,
            "boundary_rules": existing.get("boundary_rules") or BOUNDARY_RULES,
        }
        if existing.get("avoid"):
            brief["avoid"] = existing["avoid"]
        if missing:
            brief["missing"] = missing
        if existing.get("recommended_visuals"):
            brief["recommended_visuals"] = existing["recommended_visuals"]
        write_json(brief_path, brief)

        source_ids = sorted({sid for claim in claims for sid in claim.get("source_ids", [])})
        required_claims = [required_slice_claim(claim) for claim in claims if claim["id"] in must]
        optional_claims = [optional_slice_claim(claim) for claim in claims if claim["id"] in optional]
        claim_slice = {
            "section_id": section_id,
            "section_brief_path": f"synthesis/section_briefs/{section_id}.json",
            "required_claims": required_claims,
            "optional_claims": optional_claims,
            "source_records": [source_by_id[sid] for sid in source_ids if sid in source_by_id],
            "boundary_rules": BOUNDARY_RULES,
        }
        write_json(slice_dir / f"{section_id}.json", claim_slice)


def validate_readiness(run_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        "synthesis/global_id_registry.json",
        "synthesis/claim_bank.json",
        "synthesis/entity_index.json",
        "synthesis/claim_graph_map.json",
        "synthesis/section_graph_hints.json",
    ]
    for rel in required:
        if not (run_dir / rel).exists():
            errors.append(f"missing required artifact: {rel}")

    if errors:
        return {"status": "fail", "errors": errors, "warnings": warnings}

    schema_checks = [
        ("synthesis/global_id_registry.json", "global_id_registry.schema.json"),
        ("synthesis/claim_bank.json", "claim_bank.schema.json"),
        ("synthesis/entity_index.json", "entity_index.schema.json"),
        ("synthesis/claim_graph_map.json", "claim_graph_map.schema.json"),
        ("synthesis/section_graph_hints.json", "section_graph_hints.schema.json"),
    ]
    schema_checks.extend(
        (str(path.relative_to(run_dir)), "section_brief.schema.json")
        for path in sorted((run_dir / "synthesis" / "section_briefs").glob("*.json"))
    )
    schema_checks.extend(
        (str(path.relative_to(run_dir)), "claim_slice.schema.json")
        for path in sorted((run_dir / "synthesis" / "claim_slices").glob("*.json"))
    )
    errors.extend(validate_schema_checks(run_dir, schema_checks))

    registry = load_json(run_dir / "synthesis" / "global_id_registry.json")
    claim_bank = load_json(run_dir / "synthesis" / "claim_bank.json")
    source_ids = set(registry.get("source_ids", {}).values())
    claim_ids = {claim["id"] for claim in claim_bank.get("claims", [])}
    claims_by_section: dict[str, list[dict[str, Any]]] = {}
    for claim in claim_bank.get("claims", []):
        claims_by_section.setdefault(claim["primary_section_id"], []).append(claim)
        missing_sources = set(claim.get("source_ids", [])) - source_ids
        if missing_sources:
            errors.append(f"{claim['id']} references unknown source_ids: {sorted(missing_sources)}")

    for section in planned_sections(run_dir):
        section_id = section["section_id"]
        brief_path = run_dir / "synthesis" / "section_briefs" / f"{section_id}.json"
        slice_path = run_dir / "synthesis" / "claim_slices" / f"{section_id}.json"
        if not brief_path.exists():
            errors.append(f"missing section brief: {brief_path.relative_to(run_dir)}")
            continue
        if not slice_path.exists():
            errors.append(f"missing claim slice: {slice_path.relative_to(run_dir)}")
            continue
        brief = load_json(brief_path)
        claim_slice = load_json(slice_path)
        referenced = set(brief.get("must_include_claim_ids", [])) | set(brief.get("optional_claim_ids", []))
        unknown = referenced - claim_ids
        if unknown:
            errors.append(f"{section_id} brief references unknown claim_ids: {sorted(unknown)}")
        slice_claim_ids = {
            claim["id"]
            for claim in (
                claim_slice.get("required_claims", [])
                + claim_slice.get("optional_claims", [])
            )
        }
        if not referenced.issubset(slice_claim_ids):
            errors.append(f"{section_id} slice is missing brief claim_ids: {sorted(referenced - slice_claim_ids)}")
        if (
            not claims_by_section.get(section_id)
            and not brief.get("missing")
            and not gap_analysis_has_missing_reason(run_dir, section["title"])
        ):
            errors.append(f"{section_id} has no claims and no explicit missing evidence reason")

    hints = load_json(run_dir / "synthesis" / "section_graph_hints.json")
    planned = set(hints.get("planned_section_ids", []))
    for section in hints.get("sections", []):
        sid = section.get("section_id")
        if sid not in planned:
            errors.append(f"graph hints introduced unplanned section: {sid}")
        related = set(section.get("related_sections", []))
        if not related.issubset(planned):
            errors.append(f"{sid} graph hints reference unplanned sections: {sorted(related - planned)}")
        linked = {link.get("to") for link in section.get("recommended_cross_links", [])}
        if not linked.issubset(planned):
            errors.append(f"{sid} graph links reference unplanned sections: {sorted(linked - planned)}")

    return {"status": "fail" if errors else "pass", "errors": errors, "warnings": warnings}


def validate_schema_checks(run_dir: Path, checks: list[tuple[str, str]]) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema is not installed; cannot validate Slice 2 artifact schemas"]

    errors: list[str] = []
    for artifact_rel, schema_name in checks:
        artifact_path = run_dir / artifact_rel
        schema_path = SYNTH_REFS / schema_name
        if not artifact_path.exists():
            errors.append(f"missing schema target: {artifact_rel}")
            continue
        try:
            artifact = load_json(artifact_path)
            schema = load_json(schema_path)
            validator = jsonschema.Draft202012Validator(schema)
            for err in validator.iter_errors(artifact):
                errors.append(f"{artifact_rel} schema error: {err.message}")
        except Exception as exc:
            errors.append(f"{artifact_rel} schema validation failed: {exc}")
    return errors


def gap_analysis_has_missing_reason(run_dir: Path, section_title: str) -> bool:
    path = run_dir / "synthesis" / "gap_analysis.md"
    if not path.exists():
        return False
    text = path.read_text().lower()
    title = section_title.lower()
    return title in text and any(token in text for token in ("missing", "no claims", "no evidence", "0 sources"))


def run_all(run_dir: Path) -> dict[str, Any]:
    init_registry(run_dir)
    if (run_dir / "synthesis" / "claim_deltas").exists():
        merge_claim_deltas(run_dir)
    build_entity_index(run_dir)
    build_graph_artifacts(run_dir)
    build_section_artifacts(run_dir)
    return validate_readiness(run_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Claim pipeline helper")
    parser.add_argument("command", choices=[
        "init-registry",
        "merge-deltas",
        "write-legacy-claim-index",
        "build-entity-index",
        "build-graph-artifacts",
        "build-section-artifacts",
        "validate-readiness",
        "all",
    ])
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    run_dir = Path(args.run_dir)

    if args.command == "init-registry":
        result = init_registry(run_dir)
    elif args.command == "merge-deltas":
        result = merge_claim_deltas(run_dir)
    elif args.command == "write-legacy-claim-index":
        write_legacy_claim_index(run_dir, load_json(run_dir / "synthesis" / "claim_bank.json"))
        result = {"status": "pass", "path": "synthesis/claim_index.json"}
    elif args.command == "build-entity-index":
        result = build_entity_index(run_dir)
    elif args.command == "build-graph-artifacts":
        result = build_graph_artifacts(run_dir)[1]
    elif args.command == "build-section-artifacts":
        build_section_artifacts(run_dir)
        result = {"status": "pass"}
    elif args.command == "validate-readiness":
        result = validate_readiness(run_dir)
    else:
        result = run_all(run_dir)

    print(json.dumps(result, indent=2))
    return 1 if isinstance(result, dict) and result.get("status") == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
