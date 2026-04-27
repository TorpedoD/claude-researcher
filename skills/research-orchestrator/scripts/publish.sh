#!/usr/bin/env bash
# publish.sh — Derive report.qmd from report.md, install Mermaid extension (PDF only), copy quarto-pdf-base.yml, render with Quarto.
#
# Usage:
#   publish.sh --run-dir <path> --quarto-output <none|html|pdf|both> --produce-qmd <true|false>
#
# Outputs:
#   <run_dir>/output/report.qmd        (when produce_qmd=true)
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
publish_log="$run_dir/output/publish_log.md"
mkdir -p "$run_dir/output" "$run_dir/logs"

if [[ ! -s "$run_dir/output/report.md" ]]; then
  echo "ERROR: canonical report missing: $run_dir/output/report.md" >&2
  exit 1
fi

# Step 1: Generate Quarto source from canonical Markdown when publishing needs it.
qmd_status=skip
if [[ "$produce_qmd" = "true" ]]; then
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if python3 "$script_dir/make_qmd.py" --run-dir "$run_dir" >> "$publish_log" 2>&1; then
    qmd_status=ok
  else
    qmd_status=warn
    echo "$(date -Iseconds) publishing make_qmd failed — render skipped" >> "$publish_log"
    produce_qmd=false
  fi
fi
echo "QMD_STATUS=$qmd_status"

# Step 2: Install quarto-ext/mermaid extension when PDF selected
mermaid_install_status=skip
if [[ "$quarto_output" = "pdf" || "$quarto_output" = "both" ]]; then
  cd "$run_dir/output"
  if [[ ! -d "_extensions/quarto-ext/mermaid" ]]; then
    if quarto add quarto-ext/mermaid --no-prompt >> "$log" 2>&1; then
      mermaid_install_status=ok
    else
      mermaid_install_status=warn
      echo "$(date -Iseconds) output mermaid_extension_install_failed — Mermaid will render as code blocks in PDF" >> "$log"
      echo "$(date -Iseconds) output mermaid_extension_install_failed — Mermaid will render as code blocks in PDF" >> "$publish_log"
    fi
  else
    mermaid_install_status=ok
  fi
  cd - > /dev/null
fi
echo "MERMAID_INSTALL_STATUS=$mermaid_install_status"

# Step 3: Copy quarto-pdf-base.yml into run output directory when PDF selected
quarto_yml_status=skip
if [[ "$quarto_output" = "pdf" || "$quarto_output" = "both" ]]; then
  template="$HOME/.claude/skills/research-orchestrator/references/quarto-pdf-base.yml"
  target="$run_dir/output/_quarto.yml"
  if [[ -s "$target" ]]; then
    quarto_yml_status=exists
    echo "$(date -Iseconds) output quarto_yml_exists — preserved existing $target" >> "$log"
    echo "$(date -Iseconds) output quarto_yml_exists — preserved existing $target" >> "$publish_log"
  elif [[ ! -f "$template" ]]; then
    quarto_yml_status=warn
    echo "$(date -Iseconds) output quarto_yml_template_missing — $template not found" >> "$log"
    echo "$(date -Iseconds) output quarto_yml_template_missing — $template not found" >> "$publish_log"
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
      echo "$(date -Iseconds) publishing quarto_render_html failed" >> "$log"
      echo "$(date -Iseconds) publishing quarto_render_html failed" >> "$publish_log"
    fi
  fi
  if [[ "$quarto_output" = "pdf" || "$quarto_output" = "both" ]]; then
    if ! quarto render "$run_dir/output/report.qmd" --to pdf >> "$log" 2>&1; then
      render_failed=true
      echo "$(date -Iseconds) publishing quarto_render_pdf failed" >> "$log"
      echo "$(date -Iseconds) publishing quarto_render_pdf failed" >> "$publish_log"
    fi
  fi
fi
echo "RENDER_FAILED=$render_failed"

exit 0
