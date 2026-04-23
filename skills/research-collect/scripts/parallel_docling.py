#!/usr/bin/env python3
"""
SDK-driven parallel document converter for the research-collect pipeline.

Converts PDF, DOCX, PPTX, XLSX (and complex HTML) to markdown using Docling's
DocumentConverter, with per-worker persistent converter instances, content-hash
caching, format-aware quality classification, and full provenance YAML headers.

Usage:
    $DOCLING_PYTHON scripts/parallel_docling.py \
        --input-list <paths_file> \
        --output-dir collect/evidence/_staging \
        --runtime-profile manifest.json

Input file format: one file path or URL per line (lines starting with # ignored).

Output:
  - One JSONL record per doc emitted to stdout.
  - <output-dir>/<NNN>-<slug>.md: markdown body with YAML provenance header.
  - <output-dir>/../quarantine/docling/<slug>.md: partial/failure docs.
  - <cache-dir>/<hash>.md + <cache-dir>/<hash>.yaml: cached outputs.

Record shape:
  {"input_index": int, "source": str, "output_path": str|null,
   "quality_class": str, "extraction_method": str, "extraction_method_reason": str,
   "docling_cache_hit": bool, "docling_processing_seconds": float,
   "docling_version": str, "docling_device": str, "docling_threads": int,
   "docling_timeout": int, "success": bool, "error": str|null}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import os
import platform
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Gate-1 remediation: surface import failure before spawning workers
# ---------------------------------------------------------------------------

_IMPORT_ERROR: str | None = None
try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    import docling
    _DOCLING_VERSION = getattr(docling, "__version__", "unknown")
except Exception as _exc:
    _IMPORT_ERROR = str(_exc)
    _DOCLING_VERSION = "unavailable"

# ---------------------------------------------------------------------------
# Format gate constants
# ---------------------------------------------------------------------------

DOCLING_WHITELIST = {".pdf", ".docx", ".pptx", ".xlsx"}
COMPLEX_HTML_SIZE_BYTES = 200 * 1024  # 200 KB
COMPLEX_HTML_TABLE_PATTERN = re.compile(r"<table[\s>]", re.IGNORECASE)
COMPLEX_HTML_IFRAME_PATTERN = re.compile(r"<iframe[\s>]", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Quality thresholds by format (B3)
# ---------------------------------------------------------------------------

# Maps lowercase extension -> (success_min_chars, thin_min_chars, success_headings,
#                                success_sections, success_tables, success_sheets)
# None = not applicable for that format.
_THRESHOLDS: dict[str, dict] = {
    ".pdf":  {"min_success_chars": 2000, "min_thin_chars": 800, "need_heading": True},
    ".docx": {"min_success_chars": 2000, "min_thin_chars": 800, "need_heading": True},
    ".pptx": {"min_sections": 3},
    ".xlsx": {"need_table": True},
}

QUALITY_LABEL = {
    "success":      None,
    "thin_success": "DOCLING_THIN_OUTPUT",
    "partial":      "DOCLING_PARTIAL",
    "failure":      "DOCLING_FAILURE",
}

# ---------------------------------------------------------------------------
# Platform key (for cache key)
# ---------------------------------------------------------------------------

def _platform_key() -> str:
    mach = platform.machine().lower()
    sysname = platform.system().lower()
    return f"{sysname}-{mach}"


# ---------------------------------------------------------------------------
# Worker initializer — runs once per process
# ---------------------------------------------------------------------------

_converter: Any = None  # module-global DocumentConverter (per worker)
_worker_config: dict = {}
_CONVERTER_ERROR: str | None = None


def _build_pipeline_options(timeout_seconds: float, do_ocr: bool = False) -> "PdfPipelineOptions":
    opts = PdfPipelineOptions()
    opts.do_ocr = do_ocr
    opts.do_table_structure = True
    opts.document_timeout = timeout_seconds
    return opts


def _compute_pipeline_options_hash(opts) -> str:
    """SHA-256 of serialized PipelineOptions. Stable across runs."""
    try:
        payload = opts.model_dump(mode="json")      # pydantic v2
    except AttributeError:
        try:
            payload = opts.dict()                   # pydantic v1
        except AttributeError:
            import warnings
            warnings.warn("PipelineOptions has no model_dump/dict; using vars() fallback")
            payload = {k: str(getattr(opts, k)) for k in sorted(vars(opts))}
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _build_converter(pipeline_options: "PdfPipelineOptions") -> "DocumentConverter":
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        }
    )


def _worker_init(config: dict) -> None:
    global _converter, _worker_config, _CONVERTER_ERROR
    _worker_config = config

    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    doc_threads = str(config.get("docling_threads", 2))
    os.environ["DOCLING_NUM_THREADS"] = doc_threads

    if _IMPORT_ERROR:
        return  # converter stays None; worker will surface error per-doc

    device = config.get("docling_device", "cpu")
    timeout = float(config.get("docling_timeout", 300))
    do_ocr = bool(config.get("docling_ocr", False))
    try:
        pipeline_options = _build_pipeline_options(timeout_seconds=timeout, do_ocr=do_ocr)
        _converter = _build_converter(pipeline_options)
    except Exception as exc:
        _CONVERTER_ERROR = str(exc)
        print(f"[error] DOCLING_CONVERTER_INIT_FAILED {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Cache helpers (B2)
# ---------------------------------------------------------------------------

def _cache_key(file_bytes: bytes, device: str, docling_threads: int,
               timeout: int, pipeline_opts_hash: str) -> str:
    h = hashlib.sha256()
    h.update(file_bytes)
    h.update(_DOCLING_VERSION.encode())
    h.update(pipeline_opts_hash.encode())
    h.update(device.encode())
    h.update(str(docling_threads).encode())
    h.update(_platform_key().encode())
    return h.hexdigest()


def _cache_hit(cache_dir: Path, key: str) -> tuple[str | None, dict | None]:
    """Return (markdown, provenance_dict) if cache hit, else (None, None)."""
    md_path = cache_dir / f"{key}.md"
    meta_path = cache_dir / f"{key}.yaml"
    if md_path.exists() and meta_path.exists():
        try:
            import yaml  # type: ignore
            md = md_path.read_text(encoding="utf-8")
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            return md, meta
        except Exception:
            pass
    return None, None


def _cache_store(cache_dir: Path, key: str, markdown: str, meta: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        import yaml  # type: ignore
        (cache_dir / f"{key}.md").write_text(markdown, encoding="utf-8")
        (cache_dir / f"{key}.yaml").write_text(
            yaml.dump(meta, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"[warn] cache store failed: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Format gate (B4)
# ---------------------------------------------------------------------------

def _routing(source: str, content_bytes: bytes | None = None) -> tuple[str, str]:
    """Return (extraction_method, extraction_method_reason)."""
    ext = Path(source).suffix.lower()
    if ext in DOCLING_WHITELIST:
        return "docling_sdk", "whitelist_extension"
    if ext in (".html", ".htm"):
        if content_bytes is not None:
            size = len(content_bytes)
            tables = len(COMPLEX_HTML_TABLE_PATTERN.findall(content_bytes[:4096 * 10].decode("utf-8", errors="replace")))
            has_iframe = bool(COMPLEX_HTML_IFRAME_PATTERN.search(content_bytes[:4096 * 10].decode("utf-8", errors="replace")))
            if size > COMPLEX_HTML_SIZE_BYTES or tables > 3 or has_iframe:
                return "docling_sdk", "complex_html"
        return "direct_read", "direct_read_simple_html"
    if ext in (".md", ".txt", ""):
        return "direct_read", "direct_read_text"
    # Unknown extension — attempt Docling anyway
    return "docling_sdk", "whitelist_extension"


# ---------------------------------------------------------------------------
# Quality classification (B3 — unified schema)
# ---------------------------------------------------------------------------

def _classify_doc(markdown: str, ext: str) -> str:
    """
    Returns one of: success | thin_success | partial | failure
    (challenge_page is only emitted by the crawl path)
    """
    if not markdown or not markdown.strip():
        return "failure"

    body = markdown.strip()
    body_len = len(body)
    heading_count = len(re.findall(r"^#{1,6}\s", body, re.MULTILINE))

    thresholds = _THRESHOLDS.get(ext, {})

    if ext == ".pptx":
        # Count slide-level sections (H1 or H2 treated as slides)
        sections = len(re.findall(r"^#{1,2}\s", body, re.MULTILINE))
        if sections >= thresholds.get("min_sections", 3):
            return "success"
        if sections >= 1:
            return "thin_success"
        return "partial"

    if ext == ".xlsx":
        table_count = len(re.findall(r"^\|", body, re.MULTILINE))
        # Count level-1 headings as sheet proxy (Docling renders each XLSX sheet as an H1)
        sheet_count = sum(1 for line in markdown.splitlines() if line.startswith("# "))
        if thresholds.get("need_table") and table_count >= 1:
            return "success"
        if sheet_count >= 1:
            return "thin_success"
        return "partial"

    if ext in (".html", ".htm"):
        table_count = len(re.findall(r"^\|", body, re.MULTILINE))
        is_complex_html = table_count >= 1
        heading_density = heading_count / max(body_len, 1) * 500
        if is_complex_html or heading_density >= 1:
            return "success"
        if heading_count >= 1:
            return "thin_success"
        return "partial"

    # PDF / DOCX (and unknown)
    min_success = thresholds.get("min_success_chars", 2000)
    min_thin = thresholds.get("min_thin_chars", 800)
    need_heading = thresholds.get("need_heading", True)

    if body_len >= min_success and (not need_heading or heading_count >= 1):
        return "success"
    if body_len >= min_thin and (not need_heading or heading_count >= 1):
        return "thin_success"
    return "partial"


# ---------------------------------------------------------------------------
# Direct-read path (for .md, .txt, simple HTML)
# ---------------------------------------------------------------------------

def _direct_read(source: str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        import urllib.request
        with urllib.request.urlopen(source, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    return Path(source).read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Worker function — called per document
# ---------------------------------------------------------------------------

def _convert_one(args: tuple) -> dict:
    idx, source, config = args

    device = config.get("docling_device", "cpu")
    doc_threads = int(config.get("docling_threads", 2))
    timeout = int(config.get("docling_timeout", 120))
    cache_dir = Path(
        os.environ.get("RESEARCH_CACHE_DIR")
        or config.get("docling_cache_dir")
        or str(Path.home() / ".cache" / "research-collect" / "docling")
    )
    output_dir = Path(config["output_dir"])
    quarantine_dir = output_dir.parent.parent / "quarantine" / "docling"

    t0 = time.monotonic()

    base_record: dict = {
        "input_index": idx,
        "source": source,
        "output_path": None,
        "quality_class": "failure",
        "extraction_method": "unknown",
        "extraction_method_reason": "unknown",
        "docling_cache_hit": False,
        "docling_processing_seconds": 0.0,
        "docling_version": _DOCLING_VERSION,
        "docling_device": device,
        "docling_threads": doc_threads,
        "docling_timeout": timeout,
        "success": False,
        "error": None,
    }

    # Surface import error
    if _IMPORT_ERROR and not source.startswith("http"):
        base_record["error"] = f"docling import failed: {_IMPORT_ERROR}"
        base_record["extraction_method"] = "none"
        base_record["extraction_method_reason"] = "import_error"
        return base_record

    # Read source bytes for routing + cache key
    ext = Path(source).suffix.lower() if not source.startswith("http") else ""
    content_bytes: bytes | None = None
    try:
        if not source.startswith("http") and Path(source).exists():
            content_bytes = Path(source).read_bytes()
        elif source.startswith("http"):
            pass  # will be downloaded by converter
    except Exception as exc:
        base_record["error"] = f"read source: {exc}"
        return base_record

    method, reason = _routing(source, content_bytes)
    base_record["extraction_method"] = method
    base_record["extraction_method_reason"] = reason

    # Direct-read path
    if method == "direct_read":
        try:
            markdown = _direct_read(source)
            quality = _classify_doc(markdown, ext)
            base_record.update({
                "quality_class": quality,
                "success": quality not in ("failure",),
                "docling_processing_seconds": round(time.monotonic() - t0, 3),
            })
            if quality in ("partial", "failure"):
                _write_output(quarantine_dir, idx, source, markdown, base_record)
            else:
                path = _write_output(output_dir, idx, source, markdown, base_record)
                base_record["output_path"] = str(path)
        except Exception as exc:
            base_record["error"] = str(exc)
        return base_record

    # Docling SDK path
    if _IMPORT_ERROR:
        base_record["error"] = f"docling import failed: {_IMPORT_ERROR}"
        return base_record

    # Cache lookup
    if content_bytes is not None:
        do_ocr = bool(config.get("docling_ocr", False))
        pipeline_opts = _build_pipeline_options(timeout_seconds=float(timeout), do_ocr=do_ocr)
        pipeline_opts_hash = _compute_pipeline_options_hash(pipeline_opts)
        cache_key = _cache_key(content_bytes, device, doc_threads, timeout, pipeline_opts_hash)
        cached_md, cached_meta = _cache_hit(cache_dir, cache_key)
        if cached_md is not None:
            quality = cached_meta.get("quality_class", _classify_doc(cached_md, ext))
            base_record.update({
                "quality_class": quality,
                "docling_cache_hit": True,
                "success": quality not in ("failure",),
                "docling_processing_seconds": round(time.monotonic() - t0, 3),
            })
            if quality in ("partial", "failure"):
                _write_output(quarantine_dir, idx, source, cached_md, base_record)
            else:
                path = _write_output(output_dir, idx, source, cached_md, base_record)
                base_record["output_path"] = str(path)
            return base_record
    else:
        cache_key = None

    # Run converter
    global _converter
    converter = _converter
    if converter is None:
        reason = _CONVERTER_ERROR or "unknown init failure"
        print(f"[error] DOCLING_SKIP converter_not_initialized reason={reason} {source}", file=sys.stderr)
        base_record["error"] = f"converter_not_initialized: {reason}"
        return base_record

    try:
        print(f"[info] DOCLING_TIMEOUT_CONFIGURED {source} timeout={timeout}s", file=sys.stderr)
        result = converter.convert(source, raises_on_error=False)
        doc = result.document
        markdown = doc.export_to_markdown() if doc else ""
    except Exception as exc:
        base_record["error"] = str(exc)
        base_record["docling_processing_seconds"] = round(time.monotonic() - t0, 3)
        return base_record

    elapsed = round(time.monotonic() - t0, 3)
    quality = _classify_doc(markdown, ext)
    base_record.update({
        "quality_class": quality,
        "success": quality not in ("failure",),
        "docling_processing_seconds": elapsed,
    })

    # Cache store
    if content_bytes is not None and cache_key:
        _cache_store(cache_dir, cache_key, markdown, {"quality_class": quality,
                                                       "docling_version": _DOCLING_VERSION,
                                                       "device": device})

    label = QUALITY_LABEL.get(quality)
    if label is not None:
        print(f"[warn] {label} {source}", file=sys.stderr)
    if quality in ("partial", "failure"):
        _write_output(quarantine_dir, idx, source, markdown, base_record)
    else:
        path = _write_output(output_dir, idx, source, markdown, base_record)
        base_record["output_path"] = str(path)

    return base_record


def _slugify(s: str) -> str:
    s = Path(s).stem if not s.startswith("http") else s.split("/")[-1].split("?")[0]
    s = re.sub(r"[^\w-]", "-", s).strip("-").lower()
    return s[:60] or "doc"


def _write_output(out_dir: Path, idx: int, source: str, markdown: str,
                  record: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(source)
    filename = f"{idx:03d}-{slug}.md"
    path = out_dir / filename

    provenance = {
        "source": source,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "docling_version": record.get("docling_version", "unknown"),
        "docling_device": record.get("docling_device", "cpu"),
        "docling_threads": record.get("docling_threads", 2),
        "docling_timeout": record.get("docling_timeout", 120),
        "docling_cache_hit": record.get("docling_cache_hit", False),
        "docling_processing_seconds": record.get("docling_processing_seconds", 0.0),
        "extraction_method": record.get("extraction_method", "unknown"),
        "extraction_method_reason": record.get("extraction_method_reason", "unknown"),
        "quality_class": record.get("quality_class", "unknown"),
    }

    yaml_header = "---\n"
    for k, v in provenance.items():
        yaml_header += f"{k}: {json.dumps(v)}\n"
    yaml_header += "---\n\n"

    path.write_text(yaml_header + markdown, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _load_config(profile_path: str | None, args: argparse.Namespace) -> dict:
    config: dict = {}
    if profile_path:
        try:
            manifest = json.loads(Path(profile_path).read_text())
            config = (manifest.get("runtime_profile", {}).get("resolved") or {}).copy()
        except Exception as exc:
            print(f"[warn] could not read runtime profile: {exc}", file=sys.stderr)
    # CLI overrides
    config["output_dir"] = args.output_dir
    if args.device:
        config["docling_device"] = args.device
    if args.threads:
        config["docling_threads"] = args.threads
    if args.timeout:
        config["docling_timeout"] = args.timeout
    if args.parallelism:
        config["docling_parallelism"] = args.parallelism
    # Defaults
    config.setdefault("docling_device", "cpu")
    config.setdefault("docling_threads", 2)
    config.setdefault("docling_timeout", 120)
    config.setdefault("docling_parallelism", 4)
    config.setdefault("docling_cache_dir",
                      str(Path.home() / ".cache" / "research-collect" / "docling"))
    return config


def main() -> None:
    if _IMPORT_ERROR:
        print(
            f"\n[GATE-1 REMEDIATION] Docling SDK could not be imported: {_IMPORT_ERROR}\n"
            "To fix:\n"
            "  pipx install docling\n"
            "  # Then re-run init_run.py to update DOCLING_PYTHON in the manifest.\n"
            "If docling is already installed, set DOCLING_PYTHON to its Python executable:\n"
            "  export DOCLING_PYTHON=$(pipx environment --value PIPX_HOME)/venvs/docling/bin/python3\n",
            file=sys.stderr,
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Parallel Docling SDK converter")
    parser.add_argument("--input-list", required=True, help="File with one source path/URL per line")
    parser.add_argument("--output-dir", required=True, help="Directory for output .md files")
    parser.add_argument("--runtime-profile", default=None, help="Path to manifest.json")
    parser.add_argument("--device", default=None, help="Docling device (cpu/mps/cuda)")
    parser.add_argument("--threads", type=int, default=None, help="Docling intra-doc threads")
    parser.add_argument("--timeout", type=int, default=None, help="Per-doc timeout seconds")
    parser.add_argument("--parallelism", type=int, default=None, help="Worker pool size")
    args = parser.parse_args()

    config = _load_config(args.runtime_profile, args)
    parallelism = int(config.get("docling_parallelism", 4))

    sources = [ln.strip() for ln in Path(args.input_list).read_text().splitlines()
               if ln.strip() and not ln.startswith("#")]

    if not sources:
        print("[warn] input-list is empty — nothing to convert", file=sys.stderr)
        return

    tasks = [(i, src, config) for i, src in enumerate(sources)]

    cache_hit_count = 0
    thin_count = 0

    with multiprocessing.Pool(
        processes=min(parallelism, len(sources)),
        initializer=_worker_init,
        initargs=(config,),
    ) as pool:
        for record in pool.imap_unordered(_convert_one, tasks):
            if record.get("docling_cache_hit"):
                cache_hit_count += 1
            if record.get("quality_class") == "thin_success":
                thin_count += 1
            print(json.dumps(record, ensure_ascii=False), flush=True)

    total = len(sources)
    rate = f"{cache_hit_count}/{total}"
    print(f"[info] DOCLING_CACHE_HIT_RATE {rate} ({cache_hit_count} cached, {thin_count} thin)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
