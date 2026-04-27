"""Contract tests for claim-based pipeline Slice 1 artifacts."""
import importlib.util
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
SYNTH_REFS = ROOT / "skills" / "research-synthesize" / "references"
FORMAT_REFS = ROOT / "skills" / "research-format" / "references"
FIXTURES = Path(__file__).parent / "fixtures" / "contracts"

CONTRACTS = {
    "global_id_registry": SYNTH_REFS / "global_id_registry.schema.json",
    "claim_bank": SYNTH_REFS / "claim_bank.schema.json",
    "entity_index": SYNTH_REFS / "entity_index.schema.json",
    "claim_slice": SYNTH_REFS / "claim_slice.schema.json",
    "section_brief": SYNTH_REFS / "section_brief.schema.json",
    "claim_graph_map": SYNTH_REFS / "claim_graph_map.schema.json",
    "section_graph_hints": SYNTH_REFS / "section_graph_hints.schema.json",
    "assembly_plan": FORMAT_REFS / "assembly_plan.schema.json",
    "section_meta": FORMAT_REFS / "section_meta.schema.json",
    "formatter_audit": FORMAT_REFS / "formatter_audit.schema.json",
}


def load_json(path: Path):
    return json.loads(path.read_text())


def validator_for(schema_path: Path):
    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_new_schemas_parse_as_valid_json_schema():
    for schema_path in CONTRACTS.values():
        validator_for(schema_path)


def test_valid_minimal_fixtures_validate():
    for name, schema_path in CONTRACTS.items():
        validator = validator_for(schema_path)
        fixture = load_json(FIXTURES / name / "valid_minimal.json")
        validator.validate(fixture)


def test_invalid_missing_required_fixtures_fail():
    for name, schema_path in CONTRACTS.items():
        validator = validator_for(schema_path)
        fixture = load_json(FIXTURES / name / "invalid_missing_required.json")
        errors = list(validator.iter_errors(fixture))
        assert errors, f"{name} invalid_missing_required.json unexpectedly passed"


def test_claim_bank_requires_canonical_claim_fields():
    schema = load_json(CONTRACTS["claim_bank"])
    required = set(schema["properties"]["claims"]["items"]["required"])
    assert {
        "id",
        "content_hash",
        "primary_section_id",
        "source_ids",
        "confidence",
        "salience",
        "include_in_report",
    }.issubset(required)


def test_claim_slice_contains_one_section_and_only_matching_claims_and_sources():
    fixture = load_json(FIXTURES / "claim_slice" / "valid_minimal.json")
    section_id = fixture["section_id"]
    claims = fixture["required_claims"] + fixture["optional_claims"]
    source_ids = {source["source_id"] for source in fixture["source_records"]}

    assert isinstance(section_id, str) and section_id
    assert all(claim["primary_section_id"] == section_id for claim in claims)
    assert all(
        set(claim["source_ids"]).issubset(source_ids)
        for claim in claims
    )


def test_section_graph_hints_cannot_introduce_unplanned_sections():
    fixture = load_json(FIXTURES / "section_graph_hints" / "valid_minimal.json")
    planned = set(fixture["planned_section_ids"])

    for section in fixture["sections"]:
        assert section["section_id"] in planned
        assert set(section.get("related_sections", [])).issubset(planned)
        assert {
            link["to"] for link in section.get("recommended_cross_links", [])
        }.issubset(planned)


def test_init_run_manifest_uses_claim_pipeline_phase_model():
    init_run_path = ROOT / "skills" / "research-orchestrator" / "scripts" / "init_run.py"
    spec = importlib.util.spec_from_file_location("init_run", init_run_path)
    init_run = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(init_run)

    manifest = init_run.create_manifest(
        "run-001-20260427T000000",
        "test request",
        {"max_pages": 1},
    )

    assert manifest["pipeline_contract_version"] == "claim_pipeline_v1"
    assert list(manifest["phase_status"]) == [
        "planning",
        "collection",
        "claim_extraction",
        "graph_relationships",
        "section_brief_synthesis",
        "formatting",
        "publishing",
    ]


def test_publishing_contract_requires_report_md_as_source_artifact():
    assembly_schema = load_json(CONTRACTS["assembly_plan"])
    audit_schema = load_json(CONTRACTS["formatter_audit"])

    assert assembly_schema["properties"]["canonical_report_path"]["const"] == "output/report.md"
    assert audit_schema["properties"]["canonical_report_path"]["const"] == "output/report.md"


def test_publishing_instructions_update_publishing_phase_status():
    orchestrator_skill = (ROOT / "skills" / "research-orchestrator" / "SKILL.md").read_text()

    assert 'm["phase_status"]["publishing"]["render_failed"] = render_failed' in orchestrator_skill
    assert "append_log(run_dir, 'publishing', 'quarto_rendered'" in orchestrator_skill
    assert 'update_phase_status(manifest_path, "publishing", "complete")' in orchestrator_skill
    assert 'm["phase_status"]["formatting"]["render_failed"] = render_failed' not in orchestrator_skill
    assert 'update_phase_status(manifest_path, "formatting", "complete")' not in orchestrator_skill
