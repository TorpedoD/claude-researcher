#!/usr/bin/env bash
# One-shot installer for the Research Pipeline for Claude Code.
# Copies skills + agents into ~/.claude/ and installs the Python helper package.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILLS="$HOME/.claude/skills"
CLAUDE_AGENTS="$HOME/.claude/agents"

echo "→ Research Pipeline installer"
echo "  Source: $REPO_DIR"
echo "  Target: ~/.claude/{skills,agents}"
echo

mkdir -p "$CLAUDE_SKILLS" "$CLAUDE_AGENTS"

echo "→ Installing skills..."
for skill in research-orchestrator research-collect research-synthesize research-format; do
  if [ -d "$CLAUDE_SKILLS/$skill" ]; then
    echo "  ! $skill already exists — backing up to ${skill}.bak"
    rm -rf "$CLAUDE_SKILLS/${skill}.bak"
    mv "$CLAUDE_SKILLS/$skill" "$CLAUDE_SKILLS/${skill}.bak"
  fi
  cp -R "$REPO_DIR/skills/$skill" "$CLAUDE_SKILLS/"
  echo "  ✓ $skill"
done

echo "→ Installing agents..."
for agent in research-orchestrator research-collector research-synthesizer researcher; do
  cp "$REPO_DIR/agents/${agent}.md" "$CLAUDE_AGENTS/"
  echo "  ✓ ${agent}.md"
done

echo "→ Installing Python helper package..."
if command -v pip >/dev/null 2>&1; then
  pip install -e "$REPO_DIR/scripts/research_orchestrator" 2>/dev/null || \
    echo "  ! pip install failed — package is still importable from $REPO_DIR/scripts/"
  echo "  ✓ research_orchestrator"
else
  echo "  ! pip not found — skipping Python package install"
fi

echo
echo "✓ Installation complete."
echo
echo "Next steps:"
echo "  1. Ensure prerequisites are installed (see README.md):"
echo "     pipx install crawl4ai==0.8.6 && crawl4ai-setup"
echo "     pipx install docling==2.86.0"
echo "     brew install --cask quarto"
echo "  2. Install Graphify: https://github.com/safishamsi/graphify"
echo "  3. Open Claude Code and run: /research \"your topic\""
