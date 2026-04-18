#!/usr/bin/env python3
"""
Parallel crawler for the research-collect pipeline.

Two subcommands:
  flat  <urls_file>   Batch-fetch a flat URL list with arun_many + MemoryAdaptiveDispatcher
                      (streaming), pre-interleaved by host for per-host fairness.
  deep  <seeds_file>  Run multiple deep-crawl seeds (BFS or best-first) concurrently.

Both modes:
  - Emit JSONL to stdout, one record per returned page.
  - Preserve input ordering via `input_index` (flat) or `seed_index` (deep) — flat
    mode buffers all results and emits sorted by input_index for canonical ordering.
  - Classify each successful result (success / thin_success / likely_truncated /
    challenge_page) using content-sufficiency and soft-failure heuristics.
  - Track a sliding window of the last 50 results and log adaptive-backoff events
    (advisory only — dispatcher is not mutated mid-run).
  - Support fixture replay (--fixture-dir) for deterministic offline testing.
  - Never raise on per-URL failure; emit success=false records instead.

Record shape (existing fields preserved, new fields additive):
  {"input_index": int, "seed_index": int|null, "seed_url": str|null,
   "url": str, "final_url": str, "title": str, "markdown": str,
   "metadata": {...}, "links": {"internal": [...], "external": [...]},
   "depth": int, "success": bool, "error": str|null,
   "classification": str, "body_length": int, "heading_count": int,
   "content_density": float, "soft_fail_reason": str|null}

Usage:
  python parallel_crawl.py flat urls.txt --max-concurrent 5 --per-domain-cap 2 \
      [--cache bypass|enabled] [--runtime-profile profile.json] \
      [--backoff-log backoff.jsonl] [--fixture-dir fixtures/] > out.jsonl
  python parallel_crawl.py deep seeds.txt --strategy bfs --max-pages-per-seed 15 \
      --max-concurrent 3 [--cache bypass|enabled] > out.jsonl
"""

import argparse
import asyncio
import hashlib
import json
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


# --- RLIMIT_NOFILE bump (before any async machinery) -----------------------------

def _bump_nofile() -> None:
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        target = min(4096, hard) if hard > 0 else 4096
        if target > soft:
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
    except Exception as exc:
        print(f"[warn] RLIMIT_NOFILE bump failed: {exc}", file=sys.stderr)


_bump_nofile()


# --- I/O helpers (unchanged contract) --------------------------------------------

def load_lines(path: str) -> List[str]:
    with open(path) as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]


def host_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


# Pin a reference to the real stdout at import time. Crawl4AI's dispatcher
# prints progress/log lines to whatever sys.stdout currently points at; we
# redirect sys.stdout -> sys.stderr during crawl and write JSONL to the pinned fd
# so the output contract (one JSON record per line on stdout) is preserved.
_REAL_STDOUT = sys.stdout


def _emit(record: Dict[str, Any]) -> None:
    _REAL_STDOUT.write(json.dumps(record, ensure_ascii=False) + "\n")
    _REAL_STDOUT.flush()


# --- Classification (QUAL-02 / QUAL-03) ------------------------------------------

SOFT_FAIL_PATTERNS = [
    r"verify you are human",
    r"enable javascript",
    r"checking your browser",
    r"access denied",
    r"unusual traffic",
    r"cloudflare ray id",
    r"\bcaptcha\b",
    r"are you a robot",
    r"just a moment",
    r"please wait while",
    r"ddos protection",
]

_SOFT_FAIL_RE = re.compile("|".join(SOFT_FAIL_PATTERNS), re.IGNORECASE)
_SHORT_TITLE_FAIL_RE = re.compile(
    r"access denied|forbidden|error|blocked|just a moment", re.IGNORECASE
)

_SENTENCE_END_CHARS = set(".!?)\"'`*#")


def classify_result(markdown: str, title: str) -> Dict[str, Any]:
    """Classify a successful fetch based on body content heuristics.

    Returns a dict with: classification, body_length, heading_count,
    content_density, soft_fail_reason.
    """
    md = markdown or ""
    body_length = len(md)
    heading_count = sum(1 for line in md.splitlines() if line.lstrip().startswith("#"))
    # Approximation: no direct HTML access, so bound content_density in [0, 1).
    content_density = body_length / max(1, body_length + 500)

    soft_fail_reason: Optional[str] = None

    # QUAL-02: anti-bot / challenge detection
    match = _SOFT_FAIL_RE.search(md)
    if match:
        soft_fail_reason = match.group(0)
    elif body_length < 500 and title and _SHORT_TITLE_FAIL_RE.search(title):
        soft_fail_reason = f"short body + suspicious title: {title!r}"

    if soft_fail_reason:
        classification = "challenge_page"
    else:
        # QUAL-03: content sufficiency
        stripped = md.rstrip()
        last_char = stripped[-1] if stripped else ""
        ends_mid_sentence = bool(stripped) and last_char not in _SENTENCE_END_CHARS

        if body_length >= 1500 and heading_count >= 1:
            classification = "success"
        elif 500 <= body_length < 1500:
            classification = "thin_success"
        elif ends_mid_sentence and body_length < 2000:
            classification = "likely_truncated"
        elif body_length >= 1500:
            classification = "success"
        else:
            # body_length < 500 and no soft-fail match — still thin
            classification = "thin_success"

    return {
        "classification": classification,
        "body_length": body_length,
        "heading_count": heading_count,
        "content_density": content_density,
        "soft_fail_reason": soft_fail_reason,
    }


# --- Record builder (existing fields + new classification fields) ---------------

def _result_to_record(
    result: Any,
    input_index: int,
    seed_index: Optional[int] = None,
    seed_url: Optional[str] = None,
) -> Dict[str, Any]:
    ok = bool(getattr(result, "success", False))
    md = ""
    if ok:
        raw_md = getattr(result, "markdown", "") or ""
        md = raw_md if isinstance(raw_md, str) else getattr(raw_md, "raw_markdown", "") or str(raw_md)
    metadata = getattr(result, "metadata", {}) or {}
    links = getattr(result, "links", {}) or {}
    title = metadata.get("title", "") or ""

    base = {
        "input_index": input_index,
        "seed_index": seed_index,
        "seed_url": seed_url,
        "url": getattr(result, "url", ""),
        "final_url": metadata.get("final_url") or getattr(result, "url", ""),
        "title": title,
        "markdown": md,
        "metadata": {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool, type(None)))},
        "links": {
            "internal": [l.get("href") if isinstance(l, dict) else l for l in (links.get("internal") or [])][:100],
            "external": [l.get("href") if isinstance(l, dict) else l for l in (links.get("external") or [])][:100],
        },
        "depth": int(metadata.get("depth", 0) or 0),
        "success": ok,
        "error": getattr(result, "error_message", None) if not ok else None,
    }

    if ok:
        quality = classify_result(md, title)
    else:
        quality = {
            "classification": "failure",
            "body_length": 0,
            "heading_count": 0,
            "content_density": 0.0,
            "soft_fail_reason": None,
        }
    base.update(quality)
    return base


# --- Adaptive backoff monitor (QUAL-06 / QUAL-07) --------------------------------

class BackoffMonitor:
    WINDOW_SIZE = 50
    RATE_429_THRESHOLD = 0.15
    SUCCESS_RATE_THRESHOLD = 0.70
    EVENT_CAP = 4

    def __init__(self, log_path: Optional[str]):
        self.log_path = log_path
        self._log_fh = open(log_path, "w") if log_path else None
        self._window: deque = deque(maxlen=self.WINDOW_SIZE)
        self._event_count = 0
        self._locked = False

    def record(self, success: bool, status_code: Optional[int]) -> None:
        self._window.append({
            "success": bool(success),
            "throttled": status_code in (429, 503) if status_code is not None else False,
        })
        if self._locked or len(self._window) < self.WINDOW_SIZE:
            return

        n = len(self._window)
        rate_429 = sum(1 for r in self._window if r["throttled"]) / n
        success_rate = sum(1 for r in self._window if r["success"]) / n

        trigger: Optional[str] = None
        if rate_429 > self.RATE_429_THRESHOLD:
            trigger = "rate_429"
        elif success_rate < self.SUCCESS_RATE_THRESHOLD:
            trigger = "low_success"

        if trigger is None:
            return

        self._event_count += 1
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "trigger": trigger,
            "rate_429": round(rate_429, 4),
            "success_rate": round(success_rate, 4),
            "window_size": n,
            "recommendation": "reduce max_concurrent",
        }

        if self._event_count > self.EVENT_CAP:
            self._locked = True
            event["type"] = "BACKOFF_LOCK"
            event["recommendation"] = (
                "oscillation cap reached — stopping further backoff events for this run"
            )
            self._write(event)
            return

        self._write(event)

    def _write(self, event: Dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False)
        if self._log_fh is not None:
            self._log_fh.write(line + "\n")
            self._log_fh.flush()
        else:
            print(f"[WARN backoff] {line}", file=sys.stderr)

    def close(self) -> None:
        if self._log_fh is not None:
            try:
                self._log_fh.close()
            except Exception:
                pass


# --- Interleaving for per-host fairness -----------------------------------------

def interleave_by_host(urls: List[str]) -> List[str]:
    """Round-robin URLs across hosts so the dispatcher's queue won't blast
    a single host in order."""
    groups: Dict[str, List[str]] = defaultdict(list)
    for u in urls:
        groups[host_of(u)].append(u)
    queues = [list(g) for g in groups.values()]
    result: List[str] = []
    while any(queues):
        for q in queues:
            if q:
                result.append(q.pop(0))
    return result


# --- Fixture replay (QUAL-01) ----------------------------------------------------

def _fixture_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _load_fixture(fixture_dir: str, url: str) -> Tuple[bool, str]:
    path = Path(fixture_dir) / "snapshots" / f"{_fixture_hash(url)}.md"
    if path.exists():
        try:
            return True, path.read_text(encoding="utf-8")
        except Exception as exc:
            return False, f"fixture_read_error: {exc}"
    return False, "fixture_not_found"


async def run_fixture_replay(
    urls: List[str],
    fixture_dir: str,
    seed_index: Optional[int] = None,
    seed_url: Optional[str] = None,
) -> None:
    """Emit records from pre-captured fixture files."""
    for idx, u in enumerate(urls):
        found, payload = _load_fixture(fixture_dir, u)
        if found:
            fake = SimpleNamespace(
                success=True,
                url=u,
                markdown=payload,
                error_message=None,
                metadata={"title": ""},
                links={},
                status_code=200,
            )
            _emit(_result_to_record(fake, input_index=idx, seed_index=seed_index, seed_url=seed_url))
        else:
            fake = SimpleNamespace(
                success=False,
                url=u,
                markdown="",
                error_message=payload,
                metadata={},
                links={},
                status_code=None,
            )
            _emit(_result_to_record(fake, input_index=idx, seed_index=seed_index, seed_url=seed_url))


# --- Runtime profile loading -----------------------------------------------------

def load_runtime_profile(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[warn] failed to read runtime profile {path}: {exc}", file=sys.stderr)
        return {}
    rec = data.get("recommended") if isinstance(data, dict) else None
    return rec if isinstance(rec, dict) else {}


# --- Crawler context -------------------------------------------------------------

async def _build_crawler_imports():
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher
    try:
        from crawl4ai.async_dispatcher import RateLimiter  # type: ignore
    except Exception:
        RateLimiter = None  # type: ignore
    return {
        "AsyncWebCrawler": AsyncWebCrawler,
        "BrowserConfig": BrowserConfig,
        "CrawlerRunConfig": CrawlerRunConfig,
        "CacheMode": CacheMode,
        "MemoryAdaptiveDispatcher": MemoryAdaptiveDispatcher,
        "RateLimiter": RateLimiter,
    }


def _build_dispatcher(imports: Dict[str, Any], max_concurrent: int):
    MAD = imports["MemoryAdaptiveDispatcher"]
    RateLimiter = imports.get("RateLimiter")

    # Probe which rate-limiter kwarg the installed crawl4ai accepts.
    # 0.8.6 uses `rate_limiter`; older/newer versions may differ or omit it.
    rl_kwarg: Optional[str] = None
    try:
        import inspect
        params = inspect.signature(MAD.__init__).parameters
        for candidate in ("rate_limiter", "rate_limit_config"):
            if candidate in params:
                rl_kwarg = candidate
                break
    except Exception:
        rl_kwarg = None

    kwargs: Dict[str, Any] = {
        "memory_threshold_percent": 75.0,
        "max_session_permit": max_concurrent,
    }
    if RateLimiter is not None and rl_kwarg is not None:
        try:
            kwargs[rl_kwarg] = RateLimiter(
                base_delay=(0.5, 1.5),
                max_delay=10.0,
                max_retries=2,
                rate_limit_codes=[429, 503],
            )
        except Exception as exc:
            print(f"[warn] RateLimiter init failed, continuing without: {exc}", file=sys.stderr)
    return MAD(**kwargs)


# --- Flat mode -------------------------------------------------------------------

async def run_flat(
    urls: List[str],
    max_concurrent: int,
    per_domain_cap: int,
    cache_mode: str,
    backoff_log: Optional[str],
) -> None:
    imports = await _build_crawler_imports()
    AsyncWebCrawler = imports["AsyncWebCrawler"]
    BrowserConfig = imports["BrowserConfig"]
    CrawlerRunConfig = imports["CrawlerRunConfig"]
    CacheMode = imports["CacheMode"]

    cm = CacheMode.BYPASS if cache_mode == "bypass" else CacheMode.ENABLED

    interleaved = interleave_by_host(urls)
    index_by_url: Dict[str, int] = {}
    for i, u in enumerate(interleaved):
        # In case of duplicates, keep the first occurrence.
        index_by_url.setdefault(u, i)

    run_cfg = CrawlerRunConfig(
        cache_mode=cm,
        stream=True,
        remove_overlay_elements=True,
        page_timeout=30000,
        screenshot=False,
    )

    dispatcher = _build_dispatcher(imports, max_concurrent)
    monitor = BackoffMonitor(backoff_log)

    browser_cfg = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        verbose=False,
    )

    # per_domain_cap is retained as an advisory for the pre-interleave step;
    # it does not map onto MemoryAdaptiveDispatcher directly in 0.8.6.
    _ = per_domain_cap

    buffer: Dict[int, Dict[str, Any]] = {}
    seen_urls: set = set()

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            try:
                stream = await crawler.arun_many(
                    urls=interleaved,
                    config=run_cfg,
                    dispatcher=dispatcher,
                )
                async for result in stream:
                    url = getattr(result, "url", "") or ""
                    idx = index_by_url.get(url)
                    if idx is None:
                        # Unknown URL (e.g., redirect target). Assign end-of-range slot.
                        idx = len(interleaved) + len(buffer)
                    # Guard against duplicate emissions.
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    record = _result_to_record(result, input_index=idx)
                    buffer[idx] = record
                    monitor.record(
                        success=record["success"],
                        status_code=getattr(result, "status_code", None),
                    )
            except Exception as exc:
                # Catastrophic failure: emit failure records for anything unfetched.
                print(f"[error] arun_many failed: {type(exc).__name__}: {exc}", file=sys.stderr)
                for i, u in enumerate(interleaved):
                    if i in buffer:
                        continue
                    buffer[i] = {
                        "input_index": i,
                        "seed_index": None,
                        "seed_url": None,
                        "url": u,
                        "final_url": u,
                        "title": "",
                        "markdown": "",
                        "metadata": {},
                        "links": {"internal": [], "external": []},
                        "depth": 0,
                        "success": False,
                        "error": f"{type(exc).__name__}: {exc}",
                        "classification": "failure",
                        "body_length": 0,
                        "heading_count": 0,
                        "content_density": 0.0,
                        "soft_fail_reason": None,
                    }

        # Fill in any URLs that never produced a result.
        for i, u in enumerate(interleaved):
            if i not in buffer:
                buffer[i] = {
                    "input_index": i,
                    "seed_index": None,
                    "seed_url": None,
                    "url": u,
                    "final_url": u,
                    "title": "",
                    "markdown": "",
                    "metadata": {},
                    "links": {"internal": [], "external": []},
                    "depth": 0,
                    "success": False,
                    "error": "no_result_from_dispatcher",
                    "classification": "failure",
                    "body_length": 0,
                    "heading_count": 0,
                    "content_density": 0.0,
                    "soft_fail_reason": None,
                }

        # QUAL-05: canonical emission order.
        for i in sorted(buffer.keys()):
            _emit(buffer[i])
    finally:
        monitor.close()


# --- Deep mode -------------------------------------------------------------------

async def run_deep(
    seeds: List[str],
    strategy: str,
    max_pages_per_seed: int,
    max_concurrent: int,
    cache_mode: str,
    backoff_log: Optional[str],
) -> None:
    imports = await _build_crawler_imports()
    AsyncWebCrawler = imports["AsyncWebCrawler"]
    BrowserConfig = imports["BrowserConfig"]
    CrawlerRunConfig = imports["CrawlerRunConfig"]
    CacheMode = imports["CacheMode"]

    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy

    cm = CacheMode.BYPASS if cache_mode == "bypass" else CacheMode.ENABLED

    def make_strategy():
        if strategy == "bfs":
            return BFSDeepCrawlStrategy(
                max_depth=3, max_pages=max_pages_per_seed, include_external=False
            )
        return BestFirstCrawlingStrategy(
            max_depth=3, max_pages=max_pages_per_seed, include_external=False
        )

    seed_sem = asyncio.Semaphore(max_concurrent)
    input_counter = {"n": 0}
    counter_lock = asyncio.Lock()

    monitor = BackoffMonitor(backoff_log)

    browser_cfg = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        verbose=False,
    )

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            async def _run_seed(seed_index: int, seed_url: str) -> None:
                async with seed_sem:
                    run_cfg = CrawlerRunConfig(
                        cache_mode=cm,
                        deep_crawl_strategy=make_strategy(),
                        remove_overlay_elements=True,
                        page_timeout=30000,
                        screenshot=False,
                    )
                    try:
                        results = await crawler.arun(url=seed_url, config=run_cfg)
                        iterable = results if isinstance(results, list) else [results]
                        for res in iterable:
                            async with counter_lock:
                                idx = input_counter["n"]
                                input_counter["n"] += 1
                            record = _result_to_record(
                                res,
                                input_index=idx,
                                seed_index=seed_index,
                                seed_url=seed_url,
                            )
                            _emit(record)
                            monitor.record(
                                success=record["success"],
                                status_code=getattr(res, "status_code", None),
                            )
                    except Exception as exc:
                        async with counter_lock:
                            idx = input_counter["n"]
                            input_counter["n"] += 1
                        _emit({
                            "input_index": idx,
                            "seed_index": seed_index,
                            "seed_url": seed_url,
                            "url": seed_url,
                            "final_url": seed_url,
                            "title": "",
                            "markdown": "",
                            "metadata": {},
                            "links": {"internal": [], "external": []},
                            "depth": 0,
                            "success": False,
                            "error": f"{type(exc).__name__}: {exc}",
                            "classification": "failure",
                            "body_length": 0,
                            "heading_count": 0,
                            "content_density": 0.0,
                            "soft_fail_reason": None,
                        })
                        monitor.record(success=False, status_code=None)

            await asyncio.gather(*[_run_seed(i, s) for i, s in enumerate(seeds)])
    finally:
        monitor.close()


# --- CLI -------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Parallel crawler for research-collect")
    sub = p.add_subparsers(dest="mode", required=True)

    flat = sub.add_parser("flat", help="Batch fetch a flat URL list")
    flat.add_argument("urls_file")
    flat.add_argument("--max-concurrent", type=int, default=None)
    flat.add_argument("--per-domain-cap", type=int, default=None)
    flat.add_argument("--cache", choices=["bypass", "enabled"], default="enabled")
    flat.add_argument("--runtime-profile", default=None,
                      help="Path to detect_runtime.py JSON output; CLI flags override.")
    flat.add_argument("--backoff-log", default=None,
                      help="Sidecar JSONL file for adaptive-backoff events.")
    flat.add_argument("--fixture-dir", default=None,
                      help="Directory containing snapshots/<sha256[:16]>.md fixtures (offline replay).")

    deep = sub.add_parser("deep", help="Run multiple deep-crawl seeds concurrently")
    deep.add_argument("seeds_file")
    deep.add_argument("--strategy", choices=["bfs", "best-first"], default="bfs")
    deep.add_argument("--max-pages-per-seed", type=int, default=15)
    deep.add_argument("--max-concurrent", type=int, default=None)
    deep.add_argument("--cache", choices=["bypass", "enabled"], default="enabled")
    deep.add_argument("--runtime-profile", default=None,
                      help="Path to detect_runtime.py JSON output; CLI flags override.")
    deep.add_argument("--backoff-log", default=None,
                      help="Sidecar JSONL file for adaptive-backoff events.")
    deep.add_argument("--fixture-dir", default=None,
                      help="Directory containing snapshots/<sha256[:16]>.md fixtures (offline replay).")
    return p


def _resolve_concurrency(
    cli_max: Optional[int],
    cli_cap: Optional[int],
    profile: Dict[str, Any],
    defaults: Tuple[int, int],
) -> Tuple[int, int]:
    default_max, default_cap = defaults
    max_c = cli_max if cli_max is not None else profile.get("max_concurrent", default_max)
    cap = cli_cap if cli_cap is not None else profile.get("per_domain_cap", default_cap)
    try:
        max_c = int(max_c)
    except Exception:
        max_c = default_max
    try:
        cap = int(cap)
    except Exception:
        cap = default_cap
    return max_c, cap


def main() -> int:
    args = build_parser().parse_args()
    profile = load_runtime_profile(getattr(args, "runtime_profile", None))

    # Redirect sys.stdout -> sys.stderr for the duration of the run so
    # Crawl4AI's dispatcher/monitor print() calls don't corrupt the JSONL
    # output contract. _emit() writes directly to the pinned _REAL_STDOUT.
    sys.stdout = sys.stderr

    if args.mode == "flat":
        urls = load_lines(args.urls_file)
        if not urls:
            print("no urls", file=sys.stderr)
            return 1
        max_c, cap = _resolve_concurrency(
            args.max_concurrent, args.per_domain_cap, profile, defaults=(5, 2)
        )
        if args.fixture_dir:
            asyncio.run(run_fixture_replay(urls, args.fixture_dir))
            return 0
        asyncio.run(run_flat(urls, max_c, cap, args.cache, args.backoff_log))
    else:
        seeds = load_lines(args.seeds_file)
        if not seeds:
            print("no seeds", file=sys.stderr)
            return 1
        max_c, _ = _resolve_concurrency(
            args.max_concurrent, None, profile, defaults=(3, 2)
        )
        if args.fixture_dir:
            # In deep-mode fixture replay, treat each seed as its own record.
            asyncio.run(run_fixture_replay(seeds, args.fixture_dir))
            return 0
        asyncio.run(
            run_deep(
                seeds,
                args.strategy,
                args.max_pages_per_seed,
                max_c,
                args.cache,
                args.backoff_log,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
