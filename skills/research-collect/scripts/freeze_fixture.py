"""
freeze_fixture.py — One-time fixture capture helper for QUAL-01 replay mode.

Given a list of URLs, crawls them once using the pipeline's resolved crawl4ai
Python and saves their HTML/markdown to a snapshot directory. Saved snapshots
can be used by parallel_crawl.py --fixture-dir to replay collection without
hitting the live web (for regression testing).

Usage:
    python freeze_fixture.py urls.txt --output-dir ./fixtures/baseline-2026-04-18
    python freeze_fixture.py urls.txt --output-dir ./fixtures/baseline --force
    python freeze_fixture.py urls.txt --output-dir ./fixtures/baseline --max-urls 10
"""

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_crawl4ai_python(scripts_dir: Path) -> str:
    """Call resolve_env.py to discover the crawl4ai Python path."""
    resolve_script = scripts_dir / "resolve_env.py"
    if not resolve_script.exists():
        print(f"ERROR: resolve_env.py not found at {resolve_script}", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(resolve_script)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"ERROR: resolve_env.py failed (exit {result.returncode}):\n{result.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)

    # resolve_env.py prints key=value pairs; look for crawl4ai_python
    for line in result.stdout.splitlines():
        if line.startswith("crawl4ai_python="):
            path = line.split("=", 1)[1].strip()
            if path:
                return path

    print(
        "ERROR: resolve_env.py did not emit crawl4ai_python=<path>",
        file=sys.stderr,
    )
    sys.exit(1)


def url_hash(url: str) -> str:
    """Return first 16 hex chars of SHA-256 of the URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


# Inline Python script run per-URL via the resolved crawl4ai interpreter.
_CRAWL_SCRIPT = """
import asyncio, json, sys

url = sys.argv[1]

async def fetch(url):
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    browser_cfg = BrowserConfig(headless=True)
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=30000,
        remove_overlay_elements=True,
    )
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)
        record = {
            "url": url,
            "final_url": getattr(result, "url", url),
            "title": (result.metadata or {}).get("title", ""),
            "markdown": result.markdown if isinstance(result.markdown, str) else (
                result.markdown.raw_markdown if result.markdown else ""
            ),
            "success": result.success,
            "error": result.error_message if not result.success else None,
        }
        print(json.dumps(record))

asyncio.run(fetch(url))
"""


def crawl_url(crawl4ai_python: str, url: str) -> dict:
    """
    Run a single URL crawl via the resolved crawl4ai Python.
    Returns a dict with: url, final_url, title, markdown, success, error.
    """
    result = subprocess.run(
        [crawl4ai_python, "-c", _CRAWL_SCRIPT, url],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        return {
            "url": url,
            "final_url": url,
            "title": "",
            "markdown": "",
            "success": False,
            "error": result.stderr.strip() or f"exit code {result.returncode}",
        }
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        return {
            "url": url,
            "final_url": url,
            "title": "",
            "markdown": "",
            "success": False,
            "error": f"JSON parse error: {exc}. stdout={result.stdout[:200]}",
        }


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def freeze(
    urls: list[str],
    output_dir: Path,
    crawl4ai_python: str,
    force: bool,
) -> dict:
    """
    Capture snapshots for each URL. Returns manifest dict.
    """
    snapshots_dir = output_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    # Copy input URL list
    (output_dir / "urls.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")

    captured = 0
    skipped = 0
    failed = 0

    total = len(urls)
    for i, url in enumerate(urls, start=1):
        h = url_hash(url)
        md_path = snapshots_dir / f"{h}.md"
        meta_path = snapshots_dir / f"{h}.meta.json"

        if md_path.exists() and not force:
            print(f"[{i}/{total}] SKIP  {url} (snapshot exists; use --force to re-fetch)")
            skipped += 1
            continue

        print(f"[{i}/{total}] FETCH {url}")
        fetched_at = datetime.now(timezone.utc).isoformat()

        try:
            record = crawl_url(crawl4ai_python, url)
        except subprocess.TimeoutExpired:
            record = {
                "url": url,
                "final_url": url,
                "title": "",
                "markdown": "",
                "success": False,
                "error": "timeout (60s)",
            }

        meta = {
            "url": url,
            "final_url": record.get("final_url", url),
            "title": record.get("title", ""),
            "fetched_at": fetched_at,
            "success": record.get("success", False),
            "error": record.get("error"),
        }

        md_path.write_text(record.get("markdown", ""), encoding="utf-8")
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        if record.get("success"):
            captured += 1
            print(f"         OK — {len(record.get('markdown', ''))} chars markdown")
        else:
            failed += 1
            print(f"         FAIL — {record.get('error', 'unknown error')}")

        # Polite rate limiting between fetches
        if i < total:
            delay = random.uniform(1.0, 2.0)
            time.sleep(delay)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "crawl4ai_python": crawl4ai_python,
        "total_urls": total,
        "captured": captured,
        "skipped": skipped,
        "failed": failed,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="freeze_fixture.py",
        description=(
            "One-time fixture capture: crawl URLs and save snapshots for "
            "QUAL-01 regression replay via parallel_crawl.py --fixture-dir."
        ),
    )
    parser.add_argument(
        "urls_file",
        metavar="urls_file",
        help="Path to a text file containing one URL per line.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        metavar="PATH",
        help="Directory to write snapshots/ and manifest.json into.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Re-fetch URLs even if snapshots already exist.",
    )
    parser.add_argument(
        "--max-urls",
        type=int,
        default=None,
        metavar="N",
        help="Only capture the first N URLs (useful for quick baselines).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Resolve paths
    urls_file = Path(args.urls_file)
    if not urls_file.exists():
        print(f"ERROR: urls_file not found: {urls_file}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)

    # Read URLs
    raw_lines = urls_file.read_text(encoding="utf-8").splitlines()
    urls = [line.strip() for line in raw_lines if line.strip() and not line.startswith("#")]

    if not urls:
        print("ERROR: No URLs found in urls_file.", file=sys.stderr)
        sys.exit(1)

    if args.max_urls is not None and args.max_urls > 0:
        urls = urls[: args.max_urls]

    print(f"freeze_fixture: {len(urls)} URL(s) → {output_dir}")

    # Resolve crawl4ai Python
    scripts_dir = Path(__file__).parent
    crawl4ai_python = resolve_crawl4ai_python(scripts_dir)
    print(f"crawl4ai_python: {crawl4ai_python}")

    # Run capture
    manifest = freeze(
        urls=urls,
        output_dir=output_dir,
        crawl4ai_python=crawl4ai_python,
        force=args.force,
    )

    print(
        f"\nDone. captured={manifest['captured']} skipped={manifest['skipped']} "
        f"failed={manifest['failed']} → {output_dir / 'manifest.json'}"
    )


if __name__ == "__main__":
    main()
