"""Contract tests for a document dependency graph, not experimental completion."""

import contextlib
import copy
import errno
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from caap.runtime import plancheck


REVIEWERS = [f"R1-{index}" for index in range(1, 8)] + [f"R2-{index}" for index in range(1, 6)] + [f"R3-{index}" for index in range(1, 5)]
HYPOTHESES = [f"H{index}" for index in range(1, 6)]


def manifest_fixture():
    evidence = REVIEWERS + HYPOTHESES
    return {
        "schema_version": "caap.tasks.v2", "plan_version": "caap-full-v2",
        "reviewer_ids": REVIEWERS.copy(), "hypothesis_ids": HYPOTHESES.copy(),
        "tasks": [{
            "id": f"F{index:02d}", "title": f"Future task {index}", "phase": index // 10,
            "depends_on": [] if index == 1 else [f"F{index - 1:02d}"],
            "owned_paths": [f"src/future_{index}/**"], "inputs": ["an input description"],
            "outputs": [f"artifacts/task_{index}/result.json"], "acceptance": ["documented check"],
            "evidence_for": [evidence[index - 1]] if index <= len(evidence) else [],
            "capabilities": ["standard-library"], "spec": "plan/spec.md",
            "status": "planned", "cost_class": "cpu",
        } for index in range(1, 46)],
    }


class PlancheckTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "plan").mkdir()
        (self.root / "plan/spec.md").write_text("# Future work\n", encoding="utf-8")
        self.manifest = manifest_fixture()

    def symlink(self, path, target):
        try:
            path.symlink_to(target, target_is_directory=True)
        except NotImplementedError:
            self.skipTest("Symbolic links are not supported on this platform.")
        except OSError as exc:
            if exc.errno in {errno.EPERM, errno.EACCES, errno.ENOSYS, errno.ENOTSUP} or getattr(exc, "winerror", None) == 1314:
                self.skipTest("Symbolic link creation is unavailable or not permitted.")
            raise

    def check(self, manifest=None):
        return plancheck.validate_manifest(self.manifest if manifest is None else manifest, self.root)

    def codes(self, result):
        return {error["code"] for error in result["errors"]}

    def test_complete_document_graph_is_valid_without_implemented_outputs(self):
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["task_count"], 45)
        self.assertEqual(len(result["topological_waves"]), 45)
        self.assertEqual(result["topological_waves"][0], ["F01"])
        self.assertEqual(result["coverage"]["reviewers"]["R1-1"], ["F01"])
        self.assertEqual(result["coverage"]["hypotheses"]["H5"], ["F21"])
        self.assertTrue(result["document_graph_only"])
        self.assertFalse(result["experiments_implemented"])
        self.assertFalse((self.root / "artifacts").exists())

    def test_duplicate_and_missing_tasks(self):
        self.manifest["tasks"][-1] = copy.deepcopy(self.manifest["tasks"][0])
        result = self.check()
        self.assertIn("duplicate_task_id", self.codes(result))
        self.assertIn("missing_task_ids", self.codes(result))
        self.assertFalse(result["valid"])

    def test_unknown_task_and_dependency_ids(self):
        self.manifest["tasks"][0]["id"] = "F99"
        self.manifest["tasks"][1]["depends_on"] = ["F98"]
        result = self.check()
        self.assertIn("invalid_task_id", self.codes(result))
        self.assertIn("unknown_dependency", self.codes(result))

    def test_all_fields_are_required(self):
        for field in tuple(self.manifest["tasks"][0]):
            with self.subTest(field=field):
                broken = copy.deepcopy(self.manifest)
                del broken["tasks"][0][field]
                result = self.check(broken)
                self.assertFalse(result["valid"])
                self.assertIn("missing_field", self.codes(result))

    def test_unknown_fields_rejected_at_both_levels(self):
        for top_level in (True, False):
            with self.subTest(top_level=top_level):
                broken = copy.deepcopy(self.manifest)
                target = broken if top_level else broken["tasks"][0]
                target["unexpected"] = "ignored?"
                self.assertIn("unknown_field", self.codes(self.check(broken)))

    def test_invalid_types_cannot_crash_validation(self):
        malformed = {
            "id": [], "title": {}, "phase": True, "depends_on": [None, {}],
            "owned_paths": "src/**", "inputs": [None], "outputs": {},
            "acceptance": [True], "evidence_for": [[]], "capabilities": 42,
            "spec": None, "status": [], "cost_class": {},
        }
        for field, value in malformed.items():
            with self.subTest(field=field):
                broken = copy.deepcopy(self.manifest)
                broken["tasks"][0][field] = value
                result = self.check(broken)
                self.assertFalse(result["valid"])
                self.assertIn("invalid_type", self.codes(result))

    def test_empty_critical_fields_and_blank_list_items_rejected(self):
        for field, value in (("id", ""), ("title", " "), ("spec", ""), ("owned_paths", []),
                             ("outputs", []), ("acceptance", []), ("acceptance", [" "])):
            with self.subTest(field=field, value=value):
                broken = copy.deepcopy(self.manifest)
                broken["tasks"][0][field] = value
                self.assertFalse(self.check(broken)["valid"])

    def test_wrong_versions_status_phase_and_cost_rejected(self):
        for field, value in (("schema_version", "old"), ("plan_version", "old")):
            broken = copy.deepcopy(self.manifest)
            broken[field] = value
            self.assertFalse(self.check(broken)["valid"])
        for field, value in (("status", "completed"), ("phase", -1), ("cost_class", "free")):
            broken = copy.deepcopy(self.manifest)
            broken["tasks"][0][field] = value
            self.assertFalse(self.check(broken)["valid"])

    def test_top_level_malformed_structures(self):
        for malformed in (None, [], "text", {"tasks": None}, {"tasks": [None]}):
            with self.subTest(value=malformed):
                self.assertFalse(plancheck.validate_manifest(malformed, self.root)["valid"])
        for field in ("tasks", "reviewer_ids", "hypothesis_ids"):
            broken = copy.deepcopy(self.manifest)
            broken[field] = [{}]
            self.assertFalse(self.check(broken)["valid"])

    def test_dependency_cycle_and_self_dependency(self):
        self.manifest["tasks"][0]["depends_on"] = ["F02"]
        result = self.check()
        self.assertIn("dependency_cycle", self.codes(result))
        self.assertEqual(result["topological_waves"], [])
        self.manifest["tasks"][0]["depends_on"] = ["F01"]
        self.assertIn("self_dependency", self.codes(self.check()))

    def test_duplicate_dependency_is_rejected(self):
        self.manifest["tasks"][1]["depends_on"] = ["F01", "F01"]
        self.assertIn("duplicate_dependency", self.codes(self.check()))

    def test_dependency_phase_cannot_move_backwards(self):
        self.manifest["tasks"][0]["phase"] = 9
        self.assertIn("phase_order", self.codes(self.check()))

    def test_specs_must_exist_and_be_markdown(self):
        for path in ("plan/missing.md", "plan", "plan/file.txt"):
            with self.subTest(path=path):
                self.manifest["tasks"][0]["spec"] = path
                self.assertFalse(self.check()["valid"])

    def test_repo_paths_cannot_escape_lexically(self):
        for field in ("spec", "owned_paths", "outputs"):
            for path in ("../outside.md", "/tmp/outside.md", "C:\\outside.md", "plan/../../outside.md"):
                with self.subTest(field=field, path=path):
                    broken = copy.deepcopy(self.manifest)
                    broken["tasks"][0][field] = path if field == "spec" else [path]
                    self.assertIn("unsafe_path", self.codes(self.check(broken)))

    def test_spec_and_write_path_symlinks_cannot_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            (Path(outside) / "outside.md").write_text("# outside", encoding="utf-8")
            self.symlink(self.root / "escape", outside)
            for field, path in (("spec", "escape/outside.md"), ("owned_paths", "escape/**"), ("outputs", "escape/result.json")):
                with self.subTest(field=field):
                    broken = copy.deepcopy(self.manifest)
                    broken["tasks"][0][field] = path if field == "spec" else [path]
                    self.assertIn("unsafe_path", self.codes(self.check(broken)))

    def test_glob_matched_symlink_components_are_rejected_without_following(self):
        reports = self.root / "reports"
        reports.mkdir()
        with tempfile.TemporaryDirectory() as outside:
            self.symlink(reports / "escape", outside)
            self.symlink(reports / "loop", reports / "loop")
            self.symlink(reports / "dangling", reports / "missing")
            for field in ("owned_paths", "outputs"):
                for pattern in ("reports/esc*/result.json", "reports/loo?/result.json", "reports/[d]angling/result.json",
                                "reports/**/result.json", "reports/*", "reports/esc*/future/**"):
                    with self.subTest(field=field, pattern=pattern):
                        broken = copy.deepcopy(self.manifest)
                        broken["tasks"][0][field] = [pattern]
                        result = self.check(broken)
                        self.assertFalse(result["valid"])
                        self.assertIn("unsafe_path", self.codes(result))

    def test_glob_without_matching_symlinks_allows_future_paths(self):
        reports = self.root / "reports"
        (reports / "safe" / "nested").mkdir(parents=True)
        self.symlink(reports / "escape", reports / "escape")
        for pattern in ("reports/sa*/future.json", "reports/safe/**/future.json", "reports/notyet*/future.json"):
            with self.subTest(pattern=pattern):
                broken = copy.deepcopy(self.manifest)
                broken["tasks"][0]["owned_paths"] = [pattern]
                self.assertTrue(self.check(broken)["valid"])

    def test_unreadable_glob_scope_is_rejected_not_assumed_safe(self):
        from unittest import mock
        (self.root / "reports").mkdir()
        self.manifest["tasks"][0]["owned_paths"] = ["reports/*/future.json"]
        with mock.patch("os.scandir", side_effect=PermissionError("not readable")):
            self.assertIn("unsafe_path", self.codes(self.check()))

    def test_excessive_glob_scan_is_unverified_not_safe(self):
        from unittest import mock
        (self.root / "reports").mkdir()
        self.manifest["tasks"][0]["owned_paths"] = ["reports/*/future.json"]
        entries = [Path(f"entry{index}") for index in range(10001)]
        with mock.patch("os.scandir") as scan:
            scan.return_value.__enter__.return_value = entries
            result = self.check()
        self.assertFalse(result["valid"])
        self.assertTrue(any("inspection limit" in error["message"] for error in result["errors"]))

    def test_cli_unknown_surrogate_key_is_json_under_strict_utf8(self):
        self.manifest["\ud800"] = "unknown"
        (self.root / "plan/tasks.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8:strict", PYTHONDONTWRITEBYTECODE="1")
        completed = subprocess.run(
            [sys.executable, "-m", "caap.runtime.plancheck", "--repo-root", str(self.root)],
            capture_output=True, text=True, encoding="utf-8", errors="strict", env=env, timeout=10,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr, "")
        result = json.loads(completed.stdout)
        self.assertFalse(result["valid"])
        self.assertIn("unknown_field", self.codes(result))
        self.assertTrue(any("\ud800" in error["location"] for error in result["errors"]))

    def test_every_reviewer_and_hypothesis_needs_task_evidence(self):
        self.manifest["tasks"][0]["evidence_for"] = []
        self.manifest["tasks"][16]["evidence_for"] = []
        result = self.check()
        self.assertIn("missing_evidence_coverage", self.codes(result))
        self.assertIn("R1-1", result["coverage"]["uncovered"])
        self.assertIn("H1", result["coverage"]["uncovered"])

    def test_invalid_evidence_and_registry_entries_rejected(self):
        self.manifest["tasks"][0]["evidence_for"] = ["R4-1"]
        self.manifest["reviewer_ids"].append("R4-1")
        self.manifest["hypothesis_ids"] = ["H1"] * 5
        result = self.check()
        self.assertIn("unknown_evidence_id", self.codes(result))
        self.assertIn("invalid_registry", self.codes(result))

    def test_conservative_write_set_conflicts_do_not_invalidate_document_graph(self):
        self.manifest["tasks"][0]["owned_paths"] = ["src/shared/**"]
        self.manifest["tasks"][1]["owned_paths"] = ["src/shared/model.py"]
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["possible_write_conflicts"][0]["task_ids"], ["F01", "F02"])
        self.assertTrue(result["possible_write_conflicts"][0]["dependency_ordered"])
        self.assertIn("conservative", result["conflict_analysis"])

    def test_glob_and_directory_overlap_are_conservative(self):
        for left, right in (("src/*/a.py", "src/mod/**"), ("src/model", "src/model/a.py"),
                            ("src/a*.py", "src/abc.py"), ("**/*.py", "other/x.py"),
                            ("./src//shared/**", "src/shared/model.py")):
            with self.subTest(left=left, right=right):
                self.assertTrue(plancheck.paths_may_overlap(left, right))
        self.assertFalse(plancheck.paths_may_overlap("src/a.py", "src/b.py"))
        self.assertFalse(plancheck.paths_may_overlap("src/a/**", "tests/a/**"))

    def test_parallel_waves_are_graph_frontiers_not_scheduling_authorization(self):
        self.manifest["tasks"][1]["depends_on"] = []
        self.manifest["tasks"][2]["depends_on"] = ["F01", "F02"]
        result = self.check()
        self.assertEqual(result["topological_waves"][0], ["F01", "F02"])
        self.assertTrue(result["document_graph_only"])

    def test_cli_reads_manifest_relative_to_repo_root_and_returns_json(self):
        path = self.root / "plan/tasks.json"
        path.write_text(json.dumps(self.manifest), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = plancheck.main(["--repo-root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["valid"])
        self.assertEqual(len(list((self.root / "plan").iterdir())), 2)

    def test_cli_missing_invalid_json_or_duplicate_json_keys_is_structured(self):
        for text in (None, "not json", '{"tasks": [], "tasks": []}'):
            with self.subTest(text=text):
                path = self.root / "plan/tasks.json"
                if text is not None:
                    path.write_text(text, encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    code = plancheck.main(["--repo-root", str(self.root)])
                result = json.loads(output.getvalue())
                self.assertNotEqual(code, 0)
                self.assertFalse(result["valid"])
                self.assertTrue(result["errors"])

    def test_cli_manifest_cannot_escape_repo_root(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = plancheck.main(["--repo-root", str(self.root), "--manifest", "../tasks.json"])
        self.assertNotEqual(code, 0)
        self.assertIn("unsafe_path", self.codes(json.loads(output.getvalue())))


if __name__ == "__main__":
    unittest.main()
