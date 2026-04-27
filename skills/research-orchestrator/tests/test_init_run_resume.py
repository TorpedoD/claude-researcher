import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "research-orchestrator" / "scripts" / "init_run.py"


def load_init_run():
    spec = importlib.util.spec_from_file_location("init_run", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_manifest(root: Path, run_id: str, statuses: dict, request: str = "test request") -> Path:
    run_dir = root / "research" / run_id
    run_dir.mkdir(parents=True)
    phase_status = {
        phase: {"status": status, "started_at": None, "completed_at": None}
        for phase, status in statuses.items()
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "created_at": "2026-04-27T00:00:00+00:00",
                "user_request": request,
                "validation_mode": "normal",
                "phase_status": phase_status,
            },
            indent=2,
        )
        + "\n"
    )
    return run_dir


def run_init(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


def test_update_phase_status_allows_running_to_running_resume_reentry(tmp_path):
    init_run = load_init_run()
    run_dir = write_manifest(
        tmp_path,
        "run-001-20260427T000000",
        {"planning": "running"},
    )
    manifest_path = run_dir / "manifest.json"
    before = json.loads(manifest_path.read_text())

    after = init_run.update_phase_status(manifest_path, "planning", "running")

    assert after == before
    assert json.loads(manifest_path.read_text()) == before


def test_find_interrupted_runs_returns_only_running_or_failed(tmp_path):
    init_run = load_init_run()
    write_manifest(tmp_path, "run-001-20260427T000000", {"planning": "complete"})
    write_manifest(tmp_path, "run-002-20260427T000001", {"planning": "failed"})
    write_manifest(tmp_path, "run-003-20260427T000002", {"planning": "running"})

    interrupted = init_run.find_interrupted_runs(tmp_path / "research")

    assert [run["run_id"] for run in interrupted] == [
        "run-002-20260427T000001",
        "run-003-20260427T000002",
    ]


def test_list_interrupted_cli_reports_zero_runs(tmp_path):
    result = run_init(tmp_path, "--list-interrupted")

    assert result.returncode == 0
    assert "No interrupted runs found." in result.stdout


def test_no_arg_cli_reports_zero_runs_without_error(tmp_path):
    result = run_init(tmp_path)

    assert result.returncode == 0
    assert "No interrupted runs found." in result.stdout
    assert "Start a new research run with /research <topic>" in result.stdout


def test_no_arg_cli_reports_interrupted_runs(tmp_path):
    write_manifest(
        tmp_path,
        "run-001-20260427T000000",
        {"planning": "running"},
        request="interrupted research topic",
    )

    result = run_init(tmp_path)

    assert result.returncode == 0
    assert "1 interrupted run(s) found" in result.stdout
    assert "run-001-20260427T000000" in result.stdout
    assert "Use --resume RUN_ID to continue, or provide a new request." in result.stdout


def test_list_interrupted_cli_reports_interrupted_runs(tmp_path):
    write_manifest(
        tmp_path,
        "run-001-20260427T000000",
        {"planning": "complete", "collection": "failed"},
        request="enterprise retrieval research",
    )

    result = run_init(tmp_path, "--list-interrupted")

    assert result.returncode == 0
    assert "1 interrupted run(s) found" in result.stdout
    assert "run-001-20260427T000000" in result.stdout
    assert "collection (failed)" in result.stdout
    assert "enterprise retrieval research" in result.stdout


def test_resume_cli_reports_resume_metadata(tmp_path):
    write_manifest(
        tmp_path,
        "run-001-20260427T000000",
        {
            "planning": "complete",
            "collection": "failed",
            "claim_extraction": "pending",
        },
    )

    result = run_init(tmp_path, "--resume", "run-001-20260427T000000")

    assert result.returncode == 0
    assert "Resume run: run-001-20260427T000000" in result.stdout
    assert "Problem phases: collection (failed)" in result.stdout
    assert "Completed phases: planning" in result.stdout
    assert "Last phase: collection" in result.stdout
    assert "Next phase: collection" in result.stdout
    assert "Required artifacts:" in result.stdout


def test_resume_cli_json_reports_artifact_status(tmp_path):
    run_dir = write_manifest(
        tmp_path,
        "run-001-20260427T000000",
        {
            "planning": "complete",
            "collection": "complete",
            "claim_extraction": "failed",
        },
    )
    collect = run_dir / "collect"
    collect.mkdir()
    (collect / "inventory.json").write_text('{"sources": []}\n')

    result = run_init(tmp_path, "--resume", "run-001-20260427T000000", "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["run_id"] == "run-001-20260427T000000"
    assert payload["run_mode"] == "resume"
    assert payload["next_phase"] == "claim_extraction"
    assert payload["required_artifacts"] == ["collect/inventory.json", "collect/evidence"]
    assert payload["artifact_status"]["collect/inventory.json"] == "valid"
    assert payload["artifact_status"]["collect/evidence"] == "missing"
    assert payload["recommended_command"] == "/research --resume run-001-20260427T000000"
    assert payload["dispatch"] == "run synthesizer claim extraction"


def test_resume_cli_fails_for_complete_run(tmp_path):
    write_manifest(
        tmp_path,
        "run-001-20260427T000000",
        {"planning": "complete", "collection": "complete"},
    )

    result = run_init(tmp_path, "--resume", "run-001-20260427T000000")

    assert result.returncode == 1
    assert "Run is not interrupted" in result.stderr


def test_resume_cli_fails_for_unknown_run(tmp_path):
    result = run_init(tmp_path, "--resume", "run-404")

    assert result.returncode == 1
    assert "Run not found: run-404" in result.stderr


def test_budget_shorthand_creates_manifest_with_overrides(tmp_path):
    result = run_init(
        tmp_path,
        "--50,10,2",
        "budget shorthand topic",
        "--collection-mode",
        "metadata_only",
    )

    assert result.returncode == 0
    run_dir = next((tmp_path / "research").glob("run-*"))
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["user_request"] == "budget shorthand topic"
    assert manifest["budget_config"]["max_pages"] == 50
    assert manifest["budget_config"]["max_per_domain"] == 10
    assert manifest["budget_config"]["max_depth"] == 2
    assert manifest["run_mode"] == "normal"
    assert manifest["collection_mode"] == "metadata_only"
    assert manifest["validation_mode"] == "normal"
    assert manifest["source_channels"] == {"web": False, "documents": False}


def test_budget_shorthand_rejects_missing_component(tmp_path):
    result = run_init(
        tmp_path,
        "--50,10",
        "budget shorthand topic",
    )

    assert result.returncode == 2
    assert "unrecognized arguments: --50,10" in result.stderr


def test_budget_shorthand_rejects_non_integer_component(tmp_path):
    result = run_init(
        tmp_path,
        "--50,x,2",
        "budget shorthand topic",
    )

    assert result.returncode == 2
    assert "invalid int value: 'x'" in result.stderr


def test_budget_shorthand_rejects_non_positive_component(tmp_path):
    result = run_init(
        tmp_path,
        "--0,10,2",
        "budget shorthand topic",
        "--collection-mode",
        "metadata_only",
    )

    assert result.returncode == 1
    assert "Error: --max-pages must be a positive integer, got 0" in result.stderr


def test_long_form_budget_overrides_still_create_manifest(tmp_path):
    result = run_init(
        tmp_path,
        "long form budget topic",
        "--max-pages",
        "60",
        "--max-per-domain",
        "12",
        "--max-depth",
        "4",
        "--collection-mode",
        "metadata_only",
        "--validation-mode",
        "strict",
    )

    assert result.returncode == 0
    run_dir = next((tmp_path / "research").glob("run-*"))
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["user_request"] == "long form budget topic"
    assert manifest["budget_config"]["max_pages"] == 60
    assert manifest["budget_config"]["max_per_domain"] == 12
    assert manifest["budget_config"]["max_depth"] == 4
    assert manifest["validation_mode"] == "strict"


def test_collection_mode_auto_resolves_from_source_channels():
    init_run = load_init_run()

    assert init_run.resolve_collection_mode({"web": True, "documents": True}, "auto") == "web_and_docs"
    assert init_run.resolve_collection_mode({"web": False, "documents": True}, "auto") == "docs_only"
    assert init_run.resolve_collection_mode({"web": True, "documents": False}, "auto") == "web_only"
    assert init_run.resolve_collection_mode({"web": False, "documents": False}, "auto") == "metadata_only"
    assert init_run.resolve_collection_mode({"web": False, "documents": False}, "none") == "metadata_only"


def test_missing_dependencies_follow_collection_mode():
    init_run = load_init_run()
    no_tools = {}

    assert [name for name, _ in init_run.missing_dependencies("web_and_docs", no_tools)] == [
        "crawl4ai",
        "playwright chromium runtime",
        "docling",
    ]
    assert [name for name, _ in init_run.missing_dependencies("docs_only", no_tools)] == ["docling"]
    assert [name for name, _ in init_run.missing_dependencies("web_only", no_tools)] == [
        "crawl4ai",
        "playwright chromium runtime",
    ]
    assert init_run.missing_dependencies("metadata_only", no_tools) == []


def test_collection_mode_metadata_only_requires_no_extraction_tools(tmp_path):
    result = run_init(tmp_path, "metadata-only topic", "--collection-mode", "metadata_only")

    assert result.returncode == 0
    run_dir = next((tmp_path / "research").glob("run-*"))
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["collection_mode"] == "metadata_only"
    assert manifest["source_channels"] == {"web": False, "documents": False}


def test_collection_mode_legacy_alias_persists_metadata_only(tmp_path):
    result = run_init(tmp_path, "metadata-only topic", "--collection-mode", "none")

    assert result.returncode == 0
    run_dir = next((tmp_path / "research").glob("run-*"))
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["collection_mode"] == "metadata_only"
    assert manifest["source_channels"] == {"web": False, "documents": False}
