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
import random
import re
import sys
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse


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


# --- Resume / staging-index helpers (A2) -----------------------------------------

@dataclass
class ResumeReject:
    task_id: str
    url: str
    reason: str   # "staged_file_missing" | "content_hash_mismatch" | "non_success_status"


class ResumeViolation(RuntimeError):
    """Fail-loud: duplicate task_id with different URL indicates corrupt run."""


def load_staging_index(path) -> Tuple[list, List[ResumeReject]]:
    """Parse staging_index.jsonl; apply 3 refuse-to-reuse conditions.

    Conditions:
      1. status != success → reject (non_success_status)
      2. Same task_id with different URLs → ResumeViolation (fail loud)
      3. staged_path missing on disk → reject (staged_file_missing)
      4. sha256(staged content) != content_hash → reject (content_hash_mismatch)
    """
    entries: list = []
    rejects: List[ResumeReject] = []
    seen: Dict[str, str] = {}
    p = Path(path)
    if not p.exists():
        return entries, rejects
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        tid, url = row.get("task_id"), row.get("url")
        if tid in seen and seen[tid] != url:
            raise ResumeViolation(
                f"task_id={tid!r} seen with urls {seen[tid]!r} and {url!r}"
            )
        seen[tid] = url
        if row.get("status") != "success":
            rejects.append(ResumeReject(tid, url, "non_success_status"))
            continue
        staged = row.get("staged_path")
        if not staged or not Path(staged).exists():
            rejects.append(ResumeReject(tid, url, "staged_file_missing"))
            continue
        recomputed = hashlib.sha256(Path(staged).read_bytes()).hexdigest()
        if recomputed != row.get("content_hash"):
            rejects.append(ResumeReject(tid, url, "content_hash_mismatch"))
            continue
        entries.append(row)
    return entries, rejects


# --- Classification (QUAL-02 / QUAL-03) -----------------------------------------

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
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx"}
DOCUMENT_PATH_HINTS = (
    "/pdf/",
    "/download/pdf",
    "/research/pdf/",
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

# A4: Header profiles for web crawl path only (never used in docling or direct-read paths)
_HEADER_PROFILES = [
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "en-US,en;q=0.9"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "en-US,en;q=0.8"),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36", "en-GB,en;q=0.9"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15", "en-US,en;q=0.9"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0", "en-US,en;q=0.7"),
    ("Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0", "en-GB,en;q=0.8"),
]
_STABLE_PROFILE_ID = 0  # index used for non-aggressive runs


def _pick_header_profile(performance_mode: str, host: str) -> tuple[tuple, int]:
    """Return (ua_accept_lang_tuple, profile_id). Random per host in aggressive mode."""
    if performance_mode == "aggressive":
        idx = hash(host) % len(_HEADER_PROFILES)
        return _HEADER_PROFILES[idx], idx
    return _HEADER_PROFILES[_STABLE_PROFILE_ID], _STABLE_PROFILE_ID


def _is_same_site(url1: str, url2: str) -> bool:
    """True if url1 and url2 share the same registrable domain (best-effort)."""
    def _reg_domain(u: str) -> str:
        try:
            import tldextract  # type: ignore
            ext = tldextract.extract(u)
            return f"{ext.domain}.{ext.suffix}".lower()
        except ImportError:
            # Fallback: naive suffix match on hostname
            h = (urlparse(u).hostname or "").lower()
            parts = h.split(".")
            return ".".join(parts[-2:]) if len(parts) >= 2 else h
    return _reg_domain(url1) == _reg_domain(url2)


def _same_site_referer(seed_url: str, target_url: str) -> Optional[str]:
    """Return seed_url as Referer if seed and target share the same hostname."""
    if not seed_url or not target_url:
        return None
    try:
        s = urlparse(seed_url)
        t = urlparse(target_url)
        if s.hostname and t.hostname and s.hostname == t.hostname:
            return seed_url
    except Exception:
        pass
    return None


def _crawl_slug(url: str) -> str:
    s = urlparse(url).path.rstrip("/").split("/")[-1] or urlparse(url).hostname or "page"
    s = re.sub(r"[^\w-]", "-", s).strip("-").lower()
    return s[:60] or "page"


def is_document_url(url: str) -> bool:
    parsed = urlparse(url.split("#", 1)[0])
    path = parsed.path.lower()
    query = parsed.query.lower()
    if any(path.endswith(ext) for ext in DOCUMENT_EXTENSIONS):
        return True
    if any(hint in path for hint in DOCUMENT_PATH_HINTS):
        return True
    return any(token in query for token in ("format=pdf", "type=pdf"))


def document_links_from_record(record: Dict[str, Any]) -> List[str]:
    """Return unique crawl-discovered document links that should be parsed by Docling."""
    base_url = record.get("final_url") or record.get("url") or ""
    candidates: list[str] = []
    for group in ("internal", "external"):
        for href in record.get("links", {}).get(group, []) or []:
            if isinstance(href, str):
                candidates.append(href)
    for href in MARKDOWN_LINK_RE.findall(record.get("markdown", "") or ""):
        candidates.append(href)

    out: list[str] = []
    seen: set[str] = set()
    for href in candidates:
        absolute = urljoin(base_url, href)
        if is_document_url(absolute) and absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


# Stepped concurrency ladder (mirrors CEILINGS values across tiers)
_CONCURRENCY_LADDER = [4, 8, 12, 16, 24]


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
    base["docling_candidate_urls"] = document_links_from_record(base) if ok else []
    return base


# --- Adaptive backoff monitor (QUAL-06 / QUAL-07) --------------------------------

class BackoffMonitor:
    WINDOW_SIZE = 50
    RATE_429_THRESHOLD = 0.15      # global trigger
    HOST_429_THRESHOLD = 0.30      # per-host trigger (host-only action)
    SUCCESS_RATE_THRESHOLD = 0.70
    RECOVERY_RATE_THRESHOLD = 0.05 # global 429 rate below which we step up
    RECOVERY_WINDOW = 50
    EVENT_CAP = 4
    MIN_DWELL_SECONDS = 30

    def __init__(self, log_path: Optional[str], dispatcher=None, rate_limiter=None,
                 min_dwell_seconds: float = 30.0):
        self.log_path = log_path
        self._log_fh = open(log_path, "w") if log_path else None
        self._window: deque = deque(maxlen=self.WINDOW_SIZE)
        self._event_count = 0
        self._locked = False
        self._dispatcher = dispatcher
        self._rate_limiter = rate_limiter
        self._last_mutation_at: float = 0.0
        self.min_dwell_seconds = min_dwell_seconds
        # per-host 429 sliding windows
        self._host_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.WINDOW_SIZE))

    def record(self, success: bool, status_code: Optional[int],
               host: str = "", response_headers: Optional[Dict] = None) -> None:
        import time as _time

        throttled = status_code in (429, 503) if status_code is not None else False
        self._window.append({"success": bool(success), "throttled": throttled, "host": host})
        if host:
            self._host_windows[host].append({"throttled": throttled})

        # Honor Retry-After header on 429/503
        if throttled and response_headers and self._rate_limiter is not None:
            retry_after = self._parse_retry_after(response_headers)
            if retry_after and host:
                try:
                    dom = getattr(self._rate_limiter, "domains", {})
                    entry = dom.get(host)
                    if entry is not None:
                        current = getattr(entry, "current_delay", 0.0)
                        entry.current_delay = max(current, retry_after)
                        self._write({"ts": datetime.now(timezone.utc).isoformat(),
                                     "type": "RETRY_AFTER_HONORED", "host": host,
                                     "retry_after_seconds": retry_after,
                                     "new_delay": entry.current_delay})
                except Exception:
                    pass

        if self._locked or len(self._window) < self.WINDOW_SIZE:
            return

        now = _time.monotonic()
        n = len(self._window)
        rate_429 = sum(1 for r in self._window if r["throttled"]) / n
        success_rate = sum(1 for r in self._window if r["success"]) / n

        # Per-host spike check (host-only action, don't touch global concurrency)
        if host and len(self._host_windows[host]) >= 20:
            hw = self._host_windows[host]
            host_rate = sum(1 for r in hw if r["throttled"]) / len(hw)
            if host_rate > self.HOST_429_THRESHOLD and rate_429 < self.RATE_429_THRESHOLD:
                if now - self._last_mutation_at >= self.min_dwell_seconds:
                    self._bump_host_delay(host, now)
                return

        # Recovery: step up concurrency if 429 rate has recovered
        if (rate_429 < self.RECOVERY_RATE_THRESHOLD and success_rate >= self.SUCCESS_RATE_THRESHOLD
                and self._dispatcher is not None
                and now - self._last_mutation_at >= self.min_dwell_seconds):
            self._step_concurrency(direction=1, rate_429=rate_429,
                                   success_rate=success_rate, now=now)
            return

        trigger: Optional[str] = None
        if rate_429 > self.RATE_429_THRESHOLD:
            trigger = "rate_429"
        elif success_rate < self.SUCCESS_RATE_THRESHOLD:
            trigger = "low_success"

        if trigger is None:
            return

        # Respect dwell time between mutations
        if now - self._last_mutation_at < self.min_dwell_seconds:
            return

        # Skip if dispatcher is under memory pressure
        if self._dispatcher is not None and getattr(self._dispatcher, "memory_pressure_mode", False):
            return

        self._event_count += 1
        if self._event_count > self.EVENT_CAP:
            self._locked = True
            self._write({"ts": datetime.now(timezone.utc).isoformat(), "type": "BACKOFF_LOCK",
                         "recommendation": "oscillation cap reached"})
            return

        self._step_concurrency(direction=-1, rate_429=rate_429,
                               success_rate=success_rate, now=now, trigger=trigger)

    def _step_concurrency(self, direction: int, rate_429: float,
                          success_rate: float, now: float, trigger: str = "recovery") -> None:
        if self._dispatcher is None:
            return
        current = getattr(self._dispatcher, "max_session_permit", None)
        if current is None:
            return
        # Find current position in ladder, step by one
        ladder = _CONCURRENCY_LADDER
        if direction == -1:
            candidates = [v for v in ladder if v < current]
            new_val = max(candidates) if candidates else ladder[0]
        else:
            candidates = [v for v in ladder if v > current]
            new_val = min(candidates) if candidates else current
        if new_val == current:
            return
        try:
            self._dispatcher.max_session_permit = new_val
            self._last_mutation_at = now
            self._write({"ts": datetime.now(timezone.utc).isoformat(),
                         "type": "BACKOFF_THROTTLE_APPLIED",
                         "direction": "down" if direction == -1 else "up",
                         "trigger": trigger,
                         "max_session_permit_before": current,
                         "max_session_permit_after": new_val,
                         "rate_429": round(rate_429, 4),
                         "success_rate": round(success_rate, 4)})
        except Exception as exc:
            print(f"[warn] backoff concurrency mutation failed: {exc}", file=sys.stderr)

    def _bump_host_delay(self, host: str, now: float) -> None:
        if self._rate_limiter is None:
            return
        try:
            dom = getattr(self._rate_limiter, "domains", {})
            entry = dom.get(host)
            if entry is not None:
                before = getattr(entry, "current_delay", 0.0)
                entry.current_delay = before * 1.5
                self._last_mutation_at = now
                self._write({"ts": datetime.now(timezone.utc).isoformat(),
                             "type": "BACKOFF_THROTTLE_APPLIED",
                             "direction": "host_delay_bump",
                             "host": host,
                             "delay_before": round(before, 3),
                             "delay_after": round(entry.current_delay, 3)})
        except Exception as exc:
            print(f"[warn] host delay bump failed: {exc}", file=sys.stderr)

    @staticmethod
    def _parse_retry_after(headers: Dict) -> Optional[float]:
        for key in ("retry-after", "Retry-After", "RETRY-AFTER"):
            val = headers.get(key)
            if val is not None:
                try:
                    return float(val)
                except Exception:
                    pass
        return None

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


def _build_host_throttled_dispatcher(MAD, per_domain_cap: int, **kwargs):
    """Return a MemoryAdaptiveDispatcher subclass with per-host asyncio.Semaphore throttling."""

    class _HostThrottledDispatcher(MAD):
        def __init__(self, _cap: int, **kw):
            super().__init__(**kw)
            self._per_domain_cap = _cap
            self._host_sems: Dict[str, asyncio.Semaphore] = {}
            self._host_sem_lock = asyncio.Lock()

        async def _get_host_sem(self, host: str) -> asyncio.Semaphore:
            async with self._host_sem_lock:
                if host not in self._host_sems:
                    self._host_sems[host] = asyncio.Semaphore(self._per_domain_cap)
                return self._host_sems[host]

        async def crawl_url(self, url, config, task_id=None, **kw):
            host = host_of(url)
            sem = await self._get_host_sem(host)
            async with sem:
                await asyncio.sleep(random.uniform(0.3, 1.2))
                if task_id is not None:
                    return await super().crawl_url(url, config, task_id, **kw)
                return await super().crawl_url(url, config, **kw)

    return _HostThrottledDispatcher(_cap=per_domain_cap, **kwargs)


def _build_dispatcher(imports: Dict[str, Any], max_concurrent: int,
                      per_domain_cap: int = 2) -> Any:
    MAD = imports["MemoryAdaptiveDispatcher"]
    RateLimiter = imports.get("RateLimiter")

    # Probe which rate-limiter kwarg the installed crawl4ai accepts.
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

    rate_limiter = None
    kwargs: Dict[str, Any] = {
        "memory_threshold_percent": 75.0,
        "max_session_permit": max_concurrent,
    }
    if RateLimiter is not None and rl_kwarg is not None:
        try:
            rate_limiter = RateLimiter(
                base_delay=(0.5, 1.5),
                max_delay=10.0,
                max_retries=2,
                rate_limit_codes=[429, 503],
            )
            kwargs[rl_kwarg] = rate_limiter
        except Exception as exc:
            print(f"[warn] RateLimiter init failed, continuing without: {exc}", file=sys.stderr)

    try:
        dispatcher = _build_host_throttled_dispatcher(MAD, per_domain_cap, **kwargs)
    except Exception as exc:
        print(f"[warn] _HostThrottledDispatcher subclass failed ({exc}), falling back to MAD",
              file=sys.stderr)
        dispatcher = MAD(**kwargs)

    return dispatcher, rate_limiter


# --- Flat mode -------------------------------------------------------------------

def _staging_append(index_fh: Any, record: Dict[str, Any]) -> None:
    if index_fh is not None:
        index_fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        index_fh.flush()


def _write_staged_md(staging_dir: Path, task_id: str, url: str,
                     markdown: str, meta: Dict[str, Any]) -> str:
    """Write a staged evidence file; return its path string."""
    staging_dir.mkdir(parents=True, exist_ok=True)
    path = staging_dir / f"{task_id}.md"
    content_hash = hashlib.sha256(markdown.encode("utf-8", errors="replace")).hexdigest()
    header_lines = ["---"]
    for k, v in meta.items():
        header_lines.append(f"{k}: {json.dumps(v)}")
    header_lines.append("---\n")
    path.write_text("\n".join(header_lines) + "\n" + markdown, encoding="utf-8")
    return content_hash


async def run_flat(
    urls: List[str],
    max_concurrent: int,
    per_domain_cap: int,
    cache_mode: str,
    backoff_log: Optional[str],
    performance_mode: str = "balanced",
    output_dir: Optional[str] = None,
    min_dwell_seconds: float = 30.0,
) -> None:
    imports = await _build_crawler_imports()
    AsyncWebCrawler = imports["AsyncWebCrawler"]
    BrowserConfig = imports["BrowserConfig"]
    CrawlerRunConfig = imports["CrawlerRunConfig"]
    CacheMode = imports["CacheMode"]

    cm = CacheMode.BYPASS if cache_mode == "bypass" else CacheMode.ENABLED

    interleaved = interleave_by_host(urls)
    index_by_url: Dict[str, int] = {}
    url_to_task_id: Dict[str, str] = {}
    for i, u in enumerate(interleaved):
        index_by_url.setdefault(u, i)
        url_to_task_id.setdefault(u, uuid.uuid4().hex)

    # Pick a batch-level header profile (A4)
    profile_tuple, profile_id = _pick_header_profile(performance_mode, "batch")
    ua, accept_lang = profile_tuple
    print(f"[info] header_profile_id={profile_id} performance_mode={performance_mode}",
          file=sys.stderr)

    run_cfg = CrawlerRunConfig(
        cache_mode=cm,
        stream=True,
        remove_overlay_elements=True,
        page_timeout=30000,
        screenshot=False,
    )

    dispatcher, rate_limiter = _build_dispatcher(imports, max_concurrent, per_domain_cap)
    monitor = BackoffMonitor(backoff_log, dispatcher=dispatcher, rate_limiter=rate_limiter,
                             min_dwell_seconds=min_dwell_seconds)

    browser_cfg = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        verbose=False,
        user_agent=ua,
        headers={"Accept-Language": accept_lang},
    )

    # A2: staging setup
    staging_dir: Optional[Path] = None
    staging_index_fh = None
    task_id_to_idx: Dict[str, int] = {v: index_by_url[k] for k, v in url_to_task_id.items()}
    staged_files: Dict[int, str] = {}      # input_index -> staged .md path
    staged_hashes: Dict[str, str] = {}     # task_id -> content_hash

    if output_dir:
        staging_dir = Path(output_dir) / "_staging"
        staging_dir.mkdir(parents=True, exist_ok=True)
        staging_index_path = staging_dir / "staging_index.jsonl"
        # Resume: read prior staging index and apply refuse-to-reuse conditions
        _resume_entries, _resume_rejects = load_staging_index(staging_index_path)
        print(f"[info] RESUME_LOADED entries={len(_resume_entries)} rejects={len(_resume_rejects)}", file=sys.stderr)
        for _r in _resume_rejects:
            print(f"[warn] RESUME_REFETCH task_id={_r.task_id} url={_r.url} reason={_r.reason}", file=sys.stderr)
        staging_index_fh = open(staging_index_path, "a", encoding="utf-8")

    # Emit "started" records for all URLs upfront
    if staging_index_fh is not None:
        for u in interleaved:
            _staging_append(staging_index_fh, {
                "task_id": url_to_task_id[u],
                "url": u,
                "input_index": index_by_url[u],
                "started_at": datetime.now(timezone.utc).isoformat(),
                "status": "started",
            })

    buffer: Dict[int, Dict[str, Any]] = {}
    seen_urls: set = set()

    def _make_failure_record(i: int, u: str, error: str) -> Dict[str, Any]:
        return {
            "input_index": i, "seed_index": None, "seed_url": None,
            "url": u, "final_url": u, "title": "", "markdown": "",
            "metadata": {}, "links": {"internal": [], "external": []},
            "depth": 0, "success": False, "error": error,
            "classification": "failure", "body_length": 0,
            "heading_count": 0, "content_density": 0.0, "soft_fail_reason": None,
            "header_profile_id": profile_id, "adaptive_backoff_active_at_fetch": False,
        }

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
                        idx = len(interleaved) + len(buffer)
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    record = _result_to_record(result, input_index=idx)
                    record["header_profile_id"] = profile_id
                    record["adaptive_backoff_active_at_fetch"] = (
                        monitor._event_count > 0 and not monitor._locked
                    )
                    # A4: flat mode has no per-URL seed concept; Referer is not injected
                    record["referer_injected"] = False
                    buffer[idx] = record

                    h = host_of(url)
                    resp_hdrs = getattr(result, "response_headers", None) or {}
                    monitor.record(
                        success=record["success"],
                        status_code=getattr(result, "status_code", None),
                        host=h,
                        response_headers=resp_hdrs,
                    )

                    # A2: staged write immediately (defeats in-memory buffer on crash)
                    if staging_dir is not None and record["success"]:
                        task_id = url_to_task_id.get(url, uuid.uuid4().hex)
                        meta = {
                            "source": url,
                            "collected_at": datetime.now(timezone.utc).isoformat(),
                            "header_profile_id": profile_id,
                            "quality_class": record.get("classification", "unknown"),
                            "adaptive_backoff_active_at_fetch": record["adaptive_backoff_active_at_fetch"],
                        }
                        content_hash = _write_staged_md(
                            staging_dir, task_id, url, record.get("markdown", ""), meta
                        )
                        staged_files[idx] = str(staging_dir / f"{task_id}.md")
                        staged_hashes[task_id] = content_hash
                        _staging_append(staging_index_fh, {
                            "task_id": task_id, "url": url, "input_index": idx,
                            "status": "finished", "content_hash": content_hash,
                            "finished_at": datetime.now(timezone.utc).isoformat(),
                        })

            except Exception as exc:
                print(f"[error] arun_many failed: {type(exc).__name__}: {exc}", file=sys.stderr)
                for i, u in enumerate(interleaved):
                    if i not in buffer:
                        buffer[i] = _make_failure_record(i, u, f"{type(exc).__name__}: {exc}")

        # Fill in URLs that never produced a result
        for i, u in enumerate(interleaved):
            if i not in buffer:
                buffer[i] = _make_failure_record(i, u, "no_result_from_dispatcher")

        # A2: post-dispatcher rename staged files to canonical NNN-slug.md
        if staging_dir is not None and output_dir:
            evidence_dir = Path(output_dir)
            evidence_dir.mkdir(parents=True, exist_ok=True)
            for idx_key in sorted(staged_files.keys()):
                staged_path = Path(staged_files[idx_key])
                url = interleaved[idx_key] if idx_key < len(interleaved) else ""
                slug = _crawl_slug(url)
                final_name = f"{idx_key:03d}-{slug}.md"
                final_path = evidence_dir / final_name
                try:
                    staged_path.rename(final_path)
                    task_id = url_to_task_id.get(url, "")
                    _staging_append(staging_index_fh, {
                        "task_id": task_id, "url": url, "input_index": idx_key,
                        "status": "renamed", "final_path": str(final_path),
                        "renamed_at": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as exc:
                    print(f"[warn] rename staged file failed: {exc}", file=sys.stderr)

        # QUAL-05: canonical emission order
        for i in sorted(buffer.keys()):
            _emit(buffer[i])
    finally:
        monitor.close()
        if staging_index_fh is not None:
            try:
                staging_index_fh.close()
            except Exception:
                pass


# --- Deep mode -------------------------------------------------------------------

async def run_deep(
    seeds: List[str],
    strategy: str,
    max_pages_per_seed: int,
    max_concurrent: int,
    cache_mode: str,
    backoff_log: Optional[str],
    performance_mode: str = "balanced",
    min_dwell_seconds: float = 30.0,
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

    # Shared per-host semaphore table for seeds (A1 for deep mode)
    _host_sems: Dict[str, asyncio.Semaphore] = {}
    _host_sem_lock = asyncio.Lock()

    async def _get_seed_host_sem(url: str) -> asyncio.Semaphore:
        h = host_of(url)
        async with _host_sem_lock:
            if h not in _host_sems:
                _host_sems[h] = asyncio.Semaphore(max_concurrent)
            return _host_sems[h]

    seed_sem = asyncio.Semaphore(max_concurrent)
    input_counter = {"n": 0}
    counter_lock = asyncio.Lock()

    _, rate_limiter = _build_dispatcher(imports, max_concurrent)
    monitor = BackoffMonitor(backoff_log, rate_limiter=rate_limiter,
                             min_dwell_seconds=min_dwell_seconds)

    profile_tuple, profile_id = _pick_header_profile(performance_mode, "batch")
    ua, accept_lang = profile_tuple
    print(f"[info] header_profile_id={profile_id} performance_mode={performance_mode}",
          file=sys.stderr)

    try:
        async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            viewport_width=1280,
            viewport_height=800,
            verbose=False,
            user_agent=ua,
            headers={"Accept-Language": accept_lang},
        )) as crawler:
            async def _run_seed(seed_index: int, seed_url: str) -> None:
                host_sem = await _get_seed_host_sem(seed_url)
                async with seed_sem, host_sem:
                    await asyncio.sleep(random.uniform(0.3, 1.2))
                    # A4: inject same-site Referer — all deep-crawl pages are same-site
                    # (include_external=False), so seed_url is always a valid Referer.
                    seed_headers = {"Accept-Language": accept_lang, "Referer": seed_url}
                    seed_browser_cfg = BrowserConfig(
                        headless=True,
                        viewport_width=1280,
                        viewport_height=800,
                        verbose=False,
                        user_agent=ua,
                        headers=seed_headers,
                    )
                    run_cfg = CrawlerRunConfig(
                        cache_mode=cm,
                        deep_crawl_strategy=make_strategy(),
                        remove_overlay_elements=True,
                        page_timeout=30000,
                        screenshot=False,
                    )
                    try:
                        results = await crawler.arun(url=seed_url, config=run_cfg,
                                                     browser_config=seed_browser_cfg)
                        iterable = results if isinstance(results, list) else [results]
                        for res in iterable:
                            async with counter_lock:
                                idx = input_counter["n"]
                                input_counter["n"] += 1
                            res_url = getattr(res, "url", seed_url) or seed_url
                            record = _result_to_record(
                                res,
                                input_index=idx,
                                seed_index=seed_index,
                                seed_url=seed_url,
                            )
                            # referer_injected: True only when Referer was in headers
                            # AND the result URL is actually same-hostname as seed
                            record["referer_injected"] = (
                                _same_site_referer(seed_url, res_url) is not None
                            )
                            record["header_profile_id"] = profile_id
                            _emit(record)
                            monitor.record(
                                success=record["success"],
                                status_code=getattr(res, "status_code", None),
                                host=host_of(res_url),
                                response_headers=getattr(res, "response_headers", None) or {},
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
                            "referer_injected": False,
                            "header_profile_id": profile_id,
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
    flat.add_argument("--output-dir", default=None,
                      help="Write staged evidence .md files here; enables staging_index.jsonl.")
    flat.add_argument("--performance-mode", choices=["conservative", "balanced", "aggressive"],
                      default=None, help="Crawl aggressiveness (overrides runtime-profile).")

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
    deep.add_argument("--performance-mode", choices=["conservative", "balanced", "aggressive"],
                      default=None, help="Crawl aggressiveness (overrides runtime-profile).")
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

    perf_mode = (getattr(args, "performance_mode", None)
                 or profile.get("performance_mode_used", "balanced")
                 or "balanced")

    min_dwell = float(profile.get("backoff_min_dwell_seconds", 30.0))

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
        asyncio.run(run_flat(urls, max_c, cap, args.cache, args.backoff_log,
                             performance_mode=perf_mode,
                             output_dir=getattr(args, "output_dir", None),
                             min_dwell_seconds=min_dwell))
    else:
        seeds = load_lines(args.seeds_file)
        if not seeds:
            print("no seeds", file=sys.stderr)
            return 1
        max_c, _ = _resolve_concurrency(
            args.max_concurrent, None, profile, defaults=(3, 2)
        )
        if args.fixture_dir:
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
                performance_mode=perf_mode,
                min_dwell_seconds=min_dwell,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
