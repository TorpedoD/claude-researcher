#!/usr/bin/env python3
"""
paragraph_ceiling.py — Optional mechanical check for HIER-04 (≤5 sentences/paragraph).

Usage:
    python3 paragraph_ceiling.py --input <report.md> [--max-sentences 5]

Exit codes:
    0 — all paragraphs within ceiling
    1 — violations found (advisory; formatter may invoke when Opus deems useful)
"""

import re
import sys
from pathlib import Path


def parse_args():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--max-sentences", type=int, default=5)
    return p.parse_args()


def count_sentences(text: str) -> int:
    """Approximate sentence count by terminal punctuation."""
    return len(re.findall(r'[.!?]+(?:\s|$)', text))


def main():
    args = parse_args()
    path = Path(args.input)
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    paragraphs = re.split(r'\n{2,}', text)

    violations = []
    for i, para in enumerate(paragraphs):
        stripped = para.strip()
        # Skip headings, code blocks, tables, blockquotes, list items
        if (stripped.startswith('#') or stripped.startswith('```') or
                stripped.startswith('|') or stripped.startswith('>') or
                stripped.startswith('-') or stripped.startswith('*') or
                re.match(r'^\d+\.', stripped)):
            continue
        count = count_sentences(stripped)
        if count > args.max_sentences:
            violations.append((i + 1, count, stripped[:80]))

    if violations:
        print(f"HIER-04: {len(violations)} paragraph(s) exceed {args.max_sentences} sentences:")
        for idx, count, preview in violations[:10]:
            print(f"  Para ~{idx}: {count} sentences — {preview!r}")
        sys.exit(1)

    print(f"paragraph_ceiling: OK — all paragraphs ≤{args.max_sentences} sentences")
    sys.exit(0)


if __name__ == "__main__":
    main()
