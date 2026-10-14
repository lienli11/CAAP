"""Repository governance and preservation checks, independent of PyTorch."""

import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RepositoryTests(unittest.TestCase):
    def test_top_level_roles_are_registered(self):
        config = json.loads((ROOT / "configs/repository-layout.json").read_text())
        allowed = set(config["root_files"] + config["maintained_directories"] + config["local_only_directories"])
        unknown = [p.name for p in ROOT.iterdir() if p.name not in allowed and p.name != ".DS_Store"]
        self.assertEqual([], unknown, "Register new top-level roles instead of scattering files")

    def test_no_nested_git_or_symlinks_in_published_source(self):
        for folder in ("src", "paper", "archive", "configs", "plan", "doc", "tests"):
            for path in (ROOT / folder).rglob("*"):
                self.assertNotEqual(".git", path.name)
                self.assertFalse(path.is_symlink(), str(path))

    def test_frozen_assets_preserve_original_bytes(self):
        manifest = json.loads((ROOT / "archive/legacy/migration.json").read_text())
        checked = 0
        for record in manifest["records"]:
            if record.get("migration_policy") != "frozen_bytes":
                continue
            path = ROOT / record["new_path"]
            self.assertTrue(path.is_file(), str(path))
            with path.open("rb") as source:
                digest = hashlib.sha256()
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
            self.assertEqual(record["sha256"], digest.hexdigest(), str(path))
            checked += 1
        self.assertGreaterEqual(checked, 15)
        self.assertFalse(manifest["legacy_artifacts"]["replay_supported"])

    def test_maintained_markdown_links_and_structure(self):
        files = [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "archive/README.md"]
        for folder in ("doc", "plan", "configs", "paper"):
            files.extend((ROOT / folder).rglob("*.md"))
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("\x00", text, str(path))
            self.assertEqual(0, sum(line.startswith("```") for line in text.splitlines()) % 2, str(path))
            self.assertFalse(re.search(r"^#{5,}\s", text, re.MULTILINE), str(path))
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*://", target) or target.startswith("#"):
                    continue
                resolved = (path.parent / target.split("#", 1)[0]).resolve()
                self.assertTrue(resolved.is_relative_to(ROOT), str(path) + ": outside link " + target)
                self.assertTrue(resolved.exists(), str(path) + ": missing link " + target)

    def test_full_profile_is_a_nonexecutable_scope_template(self):
        profile = json.loads((ROOT / "configs/profiles/full.json").read_text())
        tasks = json.loads((ROOT / "plan/tasks.json").read_text())
        self.assertFalse(profile["executable"])
        self.assertEqual(tasks["plan_version"], profile["plan_version"])
        self.assertEqual(set(tasks["hypothesis_ids"]), set(profile["hypotheses"]))
        self.assertEqual(3, len(profile["datasets"]))
        self.assertEqual(7, len(profile["models"]))
        self.assertFalse(profile["search_policy"]["allow_test_driven_search"])
        self.assertTrue(profile["resource_policy"]["require_explicit_allocation"])
        self.assertTrue(profile["completion_policy"]["cancelled_scope_is_not_original_full_complete"])

    def test_planned_writers_cannot_modify_frozen_sources(self):
        from caap.runtime.plancheck import paths_may_overlap
        manifest = json.loads((ROOT / "plan/tasks.json").read_text())
        forbidden = ("paper/sources/**", "archive/legacy/**", ".git/**", ".codebuddy/**")
        for task in manifest["tasks"]:
            for owned in task["owned_paths"]:
                for protected in forbidden:
                    self.assertFalse(paths_may_overlap(owned, protected),
                                     task["id"] + " may write protected evidence/state: " + owned)

    def test_task_specs_and_control_outputs_have_explicit_owners(self):
        from caap.runtime.plancheck import paths_may_overlap
        manifest = json.loads((ROOT / "plan/tasks.json").read_text())
        nodes = {task["id"]: task for task in manifest["tasks"]}
        for task in nodes.values():
            spec = (ROOT / task["spec"]).read_text()
            self.assertRegex(spec, r"(?m)^## " + task["id"] + r"\b")
            for output in task["outputs"]:
                self.assertTrue(any(paths_may_overlap(output, owned) for owned in task["owned_paths"]),
                                task["id"] + " has no publishing owner for " + output)
        for filename in ("experiment_manifest.json", "runner_registry.json", "dependency_bindings.json", "execution_prerequisites.json"):
            path = "runs/control/" + filename
            self.assertIn(path, nodes["F20"]["owned_paths"])
            self.assertIn(path, nodes["F20"]["outputs"])
        self.assertIn("F22", nodes["F43"]["depends_on"])
        self.assertTrue({"F36", "F39"}.isdisjoint(nodes["F20"]["depends_on"]))
        self.assertNotIn("F22", nodes["F23"]["depends_on"])
        self.assertIn("paper/revision/**", nodes["F44"]["owned_paths"])
        registry_gate = "reports/F09/registry-ready.json"
        self.assertIn(registry_gate, nodes["F09"]["outputs"])
        self.assertIn(registry_gate, nodes["F20"]["inputs"])
        self.assertIn("reports/F09/model-gates/", nodes["F09"]["outputs"])
        self.assertIn("reports/F09/clean-validation.json", nodes["F09"]["outputs"])

    def test_no_runtime_cwd_or_sys_path_mutation(self):
        patterns = ("os.chdir(", "sys.path.insert(", "sys.path.append(")
        for path in (ROOT / "src/caap").rglob("*.py"):
            for pattern in patterns:
                self.assertNotIn(pattern, path.read_text(), str(path))


if __name__ == "__main__":
    unittest.main()
