"""Runtime tests for Slice 3 report composition and publishing split."""
import importlib.util
import json
import subprocess
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[3]
COMPOSER_SCRIPT = ROOT / "skills" / "research-format" / "scripts" / "report_composer.py"
MAKE_QMD_SCRIPT = ROOT / "skills" / "research-orchestrator" / "scripts" / "make_qmd.py"
PUBLISH_SCRIPT = ROOT / "skills" / "research-orchestrator" / "scripts" / "publish.sh"
FORMAT_REFS = ROOT / "skills" / "research-format" / "references"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def load_json(path: Path):
    return json.loads(path.read_text())


def validate(path: Path, schema_name: str):
    schema = load_json(FORMAT_REFS / schema_name)
    jsonschema.Draft202012Validator(schema).validate(load_json(path))


def make_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run-001"
    write_json(
        run_dir / "manifest.json",
        {
            "topic": "Cardano Research",
            "format_preferences": {
                "mode": "Full Report",
                "audience": "external",
                "tone": "professional",
                "quarto_output": "none",
            },
        },
    )
    write_json(
        run_dir / "synthesis" / "section_graph_hints.json",
        {
            "planned_section_ids": ["consensus"],
            "sections": [
                {
                    "section_id": "consensus",
                    "central_entities": ["Ouroboros"],
                    "related_sections": [],
                    "recommended_cross_links": [],
                }
            ],
            "graph_rules": {
                "advisory_only": True,
                "cannot_create_sections": True,
                "cannot_reorder_sections": True,
            },
        },
    )
    write_json(
        run_dir / "synthesis" / "section_briefs" / "consensus.json",
        {
            "section_id": "consensus",
            "title": "Consensus Mechanism",
            "summary": "Explains how consensus works.",
            "must_include_claim_ids": ["claim_001"],
            "optional_claim_ids": [],
            "boundary_rules": ["Do not rewrite claims primary to other sections."],
        },
    )
    write_json(
        run_dir / "synthesis" / "claim_slices" / "consensus.json",
        {
            "section_id": "consensus",
            "section_brief_path": "synthesis/section_briefs/consensus.json",
            "claims": [
                {
                    "id": "claim_001",
                    "text": "Cardano uses Ouroboros as its proof-of-stake consensus protocol.",
                    "content_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    "primary_section_id": "consensus",
                    "source_ids": ["src_001"],
                    "confidence": "high",
                    "salience": "high",
                    "include_in_report": True,
                }
            ],
            "sources": [
                {
                    "source_id": "src_001",
                    "title": "Cardano Docs",
                    "url": "https://example.com/cardano",
                    "tier": 1,
                }
            ],
            "boundary_rules": ["claim_001 is primary to consensus."],
        },
    )
    return run_dir


def write_section_outputs(run_dir: Path, *, claim_ids=None, source_ids=None, citation=None):
    claim_ids = ["claim_001"] if claim_ids is None else claim_ids
    source_ids = ["src_001"] if source_ids is None else source_ids
    citation = citation or "[Cardano Docs](https://example.com/cardano)"
    write_text(
        run_dir / "output" / "sections" / "consensus.md",
        f"## Consensus Mechanism\n\nCardano uses Ouroboros as its proof-of-stake consensus protocol. {citation}\n",
    )
    write_json(
        run_dir / "output" / "sections" / "consensus.meta.json",
        {
            "section_id": "consensus",
            "title": "Consensus Mechanism",
            "claim_ids_used": claim_ids,
            "source_ids_used": source_ids,
            "word_count": 11,
            "cross_links": [],
            "warnings": [],
        },
    )


def test_build_plan_creates_assembly_plan_from_briefs_and_slices(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)

    plan = composer.build_plan(run_dir)

    assert plan["canonical_report_path"] == "output/report.md"
    assert plan["sections"][0]["claim_slice_path"] == "synthesis/claim_slices/consensus.json"
    validate(run_dir / "output" / "assembly_plan.json", "assembly_plan.schema.json")


def test_composer_does_not_require_raw_research(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)

    assert not (run_dir / "synthesis" / "raw_research.md").exists()
    composer.build_plan(run_dir)

    assert (run_dir / "output" / "assembly_plan.json").exists()


def test_composition_fails_when_claim_slice_missing_and_does_not_fallback_to_claim_bank(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    (run_dir / "synthesis" / "claim_slices" / "consensus.json").unlink()
    write_json(
        run_dir / "synthesis" / "claim_bank.json",
        {"claims": [{"id": "claim_001", "text": "Do not use this fallback."}]},
    )

    with pytest.raises(FileNotFoundError) as exc:
        composer.build_plan(run_dir)

    assert "no claim_bank.json fallback is allowed" in str(exc.value)


def test_section_metadata_validates_against_schema(tmp_path):
    run_dir = make_run(tmp_path)
    write_section_outputs(run_dir)

    validate(run_dir / "output" / "sections" / "consensus.meta.json", "section_meta.schema.json")


def test_audit_passes_when_required_claims_used_once(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    composer.build_plan(run_dir)
    write_section_outputs(run_dir)

    result = composer.audit(run_dir)

    assert result["status"] == "pass"
    validate(run_dir / "output" / "formatter_audit.json", "formatter_audit.schema.json")


def test_audit_flags_repeated_claim_ids_across_sections(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    write_json(
        run_dir / "synthesis" / "section_briefs" / "security.json",
        {
            "section_id": "security",
            "title": "Security Model",
            "summary": "Explains security.",
            "must_include_claim_ids": [],
            "optional_claim_ids": ["claim_001"],
            "boundary_rules": ["Reference, do not rewrite, claims from other sections."],
        },
    )
    write_json(
        run_dir / "synthesis" / "claim_slices" / "security.json",
        {
            "section_id": "security",
            "section_brief_path": "synthesis/section_briefs/security.json",
            "claims": [
                {
                    "id": "claim_001",
                    "text": "Cardano uses Ouroboros as its proof-of-stake consensus protocol.",
                    "content_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    "primary_section_id": "security",
                    "source_ids": ["src_001"],
                    "confidence": "high",
                    "salience": "high",
                    "include_in_report": True,
                }
            ],
            "sources": [
                {
                    "source_id": "src_001",
                    "title": "Cardano Docs",
                    "url": "https://example.com/cardano",
                    "tier": 1,
                }
            ],
            "boundary_rules": ["claim_001 is a cross-section reference."],
        },
    )
    composer.build_plan(run_dir)
    write_section_outputs(run_dir)
    write_text(
        run_dir / "output" / "sections" / "security.md",
        "## Security Model\n\nSecurity references consensus. [Cardano Docs](https://example.com/cardano)\n",
    )
    write_json(
        run_dir / "output" / "sections" / "security.meta.json",
        {
            "section_id": "security",
            "title": "Security Model",
            "claim_ids_used": ["claim_001"],
            "source_ids_used": ["src_001"],
            "word_count": 5,
            "cross_links": [],
            "warnings": [],
        },
    )

    result = composer.audit(run_dir)

    assert result["status"] == "error"
    assert result["repeated_claim_ids"] == ["claim_001"]


def test_audit_flags_missing_required_claim_ids(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    composer.build_plan(run_dir)
    write_section_outputs(run_dir, claim_ids=[])

    result = composer.audit(run_dir)

    assert result["status"] == "error"
    assert "claim_001" in result["missing_required_claim_ids"]


def test_audit_flags_source_ids_outside_claim_slice(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    composer.build_plan(run_dir)
    write_section_outputs(run_dir, source_ids=["src_999"])

    result = composer.audit(run_dir)

    assert result["status"] == "error"
    assert any("source_ids outside claim slice" in err for err in result["errors"])


def test_audit_flags_mixed_or_numeric_citation_styles(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    composer.build_plan(run_dir)
    write_section_outputs(run_dir, citation="[1](https://example.com/cardano)")

    result = composer.audit(run_dir)

    assert result["status"] == "error"
    assert any("numeric" in err for err in result["errors"])


def test_audit_flags_invented_external_url_in_section_output(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    composer.build_plan(run_dir)
    write_section_outputs(run_dir, citation="[Invented](https://evil.example)")

    result = composer.audit(run_dir)

    assert result["status"] == "error"
    assert any("unknown source URL" in err for err in result["errors"])


def test_audit_validates_report_urls_against_union_of_section_slices(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    write_json(
        run_dir / "synthesis" / "section_briefs" / "wallets.json",
        {
            "section_id": "wallets",
            "title": "Wallets",
            "summary": "Explains wallets.",
            "must_include_claim_ids": ["claim_002"],
            "optional_claim_ids": [],
            "boundary_rules": ["claim_002 is primary to wallets."],
        },
    )
    write_json(
        run_dir / "synthesis" / "claim_slices" / "wallets.json",
        {
            "section_id": "wallets",
            "section_brief_path": "synthesis/section_briefs/wallets.json",
            "claims": [
                {
                    "id": "claim_002",
                    "text": "Lace is a Cardano wallet.",
                    "content_hash": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                    "primary_section_id": "wallets",
                    "source_ids": ["src_002"],
                    "confidence": "high",
                    "salience": "medium",
                    "include_in_report": True,
                }
            ],
            "sources": [
                {
                    "source_id": "src_002",
                    "title": "Lace Docs",
                    "url": "https://example.com/lace",
                    "tier": 1,
                }
            ],
            "boundary_rules": ["claim_002 is primary to wallets."],
        },
    )
    composer.build_plan(run_dir)
    write_section_outputs(run_dir)
    write_text(
        run_dir / "output" / "sections" / "wallets.md",
        "## Wallets\n\nLace is a Cardano wallet. [Lace Docs](https://example.com/lace)\n",
    )
    write_json(
        run_dir / "output" / "sections" / "wallets.meta.json",
        {
            "section_id": "wallets",
            "title": "Wallets",
            "claim_ids_used": ["claim_002"],
            "source_ids_used": ["src_002"],
            "word_count": 7,
            "cross_links": [],
            "warnings": [],
        },
    )
    write_text(
        run_dir / "output" / "report.md",
        "\n".join(
            [
                "# Cardano Research",
                "",
                "## Table of Contents",
                "- [Consensus Mechanism](#consensus-mechanism)",
                "- [Wallets](#wallets)",
                "",
                "Allowed source from another slice: [Lace Docs](https://example.com/lace).",
                "Invented source: [Invented](https://evil.example).",
                "",
            ]
        ),
    )

    result = composer.audit(run_dir)

    assert result["status"] == "error"
    assert any("output/report.md cites unknown source URL" in err for err in result["errors"])
    assert not any("#consensus-mechanism" in err for err in result["errors"])
    assert not any("https://example.com/lace" in err for err in result["errors"])


def test_assemble_writes_report_md_from_section_files_and_metadata(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    composer.build_plan(run_dir)
    write_section_outputs(run_dir)

    report_path = composer.assemble(run_dir)

    assert report_path == run_dir / "output" / "report.md"
    assert "## Consensus Mechanism" in report_path.read_text()
    assert "- [Cardano Docs](https://example.com/cardano)" in report_path.read_text()


def test_assembled_report_internal_anchors_do_not_require_source_metadata(tmp_path):
    composer = load_module(COMPOSER_SCRIPT, "report_composer")
    run_dir = make_run(tmp_path)
    composer.build_plan(run_dir)
    write_section_outputs(run_dir)

    composer.assemble(run_dir)
    result = composer.audit(run_dir)

    assert result["status"] == "pass"


def test_publishing_can_be_skipped_while_preserving_report_md(tmp_path):
    run_dir = make_run(tmp_path)
    write_text(run_dir / "output" / "report.md", "# Report\n")

    result = subprocess.run(
        ["bash", str(PUBLISH_SCRIPT), "--run-dir", str(run_dir), "--quarto-output", "none", "--produce-qmd", "false"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "QMD_STATUS=skip" in result.stdout
    assert (run_dir / "output" / "report.md").read_text() == "# Report\n"
    assert not (run_dir / "output" / "report.qmd").exists()


def test_make_qmd_creates_qmd_from_report_md_not_formatter_output(tmp_path):
    make_qmd = load_module(MAKE_QMD_SCRIPT, "make_qmd")
    run_dir = make_run(tmp_path)
    write_text(run_dir / "output" / "report.md", "# Report\n\nCanonical markdown.\n")

    qmd_path = make_qmd.make_qmd(run_dir)

    assert qmd_path == run_dir / "output" / "report.qmd"
    qmd = qmd_path.read_text()
    assert qmd.startswith("---")
    assert "Canonical markdown." in qmd
