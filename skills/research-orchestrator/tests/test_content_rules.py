"""Tests for check_content_rules.py — TDD suite for Phase 11 Plan 01.

Covers: HIER-04, RULE-02, CONS-01, CONS-02, fence isolation, path security.
"""
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path.home() / ".claude/skills/research-orchestrator/scripts/check_content_rules.py"
FIXTURES = Path(__file__).parent / "fixtures"


def run(md_path):
    """Run check_content_rules.py against md_path.

    Returns CompletedProcess. If SCRIPT does not exist, raises AssertionError
    with a clear Task 2 message so tests fail cleanly in RED phase.
    """
    assert SCRIPT.exists(), (
        "check_content_rules.py not yet implemented — Task 2 will create it."
    )
    return subprocess.run(
        ["python3", str(SCRIPT), str(md_path)],
        capture_output=True,
        text=True,
    )


def parse(result):
    """Parse stdout JSON from a CompletedProcess."""
    return json.loads(result.stdout)


def test_clean_passes():
    """clean_report.md must exit 0 with status pass and no violations."""
    result = run(FIXTURES / "clean_report.md")
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr={result.stderr!r}"
    payload = parse(result)
    assert payload["status"] == "pass"
    assert payload["violations"] == []


def test_bare_fence():
    """violations.md bare ``` fence triggers HIER-04."""
    result = run(FIXTURES / "violations.md")
    assert result.returncode == 1, f"Expected exit 1, got {result.returncode}"
    payload = parse(result)
    assert any(v["rule"] == "HIER-04" for v in payload["violations"]), (
        f"No HIER-04 violation found in {payload['violations']}"
    )


def test_url_cap():
    """violations.md same URL cited 4x in one section triggers RULE-02."""
    result = run(FIXTURES / "violations.md")
    assert result.returncode == 1
    payload = parse(result)
    rule02_violations = [v for v in payload["violations"] if v["rule"] == "RULE-02"]
    assert rule02_violations, f"No RULE-02 violations found in {payload['violations']}"
    # At least one violation must mention the URL and the count
    found = any(
        "https://example.com/x" in v["detail"] and "4" in v["detail"]
        for v in rule02_violations
    )
    assert found, f"RULE-02 violation detail should contain URL and count '4x': {rule02_violations}"


def test_empty_section():
    """violations.md ## heading immediately followed by ## heading triggers CONS-01."""
    result = run(FIXTURES / "violations.md")
    assert result.returncode == 1
    payload = parse(result)
    assert any(v["rule"] == "CONS-01" for v in payload["violations"]), (
        f"No CONS-01 violation found in {payload['violations']}"
    )


def test_min_sentences():
    """violations.md section with only one sentence triggers CONS-02 with '<2 sentences' detail."""
    result = run(FIXTURES / "violations.md")
    assert result.returncode == 1
    payload = parse(result)
    cons02_warn = [
        v for v in payload["violations"]
        if v["rule"] == "CONS-02" and "<2 sentences" in v["detail"]
    ]
    assert cons02_warn, (
        f"No CONS-02 '<2 sentences' violation found. Violations: {payload['violations']}"
    )


def test_800_word_warn():
    """violations.md 810-word section triggers CONS-02 severity info with '800' in detail."""
    result = run(FIXTURES / "violations.md")
    assert result.returncode == 1
    payload = parse(result)
    cons02_info = [
        v for v in payload["violations"]
        if v["rule"] == "CONS-02" and v.get("severity") == "info" and "800" in v["detail"]
    ]
    assert cons02_info, (
        f"No CONS-02 info/800-word violation found. Violations: {payload['violations']}"
    )


def test_fence_isolation():
    """fence_isolation.md content inside fenced block must not trigger any violations."""
    result = run(FIXTURES / "fence_isolation.md")
    assert result.returncode == 0, (
        f"Expected exit 0 (no violations). Got {result.returncode}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    payload = parse(result)
    assert payload["violations"] == [], (
        f"Expected 0 violations for fence isolation, got: {payload['violations']}"
    )


def test_path_traversal():
    """Path with .. component must exit 2 with error status mentioning 'path'."""
    result = run(Path("../etc/passwd"))
    assert result.returncode == 2, f"Expected exit 2 for path traversal, got {result.returncode}"
    payload = parse(result)
    assert payload["status"] == "error"
    # Error detail must contain the word "path"
    detail = payload.get("detail", "") + payload.get("file", "")
    assert "path" in detail.lower(), (
        f"Expected 'path' in error detail, got: {payload}"
    )


def test_missing_file():
    """Nonexistent file path must exit 2."""
    result = run(Path("/nonexistent/path/to/file_that_does_not_exist.md"))
    assert result.returncode == 2, f"Expected exit 2 for missing file, got {result.returncode}"
    payload = parse(result)
    assert payload["status"] == "error"


def test_merm01_over_limit():
    """merm01_over.md has 16 nodes declared — MERM-01 warn."""
    result = run(FIXTURES / "merm01_over.md")
    assert result.returncode == 1, f"Expected exit 1, got {result.returncode}. stderr={result.stderr!r}"
    payload = parse(result)
    merm_violations = [v for v in payload["violations"] if v["rule"] == "MERM-01"]
    over_limit = [v for v in merm_violations if "16" in v["detail"]]
    assert over_limit, f"No MERM-01 over-limit violation found in {merm_violations}"
    assert all(v["severity"] == "warn" for v in over_limit), (
        f"MERM-01 must be severity=warn, got {[v['severity'] for v in over_limit]}"
    )


def test_merm01_at_limit():
    """merm01_at_limit.md has 15 nodes (boundary) — no MERM-01 violation."""
    result = run(FIXTURES / "merm01_at_limit.md")
    payload = parse(result)
    merm_violations = [v for v in payload["violations"] if v["rule"] == "MERM-01"]
    assert not merm_violations, f"Expected no MERM-01 at boundary (15 nodes), got {merm_violations}"


def test_merm01_missing_comment():
    """merm01_over.md second mermaid block has no preceding comment — MERM-01 warn."""
    result = run(FIXTURES / "merm01_over.md")
    payload = parse(result)
    merm_violations = [v for v in payload["violations"] if v["rule"] == "MERM-01"]
    missing = [v for v in merm_violations if "missing" in v["detail"].lower() or "no node-count" in v["detail"].lower()]
    assert missing, f"No MERM-01 missing-comment violation found in {merm_violations}"


def test_rule02_section_refs_excluded():
    """URL [1] appears 2x inline + 1x in Section References — total 3 raw, but exemption means inline count is 2, below cap."""
    result = run(FIXTURES / "rule02_section_refs.md")
    payload = parse(result)
    rule02 = [v for v in payload["violations"] if v["rule"] == "RULE-02"]
    # [1] appears 2x inline and once in refs — must NOT be flagged
    rule02_for_one = [v for v in rule02 if "example.com/one" in v["detail"]]
    assert not rule02_for_one, (
        f"URL [1] appears only 2x inline; Section References must be exempt. "
        f"Got RULE-02 violation: {rule02_for_one}"
    )


def test_rule02_inline_cap_still_enforced():
    """URL [2] appears 4x inline (exceeds cap=3) — must still be flagged."""
    result = run(FIXTURES / "rule02_section_refs.md")
    assert result.returncode == 1
    payload = parse(result)
    rule02 = [v for v in payload["violations"] if v["rule"] == "RULE-02"]
    rule02_for_two = [v for v in rule02 if "example.com/two" in v["detail"]]
    assert rule02_for_two, (
        f"URL [2] cited 4x inline should trigger RULE-02. Got violations: {rule02}"
    )
