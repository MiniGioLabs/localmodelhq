"""Hardware detection service."""

import platform
import psutil
import subprocess
import json


async def detect() -> dict:
    """Detect hardware and return structured data."""
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "cpu": _detect_cpu(),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "gpu": await _detect_gpu(),
        "ollama_running": await _check_ollama(),
    }
    info["installed_models_count"] = await _installed_model_count() if info["ollama_running"] else 0
    return info


def _detect_cpu() -> dict:
    return {
        "name": platform.processor() or _cpu_from_lscpu(),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
    }


def _cpu_from_lscpu() -> str:
    try:
        r = subprocess.run(["lscpu"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if "Model name" in line:
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "Unknown CPU"


async def _detect_gpu() -> dict | None:
    """Try multiple methods to detect GPU."""
    system = platform.system()

    if system == "Linux":
        return _gpu_linux()
    elif system == "Darwin":
        return _gpu_macos()
    elif system == "Windows":
        return _gpu_windows()
    return None


def _gpu_linux() -> dict | None:
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split(",")
            vram = int(parts[1].strip().split()[0]) / 1024 if len(parts) > 1 else 0
            return {"name": parts[0].strip(), "vram_gb": vram}
    except Exception:
        pass
    return None


def _gpu_macos() -> dict | None:
    try:
        r = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        gpus = data.get("SPDisplaysDataType", [])
        if gpus:
            gpu = gpus[0]
            name = gpu.get("sppci_model", "Apple GPU")
            return {"name": name, "vram_gb": 0, "is_integrated": "Apple" in name}
    except Exception:
        pass
    return None


def _gpu_windows() -> dict | None:
    try:
        import wmi
        c = wmi.WMI()
        for gpu in c.Win32_VideoController():
            return {"name": gpu.Name, "vram_gb": 0}
    except Exception:
        pass
    return None


async def _check_ollama() -> bool:
    try:
        import httpx
        async with httpx.AsyncClient() as c:
            r = await c.get("http://localhost:11434/api/tags", timeout=3)
            return r.status_code == 200
    except Exception:
        return False


async def _installed_model_count() -> int:
    try:
        import httpx
        async with httpx.AsyncClient() as c:
            r = await c.get("http://localhost:11434/api/tags", timeout=3)
            return len(r.json().get("models", []))
    except Exception:
        return 0
