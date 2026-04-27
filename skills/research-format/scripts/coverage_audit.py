#!/usr/bin/env python3
"""Deprecated compatibility wrapper.

New claim-pipeline runs use report_composer.py audit against section briefs,
claim slices, and section metadata. This wrapper remains so old automation fails
with a clear migration message instead of silently applying obsolete rules.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "coverage_audit.py is deprecated for claim_pipeline_v1; "
        "run report_composer.py audit instead.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
