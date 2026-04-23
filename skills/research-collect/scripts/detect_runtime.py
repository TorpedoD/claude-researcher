"""
detect_runtime.py — Hardware/OS/runtime profiler for the research pipeline.

Called once per collection run. Detects machine capabilities and computes
recommended concurrency knobs. Emits a JSON object to stdout.

Usage:
    python detect_runtime.py                               # JSON to stdout (default)
    python detect_runtime.py --performance-mode aggressive # override performance_mode
    python detect_runtime.py --summary                     # human-readable one-liner
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

SUBPROCESS_TIMEOUT = 15  # seconds

CEILINGS = {
    ("small",  "conservative"): dict(max_concurrent=4,  per_domain_cap=1, docling_parallelism=2, docling_threads=1),
    ("small",  "balanced"):     dict(max_concurrent=6,  per_domain_cap=2, docling_parallelism=3, docling_threads=1),
    ("small",  "aggressive"):   dict(max_concurrent=8,  per_domain_cap=2, docling_parallelism=4, docling_threads=2),
    ("mid",    "conservative"): dict(max_concurrent=8,  per_domain_cap=2, docling_parallelism=3, docling_threads=1),
    ("mid",    "balanced"):     dict(max_concurrent=12, per_domain_cap=2, docling_parallelism=4, docling_threads=2),
    ("mid",    "aggressive"):   dict(max_concurrent=16, per_domain_cap=3, docling_parallelism=6, docling_threads=2),
    ("large",  "conservative"): dict(max_concurrent=10, per_domain_cap=2, docling_parallelism=4, docling_threads=2),
    ("large",  "balanced"):     dict(max_concurrent=16, per_domain_cap=3, docling_parallelism=6, docling_threads=2),
    ("large",  "aggressive"):   dict(max_concurrent=24, per_domain_cap=3, docling_parallelism=8, docling_threads=2),
}


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], timeout: int = SUBPROCESS_TIMEOUT) -> str | None:
    """Run a command, return stripped stdout or None on any failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _sysctl(key: str) -> str | None:
    return _run(["sysctl", "-n", key])


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

def detect_platform() -> tuple[str, str]:
    """Return (platform_name, arch)."""
    sys_name = platform.system().lower()
    if sys_name == "darwin":
        plat = "macos"
    elif sys_name == "linux":
        plat = "linux"
    elif sys_name == "windows":
        plat = "windows"
    else:
        plat = sys_name
    arch = platform.machine().lower()
    return plat, arch


def detect_apple_silicon(plat: str, arch: str) -> bool:
    if plat != "macos":
        return False
    # Verify via sysctl
    val = _sysctl("hw.optional.arm64")
    if val is not None:
        return val.strip() == "1"
    return arch == "arm64"


# ---------------------------------------------------------------------------
# CPU
# ---------------------------------------------------------------------------

def detect_cpu(plat: str) -> tuple[int, int]:
    """Return (cpu_cores, cpu_performance)."""
    if plat == "macos":
        cores_str = _sysctl("hw.logicalcpu")
        perf_str = _sysctl("hw.perflevel0.logicalcpu")
        try:
            cpu_cores = int(cores_str) if cores_str else 0
        except ValueError:
            cpu_cores = 0
        try:
            cpu_performance = int(perf_str) if perf_str else 0
        except ValueError:
            cpu_performance = 0
        if cpu_cores == 0:
            cpu_cores = os.cpu_count() or 1
        if cpu_performance == 0:
            cpu_performance = cpu_cores
    else:
        cpu_cores = os.cpu_count() or 1
        cpu_performance = cpu_cores
    return cpu_cores, cpu_performance


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

def detect_memory(plat: str) -> int:
    """Return memory in GB (integer)."""
    if plat == "macos":
        val = _sysctl("hw.memsize")
        if val:
            try:
                return int(int(val) / 1e9)
            except ValueError:
                pass
    elif plat == "linux":
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return int(kb / 1e6)
        except Exception:
            pass
    else:
        # Windows — try psutil gracefully
        try:
            import psutil  # type: ignore
            return int(psutil.virtual_memory().total / 1e9)
        except Exception:
            pass
    return 0


# ---------------------------------------------------------------------------
# MPS / CUDA
# ---------------------------------------------------------------------------

def detect_mps(apple_silicon: bool, plat: str, crawl4ai_python: str | None) -> tuple[bool, str | None]:
    if not (apple_silicon and plat == "macos"):
        return False, None
    py = crawl4ai_python or "python3"
    val = _run([py, "-c", "import torch; print(torch.backends.mps.is_available())"])
    if val is not None:
        return val.lower() == "true", None
    # torch not available or import failed — safe default is False
    return False, "torch not importable or MPS check failed on this machine"


def detect_cuda(crawl4ai_python: str | None) -> bool:
    py = crawl4ai_python or "python3"
    val = _run([py, "-c", "import torch; print(torch.cuda.is_available())"])
    if val is not None:
        return val.lower() == "true"
    return False


# ---------------------------------------------------------------------------
# File descriptor limits
# ---------------------------------------------------------------------------

def detect_fd_limits() -> tuple[int, int]:
    """Return (fd_soft_limit, fd_target)."""
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        if hard > 0:
            fd_target = min(4096, hard)
        else:
            fd_target = 4096
        return soft, fd_target
    except Exception:
        return 256, 4096


# ---------------------------------------------------------------------------
# Tier
# ---------------------------------------------------------------------------

def compute_tier(cpu_cores: int, memory_gb: int) -> str:
    small = cpu_cores <= 6 or memory_gb <= 16
    large = cpu_cores >= 13 and memory_gb >= 48
    if small:
        return "small"
    if large:
        return "large"
    return "mid"


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

def _get_version(python_path: str | None, import_expr: str) -> str | None:
    if not python_path:
        return None
    return _run([python_path, "-c", import_expr])


def _get_python_version(python_path: str | None) -> str | None:
    if not python_path:
        return None
    val = _run([python_path, "--version"])
    if val:
        # "Python 3.14.3" → "3.14.3"
        parts = val.split()
        return parts[1] if len(parts) >= 2 else val
    return None


def detect_versions(crawl4ai_python: str | None, docling_python: str | None) -> dict:
    crawl4ai_ver = _get_version(
        crawl4ai_python,
        "from crawl4ai.__version__ import __version__; print(__version__)",
    ) or _get_version(crawl4ai_python, "import crawl4ai; print(crawl4ai.__version__)")
    docling_ver = _get_version(
        docling_python,
        "from docling._version import __version__; print(__version__)",
    ) or _get_version(docling_python, "import docling; print(docling.__version__)")
    py_crawl4ai = _get_python_version(crawl4ai_python)
    py_docling = _get_python_version(docling_python)

    # playwright version — attempt via crawl4ai python
    playwright_ver = _get_version(crawl4ai_python, "import playwright; print(playwright.__version__)")

    os_detail = platform.platform()
    os_version = f"{platform.system()} {platform.version()}"
    # Nicer macOS version
    if platform.system() == "Darwin":
        mac_ver = platform.mac_ver()[0]
        if mac_ver:
            os_version = f"macOS {mac_ver}"

    platform_detail = f"{platform.system()} {platform.release()} {platform.machine()}"

    return {
        "crawl4ai": crawl4ai_ver,
        "docling": docling_ver,
        "playwright": playwright_ver,
        "chromium": None,  # too complex to detect reliably
        "python_crawl4ai": py_crawl4ai,
        "python_docling": py_docling,
        "os_version": os_version,
        "platform_detail": platform_detail,
    }


# ---------------------------------------------------------------------------
# resolve_env bridge
# ---------------------------------------------------------------------------

def call_resolve_env() -> dict:
    scripts_dir = Path(__file__).parent
    resolve_env_path = scripts_dir / "resolve_env.py"
    result = _run([sys.executable, str(resolve_env_path)])
    if result:
        try:
            data = json.loads(result)
            return {
                "crawl4ai_python": data.get("crawl4ai_python"),
                "docling_python": data.get("docling_python"),
                "crwl_cli": data.get("crwl_cli"),
                "docling_cli": data.get("docling_cli"),
                "playwright_ok": data.get("playwright_ok", False),
            }
        except json.JSONDecodeError:
            pass
    return {
        "crawl4ai_python": None,
        "docling_python": None,
        "crwl_cli": None,
        "docling_cli": None,
        "playwright_ok": False,
    }


# ---------------------------------------------------------------------------
# Main detection
# ---------------------------------------------------------------------------

def detect_runtime(performance_mode_override: str | None = None) -> dict:
    plat, arch = detect_platform()
    apple_silicon = detect_apple_silicon(plat, arch)
    cpu_cores, cpu_performance = detect_cpu(plat)
    memory_gb = detect_memory(plat)
    fd_soft, fd_target = detect_fd_limits()
    tier = compute_tier(cpu_cores, memory_gb)

    # Performance mode — env var > CLI arg > default
    perf_env = os.environ.get("RESEARCH_PERF_MODE", "").strip().lower()
    valid_modes = {"conservative", "balanced", "aggressive"}
    if perf_env in valid_modes:
        performance_mode = perf_env
    elif performance_mode_override and performance_mode_override.lower() in valid_modes:
        performance_mode = performance_mode_override.lower()
    else:
        performance_mode = "balanced"

    # Tools resolution
    tools = call_resolve_env()
    crawl4ai_python = tools["crawl4ai_python"]
    docling_python = tools["docling_python"]

    mps_available, mps_detection_error = detect_mps(apple_silicon, plat, crawl4ai_python)
    cuda_available = detect_cuda(crawl4ai_python)

    # docling device
    if apple_silicon and mps_available:
        docling_device = "mps"
    elif cuda_available:
        docling_device = "cuda"
    else:
        docling_device = "cpu"

    # Recommended block
    ceiling = CEILINGS.get((tier, performance_mode), CEILINGS[("mid", "balanced")])
    recommended = dict(ceiling)
    recommended["docling_device"] = docling_device

    versions = detect_versions(crawl4ai_python, docling_python)

    return {
        "platform": plat,
        "arch": arch,
        "apple_silicon": apple_silicon,
        "cpu_cores": cpu_cores,
        "cpu_performance": cpu_performance,
        "memory_gb": memory_gb,
        "mps_available": mps_available,
        "cuda_available": cuda_available,
        "mps_detection_error": mps_detection_error,
        "fd_soft_limit": fd_soft,
        "fd_target": fd_target,
        "tier": tier,
        "performance_mode": performance_mode,
        "tools": tools,
        "versions": versions,
        "recommended": recommended,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _summary_line(data: dict) -> str:
    r = data["recommended"]
    return (
        f"tier={data['tier']} | platform={data['platform']} arch={data['arch']} | "
        f"cores={data['cpu_cores']} (perf={data['cpu_performance']}) | "
        f"memory={data['memory_gb']}GB | "
        f"apple_silicon={data['apple_silicon']} mps={data['mps_available']} cuda={data['cuda_available']} | "
        f"mode={data['performance_mode']} | "
        f"max_concurrent={r['max_concurrent']} per_domain={r['per_domain_cap']} "
        f"docling_par={r['docling_parallelism']} device={r['docling_device']}"
    )


def main() -> None:
    args = sys.argv[1:]
    summary_mode = "--summary" in args
    perf_override: str | None = None

    for i, arg in enumerate(args):
        if arg == "--performance-mode" and i + 1 < len(args):
            perf_override = args[i + 1]

    data = detect_runtime(performance_mode_override=perf_override)

    if summary_mode:
        print(_summary_line(data))
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
