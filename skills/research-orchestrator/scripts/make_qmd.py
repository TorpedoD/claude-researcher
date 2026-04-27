#!/usr/bin/env python3
"""Create a Quarto source file from canonical output/report.md."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_manifest(run_dir: Path) -> dict:
    path = run_dir / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def make_qmd(run_dir: Path) -> Path:
    report_md = run_dir / "output" / "report.md"
    report_qmd = run_dir / "output" / "report.qmd"
    if not report_md.exists():
        raise FileNotFoundError(f"canonical report missing: {report_md}")

    manifest = load_manifest(run_dir)
    prefs = manifest.get("format_preferences", {})
    title = manifest.get("topic") or manifest.get("user_request") or "Research Report"
    header = [
        "---",
        f'title: "{str(title).replace(chr(34), chr(39))}"',
        "format:",
        "  html:",
        "    toc: true",
        "  pdf:",
        "    toc: true",
        "execute:",
        "  echo: false",
        f'audience: "{prefs.get("audience", "external")}"',
        f'tone: "{prefs.get("tone", "professional")}"',
        "---",
        "",
    ]
    report_qmd.write_text("\n".join(header) + report_md.read_text())
    return report_qmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate output/report.qmd from output/report.md")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    try:
        print(make_qmd(Path(args.run_dir)))
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
