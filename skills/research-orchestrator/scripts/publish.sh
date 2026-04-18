#!/usr/bin/env bash
# publish.sh — Install Mermaid extension (PDF only), copy quarto-pdf-base.yml, render with Quarto.
#
# Usage:
#   publish.sh --run-dir <path> --quarto-output <none|html|pdf|both> --produce-qmd <true|false>
#
# Outputs:
#   <run_dir>/output/report.html       (when quarto_output=html or both)
#   <run_dir>/output/report.pdf        (when quarto_output=pdf or both)
#   <run_dir>/output/_extensions/      (when quarto_output=pdf or both, mermaid ext)
#   <run_dir>/output/_quarto.yml       (when quarto_output=pdf or both, if not already present)
# All quarto render failures are logged but do NOT cause a non-zero exit.

set -euo pipefail

run_dir=""
quarto_output="none"
produce_qmd="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-dir)       run_dir="$2";       shift 2 ;;
    --quarto-output) quarto_output="$2"; shift 2 ;;
    --produce-qmd)   produce_qmd="$2";   shift 2 ;;
    --help|-h)
      sed -n '2,10p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$run_dir" ]]; then
  echo "ERROR: --run-dir is required" >&2
  exit 1
fi

if [[ ! -d "$run_dir" ]]; then
  echo "ERROR: run_dir does not exist: $run_dir" >&2
  exit 1
fi

log="$run_dir/logs/run_log.md"

# Step 3b: Install quarto-ext/mermaid extension when PDF selected
mermaid_install_status=skip
if [[ "$quarto_output" = "pdf" || "$quarto_output" = "both" ]]; then
  cd "$run_dir/output"
  if [[ ! -d "_extensions/quarto-ext/mermaid" ]]; then
    if quarto add quarto-ext/mermaid --no-prompt >> "$log" 2>&1; then
      mermaid_install_status=ok
    else
      mermaid_install_status=warn
      echo "$(date -Iseconds) output mermaid_extension_install_failed — Mermaid will render as code blocks in PDF" >> "$log"
    fi
  else
    mermaid_install_status=ok
  fi
  cd - > /dev/null
fi
echo "MERMAID_INSTALL_STATUS=$mermaid_install_status"

# Step 3c: Copy quarto-pdf-base.yml into run output directory when PDF selected
quarto_yml_status=skip
if [[ "$quarto_output" = "pdf" || "$quarto_output" = "both" ]]; then
  template="$HOME/.claude/skills/research-orchestrator/references/quarto-pdf-base.yml"
  target="$run_dir/output/_quarto.yml"
  if [[ -s "$target" ]]; then
    quarto_yml_status=exists
    echo "$(date -Iseconds) output quarto_yml_exists — preserved existing $target" >> "$log"
  elif [[ ! -f "$template" ]]; then
    quarto_yml_status=warn
    echo "$(date -Iseconds) output quarto_yml_template_missing — $template not found" >> "$log"
  else
    cp "$template" "$target"
    quarto_yml_status=ok
  fi
fi
echo "QUARTO_YML_STATUS=$quarto_yml_status"

# Step 4: Render with Quarto (conditional, graceful fallback)
render_failed=false
if [[ "$produce_qmd" = "true" ]]; then
  if [[ "$quarto_output" = "html" || "$quarto_output" = "both" ]]; then
    if ! quarto render "$run_dir/output/report.qmd" --to html >> "$log" 2>&1; then
      render_failed=true
      echo "$(date -Iseconds) formatting quarto_render_html failed rc=$?" >> "$log"
    fi
  fi
  if [[ "$quarto_output" = "pdf" || "$quarto_output" = "both" ]]; then
    if ! quarto render "$run_dir/output/report.qmd" --to pdf >> "$log" 2>&1; then
      render_failed=true
      echo "$(date -Iseconds) formatting quarto_render_pdf failed rc=$?" >> "$log"
    fi
  fi
fi
echo "RENDER_FAILED=$render_failed"

exit 0
