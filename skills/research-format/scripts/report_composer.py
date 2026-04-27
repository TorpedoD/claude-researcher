#!/usr/bin/env python3
"""Script-backed report composition helpers for claim_pipeline_v1.

The prose can still be written by the formatter agent, but the pipeline
invariants are mechanical: section slices are mandatory, global claim state is
not a fallback, and assembly/audit use small section metadata first.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
FORMAT_REFS = SCRIPT_DIR.parent / "references"

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
NUMERIC_REF_RE = re.compile(r"(?<!\!)\[(\d+)\](?:\([^)]+\))?")
EXTERNAL_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def rel(path: Path, run_dir: Path) -> str:
    return str(path.relative_to(run_dir))


def schema_errors(artifact: dict[str, Any], schema_name: str) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema is not installed; cannot validate formatter artifact schemas"]

    schema = load_json(FORMAT_REFS / schema_name)
    validator = jsonschema.Draft202012Validator(schema)
    return [err.message for err in validator.iter_errors(artifact)]


def format_preferences(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    manifest = load_json(manifest_path) if manifest_path.exists() else {}
    prefs = manifest.get("format_preferences") or {}
    return {
        "mode": prefs.get("mode", "Full Report"),
        "audience": prefs.get("audience", "external"),
        "tone": prefs.get("tone", "professional"),
        **{k: v for k, v in prefs.items() if k not in {"mode", "audience", "tone"}},
    }


def planned_section_order(run_dir: Path) -> list[str]:
    hints_path = run_dir / "synthesis" / "section_graph_hints.json"
    if hints_path.exists():
        hints = load_json(hints_path)
        return list(hints.get("planned_section_ids", []) or [])
    return []


def build_plan(run_dir: Path) -> dict[str, Any]:
    brief_dir = run_dir / "synthesis" / "section_briefs"
    slice_dir = run_dir / "synthesis" / "claim_slices"
    if not brief_dir.exists():
        raise FileNotFoundError("missing synthesis/section_briefs")
    if not slice_dir.exists():
        raise FileNotFoundError("missing synthesis/claim_slices")

    briefs = {path.stem: path for path in sorted(brief_dir.glob("*.json"))}
    order = planned_section_order(run_dir)
    ordered_ids = [sid for sid in order if sid in briefs] + [
        sid for sid in sorted(briefs) if sid not in set(order)
    ]
    if not ordered_ids:
        raise ValueError("no section briefs found")

    sections: list[dict[str, Any]] = []
    missing_slices: list[str] = []
    for idx, section_id in enumerate(ordered_ids, start=1):
        brief_path = briefs[section_id]
        slice_path = slice_dir / f"{section_id}.json"
        if not slice_path.exists():
            missing_slices.append(f"synthesis/claim_slices/{section_id}.json")
            continue
        brief = load_json(brief_path)
        claim_slice = load_json(slice_path)
        slice_errors = validate_claim_slice_shape(claim_slice, f"synthesis/claim_slices/{section_id}.json")
        if slice_errors:
            raise ValueError("; ".join(slice_errors))
        if claim_slice.get("section_id") != section_id:
            raise ValueError(f"{rel(slice_path, run_dir)} section_id does not match filename")
        source_ids = sorted({source["source_id"] for source in sources_for_slice(claim_slice)})
        sections.append({
            "section_id": section_id,
            "title": brief["title"],
            "order": idx,
            "section_brief_path": f"synthesis/section_briefs/{section_id}.json",
            "claim_slice_path": f"synthesis/claim_slices/{section_id}.json",
            "output_path": f"output/sections/{section_id}.md",
            "source_ids": source_ids,
        })

    if missing_slices:
        raise FileNotFoundError(
            "missing required claim slice(s); no claim_bank.json fallback is allowed: "
            + ", ".join(missing_slices)
        )

    plan = {
        "canonical_report_path": "output/report.md",
        "sections": sections,
        "format_preferences": format_preferences(run_dir),
    }
    errors = schema_errors(plan, "assembly_plan.schema.json")
    if errors:
        raise ValueError("assembly_plan schema errors: " + "; ".join(errors))
    write_json(run_dir / "output" / "assembly_plan.json", plan)
    return plan


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def validate_section_meta(meta_path: Path) -> list[str]:
    meta = load_json(meta_path)
    return schema_errors(meta, "section_meta.schema.json")


def claims_for_slice(claim_slice: dict[str, Any]) -> list[dict[str, Any]]:
    return (
        list(claim_slice.get("required_claims", []))
        + list(claim_slice.get("optional_claims", []))
    )


def sources_for_slice(claim_slice: dict[str, Any]) -> list[dict[str, Any]]:
    return list(claim_slice.get("source_records", []))


def validate_claim_slice_shape(claim_slice: dict[str, Any], context: str) -> list[str]:
    errors: list[str] = []
    required = {"section_id", "section_brief_path", "required_claims", "optional_claims", "source_records", "boundary_rules"}
    missing = sorted(required - set(claim_slice))
    if missing:
        errors.append(f"{context} missing compact claim-slice field(s): {missing}")
    legacy = sorted({"claims", "sources"} & set(claim_slice))
    if legacy:
        errors.append(f"{context} uses legacy claim-slice field(s): {legacy}")

    for claim in claim_slice.get("required_claims", []):
        claim_id = claim.get("id", "<unknown>")
        if "text" not in claim:
            errors.append(f"{context} required_claim {claim_id} is missing text")
        if "content_hash" in claim:
            errors.append(f"{context} required_claim {claim_id} duplicates content_hash")
    for claim in claim_slice.get("optional_claims", []):
        claim_id = claim.get("id", "<unknown>")
        if "brief" not in claim:
            errors.append(f"{context} optional_claim {claim_id} is missing brief")
        if "text" in claim or "content_hash" in claim:
            errors.append(f"{context} optional_claim {claim_id} is not compact")
    return errors


def source_maps_for_slice(claim_slice: dict[str, Any]) -> tuple[set[str], set[str], dict[str, str]]:
    claim_ids = {claim["id"] for claim in claims_for_slice(claim_slice)}
    source_ids = {source["source_id"] for source in sources_for_slice(claim_slice)}
    url_to_title = {source["url"]: source["title"] for source in sources_for_slice(claim_slice)}
    return claim_ids, source_ids, url_to_title


def is_external_url(url: str) -> bool:
    return bool(EXTERNAL_URL_RE.match(url.strip()))


def citation_errors(text: str, allowed_url_to_title: dict[str, str], context: str) -> list[str]:
    errors: list[str] = []
    for match in NUMERIC_REF_RE.finditer(text):
        errors.append(f"{context} uses numeric citation style near [{match.group(1)}]")

    for label, url in LINK_RE.findall(text):
        if label.strip().isdigit():
            errors.append(f"{context} uses numeric markdown citation [{label}]({url})")
        if not is_external_url(url):
            continue
        expected_title = allowed_url_to_title.get(url)
        if not expected_title:
            errors.append(f"{context} cites unknown source URL [{label}]({url})")
        elif label != expected_title:
            errors.append(
                f"{context} cites {url} as [{label}], expected [{expected_title}]"
            )
    return errors


def audit(run_dir: Path) -> dict[str, Any]:
    plan_path = run_dir / "output" / "assembly_plan.json"
    if not plan_path.exists():
        build_plan(run_dir)
    plan = load_json(plan_path)

    errors: list[str] = []
    warnings: list[str] = []
    section_meta_files: list[str] = []
    claim_counts: dict[str, int] = {}
    missing_required_claim_ids: set[str] = set()

    for section in sorted(plan.get("sections", []), key=lambda row: row["order"]):
        sid = section["section_id"]
        brief_path = run_dir / section["section_brief_path"]
        slice_path = run_dir / section["claim_slice_path"]
        md_path = run_dir / section["output_path"]
        meta_path = md_path.with_suffix(".meta.json")

        if not brief_path.exists():
            errors.append(f"missing section brief: {section['section_brief_path']}")
            continue
        if not slice_path.exists():
            errors.append(f"missing claim slice: {section['claim_slice_path']}")
            continue
        if not md_path.exists():
            errors.append(f"missing section markdown: {section['output_path']}")
            continue
        if not meta_path.exists():
            errors.append(f"missing section metadata: {rel(meta_path, run_dir)}")
            continue

        section_meta_files.append(rel(meta_path, run_dir))
        meta_errors = validate_section_meta(meta_path)
        errors.extend(f"{rel(meta_path, run_dir)} schema error: {err}" for err in meta_errors)
        if meta_errors:
            continue

        brief = load_json(brief_path)
        claim_slice = load_json(slice_path)
        errors.extend(validate_claim_slice_shape(claim_slice, section["claim_slice_path"]))
        meta = load_json(meta_path)
        slice_claim_ids, slice_source_ids, allowed_url_to_title = source_maps_for_slice(claim_slice)

        used_claim_ids = set(meta.get("claim_ids_used", []))
        used_source_ids = set(meta.get("source_ids_used", []))
        for claim_id in used_claim_ids:
            claim_counts[claim_id] = claim_counts.get(claim_id, 0) + 1
        missing_required_claim_ids |= set(brief.get("must_include_claim_ids", [])) - used_claim_ids

        unknown_claims = used_claim_ids - slice_claim_ids
        if unknown_claims:
            errors.append(f"{sid} metadata uses claim_ids outside claim slice: {sorted(unknown_claims)}")
        unknown_sources = used_source_ids - slice_source_ids
        if unknown_sources:
            errors.append(f"{sid} metadata uses source_ids outside claim slice: {sorted(unknown_sources)}")

        section_text = md_path.read_text()
        errors.extend(citation_errors(section_text, allowed_url_to_title, section["output_path"]))

    repeated_claim_ids = sorted([claim_id for claim_id, count in claim_counts.items() if count > 1])
    for claim_id in repeated_claim_ids:
        errors.append(f"repeated claim_id across sections: {claim_id}")
    for claim_id in sorted(missing_required_claim_ids):
        errors.append(f"missing required claim_id from section output: {claim_id}")

    report_path = run_dir / "output" / "report.md"
    if report_path.exists():
        all_url_to_title: dict[str, str] = {}
        for section in plan.get("sections", []):
            slice_path = run_dir / section["claim_slice_path"]
            if slice_path.exists():
                _, _, url_to_title = source_maps_for_slice(load_json(slice_path))
                all_url_to_title.update(url_to_title)
        errors.extend(citation_errors(report_path.read_text(), all_url_to_title, "output/report.md"))

    audit_payload = {
        "status": "error" if errors else ("warn" if warnings else "pass"),
        "canonical_report_path": "output/report.md",
        "section_meta_files": sorted(set(section_meta_files)),
        "repeated_claim_ids": repeated_claim_ids,
        "missing_required_claim_ids": sorted(missing_required_claim_ids),
        "warnings": warnings,
        "errors": errors,
    }
    schema_issues = schema_errors(audit_payload, "formatter_audit.schema.json")
    if schema_issues:
        audit_payload["status"] = "error"
        audit_payload["errors"].extend(f"formatter_audit schema error: {err}" for err in schema_issues)
    write_json(run_dir / "output" / "formatter_audit.json", audit_payload)
    return audit_payload


def markdown_anchor(title: str) -> str:
    anchor = re.sub(r"[^a-z0-9\s-]", "", title.lower())
    anchor = re.sub(r"\s+", "-", anchor.strip())
    return anchor


def assemble(run_dir: Path) -> Path:
    plan_path = run_dir / "output" / "assembly_plan.json"
    if not plan_path.exists():
        build_plan(run_dir)
    plan = load_json(plan_path)

    lines: list[str] = []
    title = load_json(run_dir / "manifest.json").get("topic", "Research Report") if (run_dir / "manifest.json").exists() else "Research Report"
    lines.extend([f"# {title}", "", "## Table of Contents"])
    for section in sorted(plan.get("sections", []), key=lambda row: row["order"]):
        lines.append(f"- [{section['title']}](#{markdown_anchor(section['title'])})")
    lines.append("- [Sources](#sources)")
    lines.append("")

    used_source_ids: set[str] = set()
    source_by_id: dict[str, dict[str, Any]] = {}
    for section in sorted(plan.get("sections", []), key=lambda row: row["order"]):
        md_path = run_dir / section["output_path"]
        meta_path = md_path.with_suffix(".meta.json")
        if not md_path.exists():
            raise FileNotFoundError(f"missing section markdown: {section['output_path']}")
        if not meta_path.exists():
            raise FileNotFoundError(f"missing section metadata: {rel(meta_path, run_dir)}")

        text = md_path.read_text().strip()
        if text.startswith("# "):
            text = re.sub(r"^#\s+", "## ", text, count=1)
        elif text.startswith("### "):
            text = re.sub(r"^###\s+", "## ", text, count=1)
        elif not text.startswith("## "):
            text = f"## {section['title']}\n\n{text}"
        lines.extend([text, ""])

        meta = load_json(meta_path)
        used_source_ids |= set(meta.get("source_ids_used", []))
        claim_slice = load_json(run_dir / section["claim_slice_path"])
        for source in sources_for_slice(claim_slice):
            source_by_id[source["source_id"]] = source

    lines.extend(["## Sources", ""])
    for source_id in sorted(used_source_ids):
        source = source_by_id.get(source_id)
        if not source:
            continue
        lines.append(f"- [{source['title']}]({source['url']})")
    lines.append("")

    report_path = run_dir / "output" / "report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines))
    audit(run_dir)
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Claim-sliced report composer")
    parser.add_argument("command", choices=["build-plan", "validate-section-meta", "audit", "assemble"])
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--meta")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    try:
        if args.command == "build-plan":
            print(json.dumps(build_plan(run_dir), indent=2))
        elif args.command == "validate-section-meta":
            if not args.meta:
                raise ValueError("--meta is required for validate-section-meta")
            errors = validate_section_meta(Path(args.meta))
            print(json.dumps({"status": "error" if errors else "pass", "errors": errors}, indent=2))
            return 1 if errors else 0
        elif args.command == "audit":
            result = audit(run_dir)
            print(json.dumps(result, indent=2))
            return 1 if result["status"] == "error" else 0
        elif args.command == "assemble":
            path = assemble(run_dir)
            print(str(path))
    except Exception as exc:
        print(json.dumps({"status": "error", "errors": [str(exc)]}, indent=2), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
