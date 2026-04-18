#!/usr/bin/env python3
"""
Parse the gap_analysis.md trigger table and decide whether gap-fill is needed.

Reads synthesis/gap_analysis.md and manifest.json from the run directory,
checks the Gap-Fill Trigger Table, and exits with a printed decision token
for the synthesizer to log.

Usage:
    python3 gap_fill_eval.py --run-dir <path>

Output (stdout, one of):
    GAP_FILL_NEEDED: [<trigger names>]
    GAP_FILL_SKIP_CAP: [<trigger names>]
    GAP_FILL_NOT_NEEDED

Exit codes:
    0  always (decision is communicated via stdout token, not exit code)
"""
import argparse
import json
import pathlib
import re
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--run-dir", required=True, help="Path to the research run directory")
    args = parser.parse_args()

    run_dir = pathlib.Path(args.run_dir)
    gap_path = run_dir / "synthesis" / "gap_analysis.md"
    manifest_path = run_dir / "manifest.json"

    if not gap_path.exists():
        print(f"GAP_FILL_PARSE_WARN: {gap_path} not found — skipping gap-fill", file=sys.stderr)
        print("GAP_FILL_NOT_NEEDED")
        return

    if not manifest_path.exists():
        print(f"ERROR: {manifest_path} not found", file=sys.stderr)
        sys.exit(1)

    ga = gap_path.read_text()
    rows = re.findall(
        r"^\s*\|\s*(Uncovered topic categories|Isolated nodes|Low-confidence claims)\s*\|[^|\n]*\|\s*(TRIGGERED|OK|BORDERLINE)\s*\|?\s*$",
        ga, re.M | re.I,
    )
    if not rows:
        print("GAP_FILL_PARSE_WARN: 0 trigger rows found — gap_analysis.md may be missing trigger table", file=sys.stderr)

    triggered = [name for name, status in rows if status.upper() == "TRIGGERED"]
    manifest = json.loads(manifest_path.read_text())
    iter_count = manifest.get("gap_fill_iteration_count", 0)

    if triggered and iter_count < 1:
        print(f"GAP_FILL_NEEDED: {triggered}")
    elif triggered and iter_count >= 1:
        print(f"GAP_FILL_SKIP_CAP: {triggered}")
    else:
        print("GAP_FILL_NOT_NEEDED")


if __name__ == "__main__":
    main()
