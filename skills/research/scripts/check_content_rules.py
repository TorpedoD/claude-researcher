#!/usr/bin/env python3
"""Post-synthesis content rules scanner for research pipeline.

Checks markdown output against 5 machine-verifiable rules:
  HIER-04 — Code fences must have language annotation (bare ``` → violation)
  RULE-02 — No source URL cited more than 3 times in the same ## section
  CONS-01 — No heading without a content body (heading immediately followed by heading)
  CONS-02 — Every ## section must have ≥2 sentences; >800 words triggers info advisory
  MERM-01 — Mermaid blocks must have <!-- mermaid: N nodes --> comment with N ≤ 15 (Phase 12 D-23, D-24)

Usage:
    python3 check_content_rules.py [--target=raw|report] [--claim-index=<path>] <path-to-markdown.md>

Options:
    --target=raw     Skip CONS-02 and HIER-04 checks (raw_research.md is exempt from readability rules).
                     Runs only CONS-01, RULE-02, MERM-01.
    --target=report  Run all checks as normal (default). If --claim-index is also provided,
                     subprocess-calls coverage_audit.py to check PRES-02 claim destinations.
    --claim-index=<path>  Path to claim_index.json. Only used when --target=report.

Exit codes:
    0 = pass (no violations)
    1 = warn (≥1 violation)
    2 = error (bad input: missing file, path traversal, oversized file)

Stdout: JSON payload matching validate_artifact.py shape:
    {
        "status": "pass" | "warn" | "error",
        "file": "<path>",
        "violations": [
            {
                "rule": "HIER-04" | "RULE-02" | "CONS-01" | "CONS-02" | "MERM-01",
                "line": <int>,
                "severity": "warn" | "info",
                "detail": "<human string>"
            }
        ],
        "summary": {
            "total": <int>,
            "by_rule": {"HIER-04": N, "RULE-02": N, "CONS-01": N, "CONS-02": N, "MERM-01": N},
            "by_severity": {"warn": N, "info": N}
        }
    }

Section definition: content between one ## heading and the next ## heading.
### subsections roll UP into their parent ## for RULE-02 URL counts and CONS-02
sentence/word counts. CONS-01 applies to BOTH ## and ### headings.

Path traversal policy: literal '..' in argv[1] parts is rejected. Absolute paths
to any location on the filesystem are accepted (fixtures live outside research/).

Stdlib-only: re, json, sys, pathlib, subprocess. No third-party dependencies.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FENCE_RE = re.compile(r'^[ ]{0,3}(`{3,})(\w*)\s*$')
HEADING_RE = re.compile(r'^(#{2,4})\s+(.+?)\s*$')
LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
SENTENCE_END_RE = re.compile(r'[.!?](?:\s|$)')
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB ReDoS guard
WORD_GUIDANCE = 800
URL_CAP = 3
MERMAID_FENCE_RE = re.compile(r'^[ ]{0,3}`{3,}mermaid\s*$')
MERMAID_NODE_COMMENT_RE = re.compile(r'^<!--\s*mermaid:\s*(\d+)\s*nodes?\s*-->\s*$', re.IGNORECASE)
SECTION_REFS_HEADING_RE = re.compile(r'^###\s+Section References\s*$', re.IGNORECASE)
MERMAID_NODE_CAP = 15


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------
def scan(md_path: Path, target: str = "report") -> dict:
    """Scan a markdown file and return violations dict.

    Args:
        md_path: Path to the markdown file to scan.
        target: "raw" skips CONS-02 and HIER-04 (raw_research.md is exempt from
                readability rules). "report" runs all checks (default).

    Returns the result dict with 'status', 'file', 'violations', 'summary'.
    """
    text = md_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    violations = []

    # --- State machine ---
    in_fence = False

    # H2-level tracking (for RULE-02, CONS-02)
    current_h2_line = None          # line number (1-indexed) of current ## heading
    section_urls: dict = {}         # url -> count within current ## section
    acc_text = ""                   # accumulated body text for current ## section

    # Heading-has-body tracking (for CONS-01)
    last_heading_line = None        # line number of the most recent ## or ### heading
    last_heading_had_content = False

    # Phase 12 additions
    in_section_refs = False                 # True while inside a ### Section References block
    pending_mermaid_node_count = None       # int | None — N from <!-- mermaid: N nodes --> on prior line

    def _close_h2_section(target: str = "report"):
        """Emit CONS-02 violations for the section just completed.

        When target='raw', CONS-02 checks are skipped (raw_research.md is exempt
        from readability rules per content_rules.md CONS-02 scope annotation).
        """
        nonlocal acc_text, section_urls
        if current_h2_line is None:
            return

        if target != "raw":
            # CONS-02 min sentences
            sentence_count = len(SENTENCE_END_RE.findall(acc_text))
            if sentence_count < 2:
                violations.append({
                    "rule": "CONS-02",
                    "line": current_h2_line,
                    "severity": "warn",
                    "detail": f"Section has <2 sentences (found {sentence_count})",
                })

            # CONS-02 800-word advisory
            word_count = len(acc_text.split())
            if word_count > WORD_GUIDANCE:
                violations.append({
                    "rule": "CONS-02",
                    "line": current_h2_line,
                    "severity": "info",
                    "detail": (
                        f"Section exceeds {WORD_GUIDANCE} words ({word_count} words); "
                        "consider adding subsection splits"
                    ),
                })

        # RULE-02 URL cap (applies to both raw and report)
        for url, count in section_urls.items():
            if count > URL_CAP:
                violations.append({
                    "rule": "RULE-02",
                    "line": current_h2_line,
                    "severity": "warn",
                    "detail": (
                        f"URL cited {count}\u00d7 in section (cap={URL_CAP}): {url}"
                    ),
                })

    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip()

        # --- Check if this line is a <!-- mermaid: N nodes --> comment (before fence check) ---
        node_comment_match = MERMAID_NODE_COMMENT_RE.match(line.strip())
        if node_comment_match and not in_fence:
            pending_mermaid_node_count = int(node_comment_match.group(1))
            # Comment satisfies CONS-01 (heading has content)
            last_heading_had_content = True
            continue

        # --- Fence state ---
        fence_match = FENCE_RE.match(line)
        if fence_match:
            lang = fence_match.group(2)
            if not in_fence:
                # Opening fence
                if lang == "" and target != "raw":
                    # HIER-04: bare opening fence (skipped for raw target)
                    violations.append({
                        "rule": "HIER-04",
                        "line": i,
                        "severity": "warn",
                        "detail": "Code fence missing language annotation (bare ```)",
                    })
                elif lang.lower() == "mermaid":
                    # MERM-01: check for preceding node-count comment
                    if pending_mermaid_node_count is None:
                        violations.append({
                            "rule": "MERM-01",
                            "line": i,
                            "severity": "warn",
                            "detail": "Mermaid block missing node-count comment <!-- mermaid: N nodes -->",
                        })
                    elif pending_mermaid_node_count > MERMAID_NODE_CAP:
                        violations.append({
                            "rule": "MERM-01",
                            "line": i,
                            "severity": "warn",
                            "detail": (
                                f"Mermaid diagram declares {pending_mermaid_node_count} nodes "
                                f"(cap={MERMAID_NODE_CAP}): consider splitting"
                            ),
                        })
                    pending_mermaid_node_count = None   # consume the pending count
            # Toggle fence state (open → close or close → open)
            in_fence = not in_fence
            continue  # fence line itself is not body content

        # --- Reset pending mermaid count if non-blank non-comment non-fence line ---
        if line.strip() and not in_fence:
            pending_mermaid_node_count = None

        # --- Skip everything inside a fence ---
        if in_fence:
            continue

        # --- Heading detection ---
        heading_match = HEADING_RE.match(line)
        if heading_match:
            hashes = heading_match.group(1)
            is_h2 = len(hashes) == 2

            # CONS-01: check if previous heading had content
            if last_heading_line is not None and not last_heading_had_content:
                violations.append({
                    "rule": "CONS-01",
                    "line": last_heading_line,
                    "severity": "warn",
                    "detail": "Heading has no content body before next heading",
                })

            # Phase 12: track Section References state
            if is_h2:
                in_section_refs = False   # new ## section resets the flag
            elif len(hashes) == 3:
                in_section_refs = bool(SECTION_REFS_HEADING_RE.match(line.strip()))

            # If this is an H2, close the previous H2 section and start a new one
            if is_h2:
                _close_h2_section(target)
                # Reset section state
                section_urls = {}
                acc_text = ""
                current_h2_line = i

            # Update heading tracking for CONS-01
            last_heading_line = i
            last_heading_had_content = False
            continue

        # --- Body line (not in fence, not a heading) ---
        # Any non-blank body line satisfies CONS-01 for the preceding heading
        if line.strip():
            last_heading_had_content = True
            # Accumulate for section checks (acc_text includes refs block for word count)
            acc_text += " " + line
            # Count URLs for RULE-02 — exempt if inside ### Section References block
            if not in_section_refs:
                for _anchor, url in LINK_RE.findall(line):
                    section_urls[url] = section_urls.get(url, 0) + 1

    # End-of-file: close the last heading and last H2 section
    if last_heading_line is not None and not last_heading_had_content:
        violations.append({
            "rule": "CONS-01",
            "line": last_heading_line,
            "severity": "warn",
            "detail": "Heading has no content body (end of file)",
        })

    _close_h2_section(target)

    # Build summary
    by_rule: dict = {"HIER-04": 0, "RULE-02": 0, "CONS-01": 0, "CONS-02": 0, "MERM-01": 0}
    by_severity: dict = {"warn": 0, "info": 0}
    for v in violations:
        by_rule[v["rule"]] = by_rule.get(v["rule"], 0) + 1
        by_severity[v["severity"]] = by_severity.get(v["severity"], 0) + 1

    status = "pass" if not violations else "warn"
    return {
        "status": status,
        "file": str(md_path),
        "violations": violations,
        "summary": {
            "total": len(violations),
            "by_rule": by_rule,
            "by_severity": by_severity,
        },
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    """CLI entry point.

    Usage:
        check_content_rules.py [--target=raw|report] [--claim-index=<path>] <file.md>

    --target=raw    Skip CONS-02 and HIER-04; run only CONS-01, RULE-02, MERM-01.
    --target=report Run all checks (default, backward-compatible).
    --claim-index   Path to claim_index.json; when provided with --target=report,
                    subprocess-calls coverage_audit.py to check PRES-02.
    """
    args = sys.argv[1:]

    # Parse --target and --claim-index flags; remaining arg is the file path.
    scan_target = "report"   # default: backward-compatible
    claim_index_path = None
    positional = []

    for arg in args:
        if arg.startswith("--target="):
            val = arg.split("=", 1)[1]
            if val not in ("raw", "report"):
                print(json.dumps({
                    "status": "error",
                    "detail": f"--target must be 'raw' or 'report', got: {val!r}",
                    "file": "",
                }))
                sys.exit(2)
            scan_target = val
        elif arg.startswith("--claim-index="):
            claim_index_path = arg.split("=", 1)[1]
        else:
            positional.append(arg)

    if len(positional) != 1:
        print(json.dumps({
            "status": "error",
            "detail": "usage: check_content_rules.py [--target=raw|report] [--claim-index=<path>] <file.md>",
            "file": "",
        }))
        sys.exit(2)

    raw_arg = positional[0]
    raw_path = Path(raw_arg)

    # Reject literal '..' in the provided path parts (before resolving)
    if ".." in raw_path.parts:
        print(json.dumps({
            "status": "error",
            "detail": "path traversal rejected: '..' found in input path",
            "file": raw_arg,
        }))
        sys.exit(2)

    md_file = raw_path.expanduser().resolve()

    if not md_file.exists() or not md_file.is_file():
        print(json.dumps({
            "status": "error",
            "detail": f"file not found: {md_file}",
            "file": str(md_file),
        }))
        sys.exit(2)

    if md_file.stat().st_size > MAX_FILE_BYTES:
        print(json.dumps({
            "status": "error",
            "detail": f"file exceeds {MAX_FILE_BYTES} bytes (ReDoS guard)",
            "file": str(md_file),
        }))
        sys.exit(2)

    result = scan(md_file, target=scan_target)

    # --target=report + --claim-index: also run coverage_audit.py for PRES-02
    if scan_target == "report" and claim_index_path:
        coverage_audit = Path.home() / ".claude/skills/research-format/scripts/coverage_audit.py"
        if coverage_audit.exists():
            audit_result = subprocess.run(
                ["python3", str(coverage_audit), "--claim-index", claim_index_path],
                capture_output=True,
                text=True,
            )
            if audit_result.returncode != 0:
                # Append a PRES-02 violation summary to the result
                result["violations"].append({
                    "rule": "PRES-02",
                    "line": 0,
                    "severity": "warn",
                    "detail": f"coverage_audit.py exited {audit_result.returncode}: {audit_result.stdout[:200].strip()}",
                })
                result["summary"]["by_rule"]["PRES-02"] = result["summary"]["by_rule"].get("PRES-02", 0) + 1
                result["summary"]["by_severity"]["warn"] = result["summary"]["by_severity"].get("warn", 0) + 1
                result["summary"]["total"] = len(result["violations"])
                result["status"] = "warn"

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
