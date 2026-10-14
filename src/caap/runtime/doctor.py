"""Read-only resource inventory; observations never authorize GPU allocation."""

import argparse
import csv
from datetime import datetime, timezone
from importlib import metadata
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile


DEPENDENCIES = ("torch", "torchvision", "numpy", "Pillow", "pandas", "scikit-learn", "matplotlib", "tqdm", "PyYAML")
SLURM_KEYS = (
    "SLURM_JOB_ID", "SLURM_STEP_ID", "SLURM_JOB_GPUS", "SLURM_STEP_GPUS",
    "SLURM_GPUS_ON_NODE", "SLURM_GPUS_PER_NODE", "SLURM_GPUS_PER_TASK",
    "SLURM_CPUS_ON_NODE", "SLURM_CPUS_PER_TASK", "SLURM_MEM_PER_NODE", "SLURM_MEM_PER_CPU",
)
LIMITATIONS = [
    "Inventory only: free VRAM is not allocation permission; no scheduler or training is started.",
    "Visibility and Slurm variables are declarations, not verified allocation authorization.",
    "CUDA logical indices may differ from nvidia-smi physical indices; correlate UUIDs, not indices.",
    "Parent GPU memory is not the memory available to a MIG instance; MIG availability is not inferred.",
    "Host CPU/RAM/disk inventory may exceed container, cgroup, quota or job allocation limits.",
]
TORCH_PROBE = """
import json
try:
    import torch
except Exception as exc:
    result = {"status": "import_error", "error_type": type(exc).__name__}
else:
    try:
        available = torch.cuda.is_available()
        devices = []
        if available:
            for index in range(torch.cuda.device_count()):
                properties = torch.cuda.get_device_properties(index)
                devices.append({"logical_index": index, "name": properties.name,
                                "total_memory_bytes": properties.total_memory,
                                "uuid": str(getattr(properties, "uuid", "")) or None})
        result = {"status": "ok", "version": str(torch.__version__),
                  "cuda_available": available, "devices": devices,
                  "allocation_authorized": False}
    except Exception as exc:
        result = {"status": "error", "error_type": type(exc).__name__}
print("CAAP_TORCH_PROBE=" + json.dumps(result))
"""


def _run(command, timeout):
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return {"status": "not_found"}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "timeout_seconds": timeout}
    except (OSError, UnicodeError) as exc:
        return {"status": "error", "error_type": type(exc).__name__}
    if completed.returncode != 0:
        return {"status": "error", "returncode": completed.returncode}
    return {"status": "ok", "stdout": completed.stdout}


def parse_gpu_csv(text):
    """Parse the fixed query schema without turning unavailable metrics into zero."""
    devices = []
    unavailable = {"n/a", "[n/a]", "not supported", "[not supported]", "[not available]"}
    metric_names = ("memory_total_mib", "memory_used_mib", "memory_free_mib", "utilization_gpu_percent")
    try:
        for row in csv.reader(io.StringIO(text), skipinitialspace=True, strict=True):
            if not row:
                continue
            if len(row) != 8:
                raise ValueError("expected eight columns")
            uuid, index, name, *tail = [value.strip() for value in row]
            if not uuid.startswith("GPU-") or not uuid[4:] or not index.isdigit() or not name or not tail[-1]:
                raise ValueError("invalid GPU identity")
            device = {"uuid": uuid, "index": int(index), "name": name, "driver_version": tail[-1], "metric_status": {}}
            for key, raw in zip(metric_names, tail[:-1]):
                if raw.lower() in unavailable:
                    device[key] = None
                    device["metric_status"][key] = "unavailable"
                else:
                    value = float(raw)
                    if not math.isfinite(value) or value < 0 or (key == "utilization_gpu_percent" and value > 100):
                        raise ValueError("invalid metric")
                    device[key] = value
                    device["metric_status"][key] = "ok"
            if any(other["uuid"] == uuid or other["index"] == int(index) for other in devices):
                raise ValueError("duplicate GPU identity")
            devices.append(device)
    except (csv.Error, ValueError, TypeError):
        return {"status": "parse_error", "devices": None, "device_count": None}
    partial = any("unavailable" in item["metric_status"].values() for item in devices)
    return {"status": "partial" if partial else ("ok" if devices else "no_devices"),
            "devices": devices, "device_count": len(devices)}


def parse_mig_listing(text):
    """Keep MIG UUIDs attached to their parent without inferring allocatable memory."""
    devices = []
    parent = None
    gpu_pattern = re.compile(r"GPU \d+: .+ \(UUID: (GPU-[^\s()]+)\)")
    mig_pattern = re.compile(r"MIG (.+?) Device (\d+): \(UUID: (MIG-[^\s()]+)\)")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        gpu = gpu_pattern.fullmatch(line)
        if gpu:
            parent = gpu.group(1)
            continue
        mig = mig_pattern.fullmatch(line)
        if mig and parent and not any(item["uuid"] == mig.group(3) for item in devices):
            devices.append({"parent_uuid": parent, "profile": mig.group(1),
                            "device_index": int(mig.group(2)), "uuid": mig.group(3)})
        else:
            return {"status": "parse_error", "devices": None}
    return {"status": "ok", "devices": devices,
            "interpretation": "Listed instances only; absence does not prove MIG is disabled or allocatable."}


def _gpu(timeout):
    executable = shutil.which("nvidia-smi")
    if not executable:
        return {"status": "not_found", "devices": None, "device_count": None,
                "mig": {"status": "not_found", "devices": None}}
    query = _run([executable, "--query-gpu=uuid,index,name,memory.total,memory.used,memory.free,utilization.gpu,driver_version",
                  "--format=csv,noheader,nounits"], timeout)
    if query["status"] == "ok":
        result = parse_gpu_csv(query["stdout"])
    else:
        result = dict(query, devices=None, device_count=None)
    listing = _run([executable, "-L"], timeout)
    result["mig"] = parse_mig_listing(listing["stdout"]) if listing["status"] == "ok" else dict(listing, devices=None)
    return result


def _cpu():
    count = os.cpu_count()
    result = {"status": "ok" if count is not None else "unavailable", "logical_count": count,
              "architecture": platform.machine(), "affinity_logical_count": None, "affinity_status": "unsupported"}
    if hasattr(os, "sched_getaffinity"):
        try:
            result.update(affinity_logical_count=len(os.sched_getaffinity(0)), affinity_status="ok")
        except OSError:
            result["affinity_status"] = "error"
    return result


def _memory(timeout):
    result = {"status": "unavailable", "total_bytes": None, "available_bytes": None,
              "available_status": "unavailable", "scope": "host_not_allocation"}
    if sys.platform.startswith("linux"):
        try:
            values = {}
            for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
                match = re.fullmatch(r"(MemTotal|MemAvailable):\s+(\d+) kB", line)
                if match:
                    values[match.group(1)] = int(match.group(2)) * 1024
            if values.get("MemTotal", 0) <= 0:
                raise ValueError("missing total")
            result.update(status="partial", total_bytes=values["MemTotal"], source="/proc/meminfo")
            if "MemAvailable" in values:
                result.update(status="ok", available_bytes=values["MemAvailable"], available_status="ok")
            return result
        except (OSError, ValueError, UnicodeError):
            result["status"] = "error"
    try:
        total = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
        if total > 0:
            result.update(status="partial", total_bytes=total, source="sysconf")
            return result
    except (AttributeError, OSError, ValueError):
        pass
    if sys.platform == "darwin":
        query = _run(["/usr/sbin/sysctl", "-n", "hw.memsize"], timeout)
        if query["status"] == "ok":
            try:
                total = int(query["stdout"].strip())
                if total <= 0:
                    raise ValueError("invalid total")
                result.update(status="partial", total_bytes=total, source="sysctl")
            except ValueError:
                result["status"] = "parse_error"
        else:
            result["status"] = query["status"]
    return result


def _disk():
    try:
        path = Path.cwd()
        usage = shutil.disk_usage(path)
        return {"status": "ok", "path": str(path), "total_bytes": usage.total,
                "used_bytes": usage.used, "free_bytes": usage.free, "scope": "filesystem_not_quota"}
    except OSError as exc:
        return {"status": "error", "total_bytes": None, "used_bytes": None, "free_bytes": None,
                "error_type": type(exc).__name__}


def _dependencies():
    result = {}
    for name in DEPENDENCIES:
        try:
            result[name] = {"status": "ok", "version": metadata.version(name)}
        except metadata.PackageNotFoundError:
            result[name] = {"status": "not_installed", "version": None}
        except Exception as exc:
            result[name] = {"status": "error", "version": None, "error_type": type(exc).__name__}
    return result


def probe_torch(timeout):
    query = _run([sys.executable, "-I", "-c", TORCH_PROBE], timeout)
    if query["status"] != "ok":
        result = query
    else:
        try:
            lines = [line.removeprefix("CAAP_TORCH_PROBE=") for line in query["stdout"].splitlines()
                     if line.startswith("CAAP_TORCH_PROBE=")]
            result = json.loads(lines[-1])
            if not isinstance(result, dict) or result.get("status") not in {"ok", "import_error", "error"}:
                raise ValueError("invalid probe result")
        except (ValueError, IndexError):
            result = {"status": "parse_error"}
    result["scope"] = "isolated_no_user_site_no_pythonpath"
    result["interpretation"] = ("The -I subprocess excludes user site and PYTHONPATH; this is not the current interpreter "
                                "import environment used for dependency metadata. An import failure does not prove "
                                "torch is absent from that environment.")
    return result


def collect_report(timeout=10.0, probe_torch_enabled=False):
    return {
        "schema_version": "caap.doctor.v1", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inventory_only": True, "allocation_authorized": False,
        "interpreter": {"status": "ok", "version": platform.python_version(),
                        "implementation": platform.python_implementation(), "executable": sys.executable},
        "cpu": _cpu(), "ram": _memory(timeout), "disk": _disk(), "dependencies": _dependencies(),
        "gpu": _gpu(timeout),
        "visibility": {key: os.environ.get(key) for key in ("CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES")},
        "allocation_declarations": {key: os.environ[key] for key in SLURM_KEYS if key in os.environ},
        "torch_probe": probe_torch(timeout) if probe_torch_enabled else {"status": "not_requested"},
        "limitations": list(LIMITATIONS),
    }


def write_report(path, report):
    """Atomically publish a complete file, refusing existing targets even in a race."""
    path = Path(path).expanduser()
    package = Path(__file__).resolve().parents[1]
    resolved = path.resolve()
    if resolved == package or package in resolved.parents:
        raise ValueError("report output must not be inside the caap package")
    if os.path.lexists(path):
        raise FileExistsError("report output already exists")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".caap-report-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        # 硬链接提供原子的“不存在才创建”；不支持硬链接的文件系统报错，不降级为可能覆盖的 rename。
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink()


def _positive_timeout(value):
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a positive finite number") from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be a positive finite number")
    return timeout


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only resource inventory, never GPU allocation authorization.")
    parser.add_argument("--output", type=Path, help="atomically create a new JSON report outside the package; default stdout")
    parser.add_argument("--probe-torch", action="store_true", help="opt in to a bounded isolated torch import/device probe")
    parser.add_argument("--timeout", type=_positive_timeout, default=10.0, help="timeout in seconds for each external probe (default 10)")
    args = parser.parse_args(argv)
    report = collect_report(timeout=args.timeout, probe_torch_enabled=args.probe_torch)
    try:
        if args.output is not None:
            write_report(args.output, report)
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "output_error", "error_type": type(exc).__name__, "error": str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
