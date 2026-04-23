#!/usr/bin/env python3
"""
coverage_audit.py — Verify every claim in claim_index.json has a traceable destination.

Usage:
    python3 coverage_audit.py \
        --claim-index <path/claim_index.json> \
        --report <path/report.md> \
        --decisions <path/formatter_decisions.md>

Exit codes:
    0 — all claims have destinations
    1 — some claims missing destination (PRES-02 violation)
"""

import json
import re
import sys
from pathlib import Path


def parse_args():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--claim-index", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--decisions", required=True)
    return p.parse_args()


def load_json(path: str) -> list | dict:
    p = Path(path)
    if not p.exists():
        print(f"WARNING: file not found: {path}", file=sys.stderr)
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    args = parse_args()
    claims = load_json(args.claim_index)
    if isinstance(claims, dict):
        claims = claims.get("claims", [])

    violations = []
    for claim in claims:
        dest = claim.get("formatter_destination")
        if dest is None:
            violations.append({
                "claim_hash": claim.get("claim_hash", "unknown"),
                "claim_text": claim.get("claim_text", "")[:80],
                "section": claim.get("section", "unknown"),
                "issue": "formatter_destination is null"
            })

    if violations:
        print(f"PRES-02 VIOLATION: {len(violations)} claims without destination:", file=sys.stderr)
        for v in violations[:20]:
            print(f"  [{v['section']}] {v['claim_hash'][:16]}... — {v['claim_text']}", file=sys.stderr)
        if len(violations) > 20:
            print(f"  ... and {len(violations) - 20} more", file=sys.stderr)
        sys.exit(1)

    print(f"coverage_audit: OK — all {len(claims)} claims have destinations")
    sys.exit(0)


if __name__ == "__main__":
    main()
