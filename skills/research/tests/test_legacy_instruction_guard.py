"""Guard against reintroducing stale active pipeline instructions."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ACTIVE_DOCS = [
    ROOT / "README.md",
    ROOT / "agents",
    ROOT / "skills" / "research-collect" / "SKILL.md",
    ROOT / "skills" / "research-format" / "SKILL.md",
    ROOT / "skills" / "research-synthesize" / "SKILL.md",
    ROOT / "skills" / "research-synthesize" / "references" / "output-quality-spec.md",
    ROOT / "skills" / "research" / "SKILL.md",
]


def iter_active_text_files():
    for path in ACTIVE_DOCS:
        if path.is_dir():
            yield from sorted(path.glob("*.md"))
        else:
            yield path


def test_active_docs_do_not_reintroduce_legacy_pipeline_terms():
    banned_always = [
        "xargs -P docling",
        "citation_registry.json",
        "formatter_destination",
    ]
    deprecated_terms = [
        "numeric citations",
        "raw_research.md",
        "claim_index.json",
    ]
    allowed_context_words = (
        "deprecated",
        "disallow",
        "disallowed",
        "fail",
        "legacy",
        "not part of the main path",
        "not used for new",
        "not use",
        "must not",
        "do not",
    )
    violations = []
    for path in iter_active_text_files():
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for term in banned_always:
            if term.lower() in lowered:
                violations.append(f"{path.relative_to(ROOT)} contains {term!r}")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            line_lower = line.lower()
            for term in deprecated_terms:
                if term not in line_lower:
                    continue
                context = "\n".join(lines[max(0, idx - 1): idx + 2]).lower()
                if not any(word in context for word in allowed_context_words):
                    violations.append(
                        f"{path.relative_to(ROOT)} describes {term!r} without legacy/deprecated framing"
                    )

    assert not violations
