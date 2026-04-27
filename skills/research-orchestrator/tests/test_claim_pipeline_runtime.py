"""Runtime invariant tests for Slice 2 claim pipeline helpers."""
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "research-synthesize" / "scripts" / "claim_pipeline.py"


def load_claim_pipeline():
    spec = importlib.util.spec_from_file_location("claim_pipeline", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def make_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run-001"
    write_json(
        run_dir / "scope" / "plan.json",
        {
            "subtopics": [
                {"name": "Consensus Mechanism", "priority": 1},
                {"name": "Security Model", "priority": 2},
            ],
            "priorities": ["Consensus Mechanism", "Security Model"],
            "expected_source_types": ["docs"],
            "estimated_coverage_areas": ["consensus", "security"],
            "section_depths": [
                {"section": "Consensus Mechanism", "depth": "high"},
                {"section": "Security Model", "depth": "medium"},
            ],
        },
    )
    write_json(
        run_dir / "collect" / "inventory.json",
        {
            "sources": [
                {
                    "url": "https://example.com/consensus",
                    "source_title": "Consensus Docs",
                    "source_type": "web",
                    "content_type": "docs",
                    "source_tier": 1,
                    "freshness": {"publication_date": "2026-01-01", "freshness_score": 0.9},
                    "fetched_at": "2026-04-27T00:00:00Z",
                    "extraction_method": "crawl4ai",
                    "content_hash": "abc",
                    "evidence_file": "evidence/consensus.md",
                },
                {
                    "url": "https://example.com/security",
                    "source_title": "Security Docs",
                    "source_type": "web",
                    "content_type": "docs",
                    "source_tier": 2,
                    "freshness": {"publication_date": "2026-01-01", "freshness_score": 0.9},
                    "fetched_at": "2026-04-27T00:00:00Z",
                    "extraction_method": "crawl4ai",
                    "content_hash": "def",
                    "evidence_file": "evidence/security.md",
                },
            ]
        },
    )
    (run_dir / "collect" / "evidence").mkdir(parents=True)
    return run_dir


def test_stable_ids_persist_across_registry_reruns(tmp_path):
    claim_pipeline = load_claim_pipeline()
    run_dir = make_run(tmp_path)

    first = claim_pipeline.init_registry(run_dir)
    second = claim_pipeline.init_registry(run_dir)

    assert first == second
    assert second["source_ids"]["https://example.com/consensus"] == "src_001"
    assert second["section_ids"]["consensus mechanism"] == "consensus-mechanism"


def test_batch_claim_deltas_merge_and_dedupe_by_content_hash(tmp_path):
    claim_pipeline = load_claim_pipeline()
    run_dir = make_run(tmp_path)
    registry = claim_pipeline.init_registry(run_dir)
    consensus_id = registry["section_ids"]["consensus mechanism"]

    write_json(
        run_dir / "synthesis" / "claim_deltas" / "batch-001.json",
        {
            "claims": [
                {
                    "text": "The protocol uses stake-weighted leader selection.",
                    "primary_section_id": consensus_id,
                    "source_ids": ["src_001"],
                    "confidence": "high",
                    "salience": "high",
                    "include_in_report": True,
                    "entities": ["leader selection", "staking"],
                }
            ]
        },
    )
    write_json(
        run_dir / "synthesis" / "claim_deltas" / "batch-002.json",
        {
            "claims": [
                {
                    "text": "The protocol uses stake-weighted leader selection.",
                    "primary_section_id": consensus_id,
                    "source_ids": ["src_002"],
                    "confidence": "high",
                    "salience": "high",
                    "include_in_report": True,
                    "entities": ["staking"],
                }
            ]
        },
    )

    claim_bank = claim_pipeline.merge_claim_deltas(run_dir)

    assert claim_bank["metadata"]["total_claims"] == 1
    assert not (run_dir / "synthesis" / "claim_index.json").exists()
    claim = claim_bank["claims"][0]
    assert claim["id"] == "claim_001"
    assert claim["primary_section_id"] == consensus_id
    assert claim["source_ids"] == ["src_001", "src_002"]


def test_gate3_readiness_fails_section_without_claims_or_missing_reason(tmp_path):
    claim_pipeline = load_claim_pipeline()
    run_dir = make_run(tmp_path)
    registry = claim_pipeline.init_registry(run_dir)
    consensus_id = registry["section_ids"]["consensus mechanism"]

    write_json(
        run_dir / "synthesis" / "claim_deltas" / "batch-001.json",
        {
            "claims": [
                {
                    "text": "The protocol uses stake-weighted leader selection.",
                    "primary_section_id": consensus_id,
                    "source_ids": ["src_001"],
                    "confidence": "high",
                    "salience": "high",
                    "include_in_report": True,
                }
            ]
        },
    )
    claim_pipeline.merge_claim_deltas(run_dir)
    claim_pipeline.build_entity_index(run_dir)
    claim_pipeline.build_graph_artifacts(run_dir)
    claim_pipeline.build_section_artifacts(run_dir)

    result = claim_pipeline.validate_readiness(run_dir)
    claim_slice = json.loads(
        (run_dir / "synthesis" / "claim_slices" / f"{consensus_id}.json").read_text()
    )

    assert result["status"] == "fail"
    assert "required_claims" in claim_slice
    assert "optional_claims" in claim_slice
    assert "source_records" in claim_slice
    assert "claims" not in claim_slice
    assert "content_hash" not in claim_slice["required_claims"][0]
    assert any("no claims and no explicit missing evidence reason" in e for e in result["errors"])


def test_gate3_readiness_passes_when_empty_section_has_missing_reason(tmp_path):
    claim_pipeline = load_claim_pipeline()
    run_dir = make_run(tmp_path)
    registry = claim_pipeline.init_registry(run_dir)
    consensus_id = registry["section_ids"]["consensus mechanism"]
    security_id = registry["section_ids"]["security model"]

    write_json(
        run_dir / "synthesis" / "section_briefs" / f"{security_id}.json",
        {
            "section_id": security_id,
            "title": "Security Model",
            "summary": "Security evidence was not found.",
            "must_include_claim_ids": [],
            "optional_claim_ids": [],
            "missing": ["No strong source found for the planned security model section."],
            "boundary_rules": ["Do not invent missing evidence."],
        },
    )
    write_json(
        run_dir / "synthesis" / "claim_deltas" / "batch-001.json",
        {
            "claims": [
                {
                    "text": "The protocol uses stake-weighted leader selection.",
                    "primary_section_id": consensus_id,
                    "source_ids": ["src_001"],
                    "confidence": "high",
                    "salience": "high",
                    "include_in_report": True,
                }
            ]
        },
    )
    claim_pipeline.merge_claim_deltas(run_dir)
    entity_index = claim_pipeline.build_entity_index(run_dir)
    claim_pipeline.build_graph_artifacts(run_dir)
    claim_pipeline.build_section_artifacts(run_dir)

    result = claim_pipeline.validate_readiness(run_dir)

    assert result == {"status": "pass", "errors": [], "warnings": []}
    assert entity_index["metadata"]["schema_version"] == "entity_index.v1"
    assert not (run_dir / "synthesis" / "raw_research.md").exists()
    assert not (run_dir / "synthesis" / "claim_index.json").exists()


def test_graph_hints_cannot_reference_unplanned_sections(tmp_path):
    claim_pipeline = load_claim_pipeline()
    run_dir = make_run(tmp_path)
    registry = claim_pipeline.init_registry(run_dir)
    consensus_id = registry["section_ids"]["consensus mechanism"]

    write_json(
        run_dir / "synthesis" / "claim_deltas" / "batch-001.json",
        {
            "claims": [
                {
                    "text": "The protocol uses stake-weighted leader selection.",
                    "primary_section_id": consensus_id,
                    "source_ids": ["src_001"],
                    "confidence": "high",
                    "salience": "high",
                    "include_in_report": True,
                }
            ]
        },
    )
    claim_pipeline.merge_claim_deltas(run_dir)
    claim_pipeline.build_entity_index(run_dir)
    claim_pipeline.build_graph_artifacts(run_dir)
    claim_pipeline.build_section_artifacts(run_dir)
    hints = json.loads((run_dir / "synthesis" / "section_graph_hints.json").read_text())
    hints["sections"][0]["related_sections"] = ["invented-section"]
    write_json(run_dir / "synthesis" / "section_graph_hints.json", hints)

    result = claim_pipeline.validate_readiness(run_dir)

    assert result["status"] == "fail"
    assert any("unplanned sections" in e for e in result["errors"])


def test_graph_artifacts_do_not_read_raw_evidence_default_path(tmp_path, monkeypatch):
    claim_pipeline = load_claim_pipeline()
    run_dir = make_run(tmp_path)
    registry = claim_pipeline.init_registry(run_dir)
    consensus_id = registry["section_ids"]["consensus mechanism"]

    write_json(
        run_dir / "synthesis" / "claim_deltas" / "batch-001.json",
        {
            "claims": [
                {
                    "text": "The protocol uses stake-weighted leader selection.",
                    "primary_section_id": consensus_id,
                    "source_ids": ["src_001"],
                    "confidence": "high",
                    "salience": "high",
                    "include_in_report": True,
                    "entities": ["staking"],
                }
            ]
        },
    )
    claim_pipeline.merge_claim_deltas(run_dir)
    claim_pipeline.build_entity_index(run_dir)
    evidence_path = run_dir / "collect" / "evidence" / "poison.md"
    evidence_path.write_text("Graph construction must not read this file.")

    original_read_text = Path.read_text

    def guarded_read_text(self, *args, **kwargs):
        if self == evidence_path:
            raise AssertionError("graph builder read raw evidence")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    claim_graph_map, section_graph_hints = claim_pipeline.build_graph_artifacts(run_dir)

    assert claim_graph_map["claims"][0]["entities"] == ["staking"]
    assert section_graph_hints["planned_section_ids"]


def test_gate3_readiness_fails_schema_invalid_artifact(tmp_path):
    claim_pipeline = load_claim_pipeline()
    run_dir = make_run(tmp_path)
    registry = claim_pipeline.init_registry(run_dir)
    consensus_id = registry["section_ids"]["consensus mechanism"]
    security_id = registry["section_ids"]["security model"]

    write_json(
        run_dir / "synthesis" / "section_briefs" / f"{security_id}.json",
        {
            "section_id": security_id,
            "title": "Security Model",
            "summary": "Security evidence was not found.",
            "must_include_claim_ids": [],
            "optional_claim_ids": [],
            "missing": ["No strong source found."],
            "boundary_rules": ["Do not invent missing evidence."],
        },
    )
    write_json(
        run_dir / "synthesis" / "claim_deltas" / "batch-001.json",
        {
            "claims": [
                {
                    "text": "The protocol uses stake-weighted leader selection.",
                    "primary_section_id": consensus_id,
                    "source_ids": ["src_001"],
                    "confidence": "high",
                    "salience": "high",
                    "include_in_report": True,
                }
            ]
        },
    )
    claim_pipeline.merge_claim_deltas(run_dir)
    claim_pipeline.build_entity_index(run_dir)
    claim_pipeline.build_graph_artifacts(run_dir)
    claim_pipeline.build_section_artifacts(run_dir)

    claim_bank = json.loads((run_dir / "synthesis" / "claim_bank.json").read_text())
    del claim_bank["metadata"]["schema_version"]
    write_json(run_dir / "synthesis" / "claim_bank.json", claim_bank)

    result = claim_pipeline.validate_readiness(run_dir)

    assert result["status"] == "fail"
    assert any("claim_bank.json schema error" in e for e in result["errors"])
