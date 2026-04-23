#!/usr/bin/env python3
"""
density_scan.py — Advisory density hints for the research formatter.

Usage:
    python3 density_scan.py --input <raw_research.md> --output <density_hints.json>

Analyzes each ## and ### section for:
- Numeric comparisons (≥3 → table hint)
- Process steps (≥4 → flowchart hint)
- Enumerable parallel items (bullet runs ≥5 → table hint)
- Citation density
- Word count

Output: density_hints.json with per-section advisory hints and confidence levels.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional


def parse_args():
    import argparse
    p = argparse.ArgumentParser(description="Density scan for research formatter")
    p.add_argument("--input", required=True, help="Path to raw_research.md")
    p.add_argument("--output", required=True, help="Path to write density_hints.json")
    return p.parse_args()


def parse_sections(text: str) -> list[dict]:
    """Split markdown into ## sections, each with heading and body."""
    sections = []
    current_heading = None
    current_lines = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_heading is not None:
                sections.append({
                    "heading": current_heading,
                    "body": "\n".join(current_lines)
                })
            current_heading = line[3:].strip()
            current_lines = []
        else:
            if current_heading is not None:
                current_lines.append(line)

    if current_heading is not None:
        sections.append({
            "heading": current_heading,
            "body": "\n".join(current_lines)
        })

    return sections


def count_numeric_comparisons(text: str) -> int:
    """Count lines/sentences with numeric values that suggest comparison tables."""
    # Pattern: numbers with units appearing multiple times in close proximity
    lines_with_numbers = []
    for line in text.splitlines():
        # Match lines with numeric values (including %, ms, KB, x multipliers, etc.)
        if re.search(r'\b\d+\.?\d*\s*(%|ms|MB|GB|KB|x|×|times|seconds?|minutes?|hours?)\b', line, re.IGNORECASE):
            lines_with_numbers.append(line)
    return len(lines_with_numbers)


def count_process_steps(text: str) -> int:
    """Count ordered/sequential step markers."""
    step_patterns = [
        r'^\s*\d+\.\s+',           # Numbered list items
        r'\b(step\s+\d+|first[,:]|second[,:]|third[,:]|then[,:]|finally[,:]|next[,:])\b',
        r'\b(begin|start|initialize|configure|deploy|verify|complete)\b',
    ]
    count = 0
    for line in text.splitlines():
        for pattern in step_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                count += 1
                break
    return count


def count_parallel_bullet_runs(text: str) -> int:
    """Count the max run of consecutive bullet list items."""
    max_run = 0
    current_run = 0
    for line in text.splitlines():
        if re.match(r'^\s*[-*+]\s+', line):
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0
    return max_run


def count_citations(text: str) -> int:
    """Count inline [N](url) citation occurrences."""
    return len(re.findall(r'\[\d+\]\(https?://[^\)]+\)', text))


def count_words(text: str) -> int:
    return len(text.split())


def compute_hints(section: dict) -> dict:
    body = section["body"]
    heading = section["heading"]

    word_count = count_words(body)
    citation_count = count_citations(body)
    numeric_comps = count_numeric_comparisons(body)
    process_steps = count_process_steps(body)
    bullet_run = count_parallel_bullet_runs(body)

    hints = []
    suggested_level = "study"  # default L1

    # Numeric comparisons → table hint
    if numeric_comps >= 6:
        hints.append({"type": "promote_to_table", "target": heading, "strength": "strong",
                      "reason": f"{numeric_comps} lines with numeric values"})
    elif numeric_comps >= 3:
        hints.append({"type": "promote_to_table", "target": heading, "strength": "moderate",
                      "reason": f"{numeric_comps} lines with numeric values"})

    # Process steps → flowchart hint
    if process_steps >= 6:
        hints.append({"type": "promote_to_flowchart", "target": heading, "strength": "strong",
                      "reason": f"{process_steps} process-step markers"})
    elif process_steps >= 4:
        hints.append({"type": "promote_to_flowchart", "target": heading, "strength": "moderate",
                      "reason": f"{process_steps} process-step markers"})

    # Parallel bullet run → table hint
    if bullet_run >= 7:
        hints.append({"type": "promote_to_table", "target": f"{heading} (list)",
                      "strength": "moderate", "reason": f"bullet run of {bullet_run} items"})
    elif bullet_run >= 5:
        hints.append({"type": "promote_to_table", "target": f"{heading} (list)",
                      "strength": "weak", "reason": f"bullet run of {bullet_run} items"})

    # Citation density → reference level
    words_nonzero = max(word_count, 1)
    citation_density = citation_count / words_nonzero * 100  # citations per 100 words
    if citation_density >= 3 or citation_count >= 20:
        suggested_level = "reference"
    elif word_count >= 800:
        suggested_level = "reference"

    return {
        "heading": heading,
        "word_count": word_count,
        "citation_count": citation_count,
        "citation_density_per_100w": round(citation_density, 2),
        "numeric_comparison_lines": numeric_comps,
        "process_step_markers": process_steps,
        "max_bullet_run": bullet_run,
        "hints": hints,
        "suggested_level": suggested_level,
    }


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    sections = parse_sections(text)

    results = [compute_hints(s) for s in sections]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"sections": results}, indent=2), encoding="utf-8")

    print(f"density_scan: analyzed {len(results)} sections → {output_path}")
    for r in results:
        if r["hints"]:
            print(f"  [{r['suggested_level']}] {r['heading']}: {[h['type']+'('+h['strength']+')' for h in r['hints']]}")


if __name__ == "__main__":
    main()
