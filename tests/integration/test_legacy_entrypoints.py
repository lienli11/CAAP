"""Safe legacy entrypoints must reject requests before data, GPU or output effects."""
from contextlib import redirect_stderr, redirect_stdout
import errno
import importlib
from importlib.util import find_spec
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


MISSING_RESEARCH = tuple(name for name in ("torch", "torchvision", "numpy", "PIL", "tqdm")
                         if find_spec(name) is None)


@unittest.skipIf(MISSING_RESEARCH, "optional research dependencies missing: " + ", ".join(MISSING_RESEARCH))
class LegacyEntrypointsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        cls._threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        import torch
        torch.set_num_threads(cls._threads)

    def assert_rejected(self, module_name, argv, expected):
        module = importlib.import_module(module_name)
        stderr = io.StringIO()
        with patch("torch.load", side_effect=AssertionError("unexpected data/checkpoint load")), \
             patch("torch.cuda.is_available", side_effect=AssertionError("unexpected GPU probe")), \
             redirect_stderr(stderr), redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                module.main(argv)
        self.assertEqual(result.exception.code, 2)
        self.assertIn(expected, stderr.getvalue())

    def test_attack_requires_legacy_consent_before_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_rejected("caap.attack.main", ["--save_dir", tmp + "/output"], "--allow-legacy-protocol")
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_pretrain_requires_legacy_consent_before_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_rejected("caap.tools.pretrain_ms_dife", ["--data_path", tmp + "/absent",
                "--num_class", "3", "--out", tmp + "/output.pth"], "--allow-legacy-protocol")
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_physical_requires_legacy_consent_before_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_rejected("caap.tools.physical_report", ["--csv", tmp + "/absent.csv",
                "--out", tmp + "/output.json"], "--allow-legacy-protocol")
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_attack_requires_existing_data_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, checkpoint = Path(tmp) / "data.pth", Path(tmp) / "checkpoint.pth"
            base = ["--allow-legacy-protocol", "--disable_ms_dife", "--save_dir", tmp + "/runs"]
            self.assert_rejected("caap.attack.main", base, "--data_path")
            self.assert_rejected("caap.attack.main", base + ["--data_path", str(data)], "--data_path")
            data.touch()
            self.assert_rejected("caap.attack.main", base + ["--data_path", str(data)], "--model_ckpt")
            self.assert_rejected("caap.attack.main", base + ["--data_path", str(data),
                "--model_ckpt", str(checkpoint)], "--model_ckpt")
            self.assertFalse((Path(tmp) / "runs").exists())

    def test_attack_rejects_unsafe_parameters_before_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data.pth"
            checkpoint = Path(tmp) / "checkpoint.pth"
            data.touch()
            checkpoint.touch()
            base = ["--allow-legacy-protocol", "--disable_ms_dife", "--data_path", str(data),
                    "--model_ckpt", str(checkpoint), "--save_dir", tmp + "/runs"]
            for option, value, expected in [("--val_ratio", "0", "val_ratio"),
                ("--val_ratio", "-0.1", "val_ratio"), ("--val_ratio", "1", "val_ratio"),
                ("--val_ratio", "nan", "val_ratio"), ("--epochs", "0", "epochs"),
                ("--batch_size", "0", "batch_size"), ("--lr", "nan", "lr"),
                ("--norm", "aug_org", "aug_0.5")]:
                with self.subTest(option=option, value=value):
                    self.assert_rejected("caap.attack.main", base + [option, value], expected)
            self.assertFalse((Path(tmp) / "runs").exists())

    def test_attack_enabled_ms_dife_requires_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data.pth"
            checkpoint = Path(tmp) / "checkpoint.pth"
            data.touch()
            checkpoint.touch()
            self.assert_rejected("caap.attack.main", ["--allow-legacy-protocol", "--data_path", str(data),
                "--model_ckpt", str(checkpoint), "--save_dir", tmp + "/runs"], "--ms_dife_ckpt")
            self.assertFalse((Path(tmp) / "runs").exists())

    def test_attack_existing_experiment_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data.pth"
            checkpoint = Path(tmp) / "checkpoint.pth"
            data.touch()
            checkpoint.touch()
            experiment = Path(tmp) / "tongji_compnet_untargeted_cross40_s42"
            experiment.mkdir()
            sentinel = experiment / "keep.txt"
            sentinel.write_text("keep")
            self.assert_rejected("caap.attack.main", ["--allow-legacy-protocol", "--disable_ms_dife",
                "--data_path", str(data), "--model_ckpt", str(checkpoint), "--save_dir", tmp], "already exists")
            self.assertEqual(sentinel.read_text(), "keep")

    def test_get_data_requires_explicit_existing_path(self):
        from caap.data.data import get_data
        with patch("torch.load", side_effect=AssertionError("unexpected load")):
            with self.assertRaises(ValueError):
                get_data(SimpleNamespace())
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(FileNotFoundError):
                    get_data(SimpleNamespace(data_path=str(Path(tmp) / "absent.pth")))

    def test_help_does_not_probe_gpu_or_load_data(self):
        for name in ("caap.attack.main", "caap.tools.pretrain_ms_dife",
                     "caap.tools.physical_report", "caap.tools.make_synth_data"):
            with self.subTest(module=name):
                module = importlib.import_module(name)
                with patch("torch.cuda.is_available", side_effect=AssertionError("GPU probe")), \
                     patch("torch.load", side_effect=AssertionError("data load")), \
                     redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as result:
                        module.main(["--help"])
                self.assertEqual(result.exception.code, 0)

    def test_synthetic_requires_output_and_rejects_unsafe_paths(self):
        self.assert_rejected("caap.tools.make_synth_data", [], "--output-dir")
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_rejected("caap.tools.make_synth_data", ["--output-dir", tmp], "already exists")
            for argv, expected in [(["--num_class", "0"], "num_class"),
                (["--train-victims", "--epochs", "0"], "epochs"),
                (["--epochs", "-1"], "epochs")]:
                self.assert_rejected("caap.tools.make_synth_data", ["--output-dir", tmp + "/new"] + argv, expected)
        module = importlib.import_module("caap.tools.make_synth_data")
        package_output = Path(module.__file__).resolve().parents[1] / "synthetic-forbidden"
        self.assert_rejected("caap.tools.make_synth_data", ["--output-dir", str(package_output)], "package")
        self.assertFalse(package_output.exists())

    def test_synthetic_default_generates_only_labeled_data(self):
        module = importlib.import_module("caap.tools.make_synth_data")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "synthetic"
            with patch.object(module, "train_victim", side_effect=AssertionError("implicit training")), \
                 redirect_stdout(io.StringIO()):
                module.main(["--output-dir", str(output), "--num_class", "2"])
            self.assertTrue((output / "data_pth" / "synth_128.pth").is_file())
            metadata = json.loads((output / "metadata.json").read_text())
            self.assertEqual(metadata["evidence_type"], "synthetic")
            self.assertIs(metadata["paper_eligible"], False)
            self.assertFalse((output / "ckpt").exists())

    def test_pretrain_missing_data_and_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, out = Path(tmp) / "data.pth", Path(tmp) / "weights.pth"
            base = ["--allow-legacy-protocol", "--data_path", str(data), "--out", str(out), "--num_class", "3"]
            self.assert_rejected("caap.tools.pretrain_ms_dife", base, "--data_path")
            data.touch()
            for option, value in [("--epochs", "0"), ("--num_class", "0"),
                                  ("--batch_size", "0"), ("--lr", "nan")]:
                self.assert_rejected("caap.tools.pretrain_ms_dife", base + [option, value], option)
            out.write_text("keep")
            self.assert_rejected("caap.tools.pretrain_ms_dife", base, "already exists")
            self.assertEqual(out.read_text(), "keep")

    def test_physical_missing_input_and_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, out = Path(tmp) / "rows.csv", Path(tmp) / "report.json"
            base = ["--allow-legacy-protocol", "--csv", str(data), "--out", str(out)]
            self.assert_rejected("caap.tools.physical_report", base, "--csv")
            data.touch()
            out.write_text("keep")
            self.assert_rejected("caap.tools.physical_report", base, "already exists")
            self.assertEqual(out.read_text(), "keep")

    def test_physical_report_labels_historical_statistics(self):
        module = importlib.import_module("caap.tools.physical_report")
        with tempfile.TemporaryDirectory() as tmp:
            data, out = Path(tmp) / "rows.csv", Path(tmp) / "report.json"
            data.write_text("subject,attempt,success,condition,model\n"
                            "s1,1,1,lab,victim\ns1,2,0,lab,victim\n")
            with redirect_stdout(io.StringIO()):
                module.main(["--allow-legacy-protocol", "--csv", str(data), "--out", str(out)])
            report = json.loads(out.read_text())
            self.assertEqual(report["schema"], "legacy-diagnostic")
            self.assertEqual(report["evidence_type"], "unverified")
            self.assertIs(report["paper_eligible"], False)
            self.assertIn("random-subset", report["metric_warning"])
            self.assertEqual(report["results"]["victim|lab"]["per_capture_asr"], 50.0)
            self.assertEqual(report["results"]["victim|lab"]["asr_at_k"], {"1": 50.0})

    def test_attack_paths_follow_caller_cwd_and_expand_home(self):
        module = importlib.import_module("caap.attack.main")
        class StopBeforeData(Exception):
            pass
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            Path(tmp, "data.pth").touch()
            Path(tmp, "weights.pth").touch()
            captured = []
            def stop(args):
                captured.append(args)
                raise StopBeforeData()
            try:
                os.chdir(tmp)
                with patch.dict(os.environ, {"HOME": tmp, "USERPROFILE": tmp}), patch.object(module, "get_data", side_effect=stop), \
                     patch.object(module, "set_seed"), patch("torch.cuda.is_available", return_value=False), \
                     patch("torch.load", side_effect=AssertionError("unexpected load")), \
                     redirect_stdout(io.StringIO()):
                    with self.assertRaises(StopBeforeData):
                        module.main(["--allow-legacy-protocol", "--disable_ms_dife", "--data_path", "data.pth",
                                     "--model_ckpt", "~/weights.pth"])
            finally:
                os.chdir(cwd)
            self.assertEqual(captured[0].data_path, str(Path(tmp, "data.pth").resolve()))
            self.assertEqual(captured[0].model_ckpt, str(Path(tmp, "weights.pth").resolve()))
            experiment = Path(tmp, "runs", "legacy", "tongji_compnet_untargeted_cross40_s42")
            metadata = json.loads((experiment / "metadata.json").read_text())
            self.assertEqual(metadata, {"schema": "legacy-diagnostic", "evidence_type": "unverified",
                                        "paper_eligible": False})

    def test_synthetic_pickle_roundtrip_is_only_for_own_generated_data(self):
        module = importlib.import_module("caap.tools.make_synth_data")
        from caap.data.data import PalmPrint
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp, "synthetic")
            with redirect_stdout(io.StringIO()):
                module.main(["--output-dir", str(output), "--num_class", "2"])
            dataset = PalmPrint(str(output / "data_pth" / "synth_128.pth"), norm="aug_0.5", train=False)
            self.assertEqual(len(dataset), 10)
            image, label = dataset[0]
            self.assertEqual(tuple(image.shape), (1, 128, 128))
            self.assertEqual(label, 0)

    def test_existing_dangling_output_links_are_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp, "input.pth")
            data.touch()
            cases = [
                ("caap.tools.make_synth_data", ["--output-dir"]),
                ("caap.tools.pretrain_ms_dife", ["--allow-legacy-protocol", "--data_path", str(data),
                  "--num_class", "3", "--out"]),
                ("caap.tools.physical_report", ["--allow-legacy-protocol", "--csv", str(data), "--out"]),
            ]
            for i, (module, argv) in enumerate(cases):
                target, link = Path(tmp, f"target-{i}"), Path(tmp, f"link-{i}")
                try:
                    link.symlink_to(target)
                except NotImplementedError as exc:
                    self.skipTest(f"symbolic links unavailable on this platform: {exc}")
                except OSError as exc:
                    if exc.errno in (errno.EPERM, errno.EACCES, errno.ENOSYS, errno.ENOTSUP):
                        self.skipTest(f"symbolic links require unavailable OS/filesystem privileges: {exc}")
                    raise
                with self.subTest(module=module):
                    self.assert_rejected(module, argv + [str(link)], "already exists")
                    self.assertFalse(target.exists())
                    self.assertTrue(link.is_symlink())

    def test_make_split_is_deterministic_and_validates_counts(self):
        from caap.tools.make_synth_data import make_split
        first, second = make_split(2, 2, size=16, seed=7), make_split(2, 2, size=16, seed=7)
        self.assertEqual(first["labels"], second["labels"])
        self.assertEqual([image.tobytes() for image in first["images"]],
                         [image.tobytes() for image in second["images"]])
        self.assertTrue(all(image.mode == "L" for image in first["images"]))
        for args in [(0, 2, 16), (2, 0, 16), (2, 2, 0)]:
            with self.assertRaises(ValueError):
                make_split(*args)


if __name__ == "__main__":
    unittest.main()
