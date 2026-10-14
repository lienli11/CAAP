"""Tests for read-only, dependency-free resource inventory."""

import contextlib
import errno
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from caap.runtime import doctor


GPU_CSV = "GPU-aaaa, 0, NVIDIA A100, 40960, 1024, 39936, 2, 550.54\n"
GPU_LIST = "GPU 0: NVIDIA A100 (UUID: GPU-aaaa)\n  MIG 1g.5gb Device 0: (UUID: MIG-bbbb)\n"


class DoctorTests(unittest.TestCase):
    def symlink(self, path, target):
        try:
            path.symlink_to(target)
        except NotImplementedError:
            self.skipTest("Symbolic links are not supported on this platform.")
        except OSError as exc:
            if exc.errno in {errno.EPERM, errno.EACCES, errno.ENOSYS, errno.ENOTSUP} or getattr(exc, "winerror", None) == 1314:
                self.skipTest("Symbolic link creation is unavailable or not permitted.")
            raise

    def test_torch_probe_scope_is_explicit_for_all_outcomes(self):
        outcomes = [
            subprocess.CompletedProcess([], 0, 'CAAP_TORCH_PROBE={"status":"ok"}\n', ""),
            subprocess.CompletedProcess([], 0, 'CAAP_TORCH_PROBE={"status":"import_error"}\n', ""),
            subprocess.CompletedProcess([], 0, "invalid", ""),
            subprocess.CompletedProcess([], 9, "", ""),
            subprocess.TimeoutExpired("python", 1),
        ]
        for outcome in outcomes:
            with self.subTest(outcome=outcome), mock.patch.object(doctor.subprocess, "run") as run:
                if isinstance(outcome, Exception):
                    run.side_effect = outcome
                else:
                    run.return_value = outcome
                result = doctor.probe_torch(1)
                self.assertEqual(result["scope"], "isolated_no_user_site_no_pythonpath")
                self.assertIn("current interpreter", result["interpretation"])
                self.assertIn("-I", run.call_args.args[0])

    def test_import_and_help_do_not_import_torch_or_run_commands(self):
        with mock.patch.dict(sys.modules, {"torch": None}), mock.patch.object(
            doctor.subprocess, "run", side_effect=AssertionError("must not run")
        ), contextlib.redirect_stdout(io.StringIO()):
            importlib.reload(doctor)
            with self.assertRaises(SystemExit) as caught:
                doctor.main(["--help"])
        self.assertEqual(caught.exception.code, 0)

    def test_missing_gpu_tool_is_unknown_not_zero(self):
        with mock.patch.object(doctor.shutil, "which", return_value=None):
            result = doctor.collect_report()
        self.assertEqual(result["gpu"]["status"], "not_found")
        self.assertIsNone(result["gpu"]["device_count"])
        self.assertIsNone(result["gpu"]["devices"])
        self.assertTrue(result["inventory_only"])
        self.assertFalse(result["allocation_authorized"])
        self.assertEqual(result["torch_probe"]["status"], "not_requested")

    def test_gpu_uuid_mig_and_visibility_are_kept_separate(self):
        replies = [
            subprocess.CompletedProcess([], 0, GPU_CSV, ""),
            subprocess.CompletedProcess([], 0, GPU_LIST, ""),
        ]
        env = {
            "CUDA_VISIBLE_DEVICES": "MIG-bbbb",
            "NVIDIA_VISIBLE_DEVICES": "GPU-aaaa",
            "SLURM_JOB_GPUS": "0",
            "SLURM_JOB_ID": "123",
            "SECRET_PASSWORD": "must-not-leak",
        }
        with mock.patch.object(doctor.shutil, "which", return_value="/usr/bin/nvidia-smi"), mock.patch.object(
            doctor.subprocess, "run", side_effect=replies
        ), mock.patch.dict(os.environ, env, clear=True):
            result = doctor.collect_report()
        self.assertEqual(result["gpu"]["devices"][0]["uuid"], "GPU-aaaa")
        self.assertEqual(result["gpu"]["devices"][0]["memory_free_mib"], 39936)
        self.assertEqual(result["gpu"]["mig"]["devices"][0]["uuid"], "MIG-bbbb")
        self.assertEqual(result["gpu"]["mig"]["devices"][0]["parent_uuid"], "GPU-aaaa")
        self.assertEqual(result["visibility"]["CUDA_VISIBLE_DEVICES"], "MIG-bbbb")
        self.assertEqual(result["allocation_declarations"]["SLURM_JOB_GPUS"], "0")
        self.assertNotIn("must-not-leak", json.dumps(result))
        self.assertFalse(result["allocation_authorized"])

    def test_malformed_csv_never_reports_zero_resources(self):
        for text in ("bad,row\n", GPU_CSV.replace("39936", "oops"), GPU_CSV + GPU_CSV):
            with self.subTest(text=text):
                result = doctor.parse_gpu_csv(text)
                self.assertEqual(result["status"], "parse_error")
                self.assertIsNone(result["device_count"])
                self.assertIsNone(result["devices"])

    def test_unsupported_metrics_are_null_not_zero(self):
        result = doctor.parse_gpu_csv(GPU_CSV.replace("39936", "[N/A]").replace(", 2,", ", N/A,"))
        self.assertEqual(result["status"], "partial")
        self.assertIsNone(result["devices"][0]["memory_free_mib"])
        self.assertIsNone(result["devices"][0]["utilization_gpu_percent"])
        self.assertEqual(result["devices"][0]["metric_status"]["memory_free_mib"], "unavailable")

    def test_successful_empty_csv_explicitly_reports_no_devices(self):
        result = doctor.parse_gpu_csv("")
        self.assertEqual(result["status"], "no_devices")
        self.assertEqual(result["device_count"], 0)

    def test_timeout_and_command_failure_are_structured_and_sanitized(self):
        for failure, expected in (
            (subprocess.TimeoutExpired("nvidia-smi", 1, output="secret"), "timeout"),
            (subprocess.CompletedProcess([], 9, "secret", "private command"), "error"),
        ):
            with self.subTest(status=expected), mock.patch.object(
                doctor.shutil, "which", return_value="/usr/bin/nvidia-smi"
            ), mock.patch.object(doctor.subprocess, "run") as run:
                if isinstance(failure, Exception):
                    run.side_effect = failure
                else:
                    run.return_value = failure
                result = doctor.collect_report(timeout=1)
            self.assertEqual(result["gpu"]["status"], expected)
            self.assertIsNone(result["gpu"]["devices"])
            self.assertNotIn("secret", json.dumps(result))
            self.assertNotIn("private command", json.dumps(result))

    def test_mig_parse_failure_is_not_reported_as_disabled(self):
        result = doctor.parse_mig_listing("unexpected output")
        self.assertEqual(result["status"], "parse_error")
        self.assertIsNone(result["devices"])

    def test_torch_probe_uses_bounded_subprocess(self):
        with mock.patch.object(doctor.subprocess, "run", side_effect=subprocess.TimeoutExpired("python", 0.2)) as run:
            result = doctor.probe_torch(0.2)
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(run.call_args.kwargs["timeout"], 0.2)
        self.assertEqual(run.call_args.args[0][0], sys.executable)
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_torch_probe_rejects_non_json(self):
        with mock.patch.object(doctor.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "noise", "")):
            self.assertEqual(doctor.probe_torch(1)["status"], "parse_error")

    def test_atomic_output_refuses_existing_and_cleans_tempfiles(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"
            doctor.write_report(target, {"inventory_only": True})
            self.assertEqual(json.loads(target.read_text()), {"inventory_only": True})
            with self.assertRaises(FileExistsError):
                doctor.write_report(target, {"replacement": True})
            self.assertEqual(json.loads(target.read_text()), {"inventory_only": True})
            self.assertEqual([p.name for p in Path(directory).iterdir()], ["report.json"])

    def test_atomic_creation_race_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"
            real_link = os.link

            def concurrent_create(source, destination):
                Path(destination).write_text("other writer", encoding="utf-8")
                return real_link(source, destination)

            with mock.patch.object(doctor.os, "link", side_effect=concurrent_create):
                with self.assertRaises(FileExistsError):
                    doctor.write_report(target, {"new": True})
            self.assertEqual(target.read_text(), "other writer")
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_output_rejects_package_directory_and_dangling_symlink(self):
        with self.assertRaises(ValueError):
            doctor.write_report(Path(doctor.__file__).parent / "bad.json", {})
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"
            self.symlink(target, Path(directory) / "missing")
            with self.assertRaises(FileExistsError):
                doctor.write_report(target, {})
            self.assertTrue(target.is_symlink())

    def test_main_output_error_has_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "exists.json"
            target.write_text("keep", encoding="utf-8")
            with mock.patch.object(doctor, "collect_report", return_value={}), contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(doctor.main(["--output", str(target)]), 2)
            self.assertEqual(target.read_text(), "keep")
            self.assertEqual(json.loads(stderr.getvalue())["status"], "output_error")

    def test_symlink_loop_output_error_is_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "loop"
            self.symlink(target, target)
            with mock.patch.object(doctor, "collect_report", return_value={}), contextlib.redirect_stderr(io.StringIO()) as output:
                self.assertEqual(doctor.main(["--output", str(target)]), 2)
            self.assertEqual(json.loads(output.getvalue())["status"], "output_error")

    def test_missing_linux_available_memory_is_partial(self):
        with mock.patch.object(doctor.sys, "platform", "linux"), mock.patch.object(
            doctor.Path, "read_text", return_value="MemTotal: 4096 kB\n"
        ):
            result = doctor._memory(1)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["total_bytes"], 4096 * 1024)
        self.assertIsNone(result["available_bytes"])

    def test_memory_and_disk_probe_failure_remain_unknown(self):
        with mock.patch.object(doctor.sys, "platform", "linux"), mock.patch.object(
            doctor.Path, "read_text", side_effect=PermissionError
        ), mock.patch.object(doctor.os, "sysconf", side_effect=ValueError, create=True):
            memory = doctor._memory(1)
        with mock.patch.object(doctor.shutil, "disk_usage", side_effect=PermissionError):
            disk = doctor._disk()
        self.assertEqual(memory["status"], "error")
        self.assertIsNone(memory["total_bytes"])
        self.assertEqual(disk["status"], "error")
        self.assertIsNone(disk["free_bytes"])

    def test_optional_probe_import_failure_and_main_opt_in(self):
        raw = 'import chatter\nCAAP_TORCH_PROBE={"status":"import_error","error_type":"ModuleNotFoundError"}\n'
        with mock.patch.object(doctor.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, raw, "")):
            self.assertEqual(doctor.probe_torch(1)["status"], "import_error")
        with mock.patch.object(doctor, "collect_report", return_value={}) as collect, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(doctor.main(["--probe-torch", "--timeout", "2"]), 0)
        collect.assert_called_once_with(timeout=2.0, probe_torch_enabled=True)

    def test_timeout_must_be_positive_finite(self):
        for value in ("0", "-1", "nan", "inf"):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    doctor.main(["--timeout", value])
                self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
