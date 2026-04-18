"""
resolve_env.py — Adaptive tool resolver for crawl4ai and docling.

Called once per collection run to discover the correct Python executable
for crawl4ai and docling. Emits a JSON object to stdout.

Usage:
    python resolve_env.py [--json]        # default: print JSON to stdout
    python resolve_env.py --check         # human-readable summary, exit 1 if crawl4ai not found
    python resolve_env.py --crawl4ai-only # just resolve crawl4ai; exit 0 if found, exit 1 if not
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


SUBPROCESS_TIMEOUT = 10  # seconds


def _validate_import(python_path: str, package: str) -> bool:
    """Return True if `python_path -c "import <package>"` exits 0."""
    try:
        result = subprocess.run(
            [python_path, "-c", f"import {package}; print('ok')"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_playwright(python_path: str) -> tuple[bool, str]:
    """Check playwright availability via subprocess."""
    try:
        result = subprocess.run(
            [python_path, "-c", "import playwright; print('ok')"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        ok = result.returncode == 0
        check_desc = f"subprocess: {python_path} -c \"import playwright; print('ok')\""
        return ok, check_desc
    except Exception as exc:
        return False, f"subprocess error: {exc}"


def _find_pipx_home() -> Path:
    """Discover PIPX_HOME via `pipx environment` or fall back to ~/.local/pipx."""
    try:
        result = subprocess.run(
            ["pipx", "environment", "--value", "PIPX_HOME"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        if result.returncode == 0:
            home = result.stdout.strip()
            if home:
                return Path(home)
    except Exception:
        pass
    return Path.home() / ".local" / "pipx"


def _pipx_python_candidates(pipx_home: Path) -> list[Path]:
    """Enumerate all bin/python3 executables under pipx venvs."""
    venvs_dir = pipx_home / "venvs"
    if not venvs_dir.is_dir():
        return []
    candidates = []
    for venv in sorted(venvs_dir.iterdir()):
        py = venv / "bin" / "python3"
        if py.is_file():
            candidates.append(py)
        # Windows fallback
        py_win = venv / "Scripts" / "python.exe"
        if py_win.is_file():
            candidates.append(py_win)
    return candidates


def resolve_env() -> dict:
    """Run the full resolution logic and return the result dict."""
    log: list[dict] = []
    crawl4ai_python: str | None = None
    docling_python: str | None = None

    # ------------------------------------------------------------------ #
    # Step 1: Env var overrides
    # ------------------------------------------------------------------ #
    for pkg, env_key in [("crawl4ai", "CRAWL4AI_PYTHON"), ("docling", "DOCLING_PYTHON")]:
        val = os.environ.get(env_key)
        if val:
            ok = _validate_import(val, pkg)
            log.append({"step": "env_var", "key": env_key, "path": val,
                         "result": "ok" if ok else "fail"})
            if ok:
                if pkg == "crawl4ai" and crawl4ai_python is None:
                    crawl4ai_python = val
                if pkg == "docling" and docling_python is None:
                    docling_python = val
        else:
            log.append({"step": "env_var", "key": env_key, "path": None, "result": "skip"})

    # ------------------------------------------------------------------ #
    # Step 2: pipx discovery
    # ------------------------------------------------------------------ #
    if crawl4ai_python is None or docling_python is None:
        pipx_home = _find_pipx_home()
        log.append({"step": "pipx_home", "key": "PIPX_HOME", "path": str(pipx_home), "result": "info"})
        candidates = _pipx_python_candidates(pipx_home)
        for py in candidates:
            py_str = str(py)
            for pkg, current in [("crawl4ai", crawl4ai_python), ("docling", docling_python)]:
                if current is not None:
                    continue
                ok = _validate_import(py_str, pkg)
                log.append({"step": "pipx", "key": pkg, "path": py_str,
                             "result": "ok" if ok else "fail"})
                if ok:
                    if pkg == "crawl4ai":
                        crawl4ai_python = py_str
                    else:
                        docling_python = py_str

    # ------------------------------------------------------------------ #
    # Step 3: Active / local virtualenvs
    # ------------------------------------------------------------------ #
    venv_candidates: list[str] = []
    if venv_env := os.environ.get("VIRTUAL_ENV"):
        venv_candidates.append(str(Path(venv_env) / "bin" / "python"))
    for rel in [".venv", "venv"]:
        p = Path(".") / rel / "bin" / "python"
        venv_candidates.append(str(p))
        p_win = Path(".") / rel / "Scripts" / "python.exe"
        venv_candidates.append(str(p_win))

    for py_str in venv_candidates:
        py = Path(py_str)
        if not py.is_file():
            continue
        for pkg, current in [("crawl4ai", crawl4ai_python), ("docling", docling_python)]:
            if current is not None:
                continue
            ok = _validate_import(py_str, pkg)
            log.append({"step": "virtualenv", "key": pkg, "path": py_str,
                         "result": "ok" if ok else "fail"})
            if ok:
                if pkg == "crawl4ai":
                    crawl4ai_python = py_str
                else:
                    docling_python = py_str

    # ------------------------------------------------------------------ #
    # Step 4: PATH CLIs
    # ------------------------------------------------------------------ #
    crwl_cli: str | None = shutil.which("crwl")
    docling_cli: str | None = shutil.which("docling")
    log.append({"step": "which_cli", "key": "crwl", "path": crwl_cli,
                 "result": "ok" if crwl_cli else "not_found"})
    log.append({"step": "which_cli", "key": "docling", "path": docling_cli,
                 "result": "ok" if docling_cli else "not_found"})

    # ------------------------------------------------------------------ #
    # Step 5: System python3 last resort
    # ------------------------------------------------------------------ #
    for pkg, current in [("crawl4ai", crawl4ai_python), ("docling", docling_python)]:
        if current is not None:
            continue
        sys_py = shutil.which("python3") or "python3"
        ok = _validate_import(sys_py, pkg)
        log.append({"step": "system_python3", "key": pkg, "path": sys_py,
                     "result": "ok" if ok else "fail"})
        if ok:
            if pkg == "crawl4ai":
                crawl4ai_python = sys_py
            else:
                docling_python = sys_py

    # ------------------------------------------------------------------ #
    # Playwright check (uses crawl4ai_python if found)
    # ------------------------------------------------------------------ #
    playwright_ok = False
    playwright_check = "skipped — crawl4ai_python not found"
    if crawl4ai_python:
        playwright_ok, playwright_check = _check_playwright(crawl4ai_python)

    return {
        "crawl4ai_python": crawl4ai_python,
        "docling_python": docling_python,
        "crwl_cli": crwl_cli,
        "docling_cli": docling_cli,
        "playwright_ok": playwright_ok,
        "playwright_check": playwright_check,
        "resolution_log": log,
    }


def _print_check(result: dict) -> int:
    """Print human-readable summary. Return exit code."""
    c4py = result["crawl4ai_python"]
    dpy = result["docling_python"]
    crwl = result["crwl_cli"]
    dcli = result["docling_cli"]
    pw = result["playwright_ok"]

    print("=== resolve_env: tool resolution summary ===")
    print(f"  crawl4ai python : {c4py or 'NOT FOUND'}")
    print(f"  docling  python : {dpy  or 'NOT FOUND'}")
    print(f"  crwl CLI        : {crwl or 'NOT FOUND'}")
    print(f"  docling CLI     : {dcli or 'NOT FOUND'}")
    print(f"  playwright      : {'ok' if pw else 'NOT FOUND'} ({result['playwright_check']})")
    print()
    if not c4py:
        print("ERROR: crawl4ai could not be resolved. Install via: pipx install crawl4ai")
        return 1
    print("OK: crawl4ai resolved.")
    return 0


def main() -> None:
    args = set(sys.argv[1:])
    crawl4ai_only = "--crawl4ai-only" in args
    check_mode = "--check" in args
    # default is --json

    result = resolve_env()

    if crawl4ai_only:
        sys.exit(0 if result["crawl4ai_python"] else 1)

    if check_mode:
        sys.exit(_print_check(result))

    # Default: JSON to stdout
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
