"""The workspace command layer is usable without heavy research dependencies."""

import contextlib
import io
import os
import subprocess
import sys
import unittest
from unittest import mock

from caap import __version__
from caap.cli import COMMANDS, main


class CliTests(unittest.TestCase):
    def test_help_does_not_import_research_modules(self):
        output = io.StringIO()
        with mock.patch("caap.cli.importlib.import_module") as load, contextlib.redirect_stdout(output):
            self.assertEqual(0, main([]))
        load.assert_not_called()
        self.assertIn("planned, not implemented", " ".join(output.getvalue().split()))

    def test_version(self):
        with contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as exc:
            main(["--version"])
        self.assertEqual(0, exc.exception.code)
        self.assertIn(__version__, output.getvalue())

    def test_dispatch_passes_arguments_without_reinterpretation(self):
        for command, (module_name, _) in COMMANDS.items():
            with self.subTest(command=command), mock.patch("caap.cli.importlib.import_module") as load:
                load.return_value.main.return_value = 7
                self.assertEqual(7, main([command, "--output", "a path.json"]))
                load.assert_called_once_with(module_name)
                load.return_value.main.assert_called_once_with(["--output", "a path.json"])

    def test_missing_research_dependency_is_actionable(self):
        for command in ("legacy-attack", "legacy-pretrain", "legacy-physical-report", "make-synthetic"):
            with self.subTest(command=command):
                missing = ModuleNotFoundError("No module named numpy", name="numpy")
                with mock.patch("caap.cli.importlib.import_module", side_effect=missing), contextlib.redirect_stderr(io.StringIO()) as output:
                    self.assertEqual(2, main([command]))
                self.assertIn("research", output.getvalue())
                self.assertNotIn("Traceback", output.getvalue())
                with mock.patch("caap.cli.importlib.import_module", side_effect=missing), contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(0, main([command, "--help"]))
                self.assertIn("No work was executed", output.getvalue())

    def test_missing_internal_module_is_not_hidden_as_optional_dependency(self):
        missing = ModuleNotFoundError("broken package", name="caap.tools.missing")
        with mock.patch("caap.cli.importlib.import_module", side_effect=missing), self.assertRaises(ModuleNotFoundError):
            main(["legacy-attack"])

    def test_unknown_command_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
            main(["run-all-experiments"])
        self.assertEqual(2, exc.exception.code)

    def test_import_has_no_working_directory_side_effect(self):
        code = "import os,sys; cwd=os.getcwd(); paths=list(sys.path); import caap; import caap.cli; assert cwd==os.getcwd(); assert paths==sys.path; assert 'torch' not in sys.modules"
        result = subprocess.run([sys.executable, "-c", code], cwd=os.getcwd(), capture_output=True, text=True, timeout=20)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
