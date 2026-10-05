"""Safety and runner-inference tests for the reversible project bootstrapper."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("testing_suite_bootstrap", SCRIPT)
bootstrap = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bootstrap
spec.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "project with spaces"
        self.package = self.base / "package"
        for directory in ("skills", "protocols", "references", "schemas", "scripts", "agent", "evaluations", "examples"):
            (self.package / directory).mkdir(parents=True)
        for name in ("SKILL.md", "README.md", "protocols/GRAPH-CONVENTIONS.md", "agent/INSTALL.md", "evaluations/cases.json", "examples/example.json"):
            (self.package / name).write_text("fixture\n", encoding="utf-8")
        (self.package / "scripts/bootstrap.py").write_bytes(SCRIPT.read_bytes())
        for name in ("suite.py", "suite_core.py"):
            (self.package / "scripts" / name).write_text("# runtime copy fixture\n", encoding="utf-8")
        self.source_patch = mock.patch.object(bootstrap, "PACKAGE_ROOT", self.package)
        self.source_patch.start()
        self.addCleanup(self.source_patch.stop)

    def call(self, *extra, agent="none"):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = bootstrap.main(["--project", str(self.project), "--agent", agent, *extra])
        return status, json.loads(output.getvalue()) if output.getvalue() else None, error.getvalue()

    def write(self, relative, content):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def snapshot(self):
        if not self.project.exists():
            return None
        result = {}
        for parent, dirs, files in os.walk(self.project, followlinks=False):
            for name in dirs + files:
                path = Path(parent) / name
                result[path.relative_to(self.project).as_posix()] = ("symlink", os.readlink(path)) if path.is_symlink() else (("directory",) if path.is_dir() else ("file", path.read_bytes()))
        return result

    def unit_test(self, name="tests/test_demo.py"):
        return self.write(name, "import unittest\nclass Demo(unittest.TestCase):\n    def test_real_case(self):\n        self.assertEqual(2 + 2, 4)\n")

    def test_dry_run_missing_target_creates_nothing_and_returns_plan(self):
        status, plan, error = self.call("--dry-run", "--ci", "--profile", "generic")
        self.assertEqual(status, 0, error)
        self.assertFalse(self.project.exists())
        self.assertTrue(plan["dry_run"])
        self.assertIn(".testing-suite/config.json", {item["path"] for item in plan["files"]})
        self.assertIn(".github/workflows/testing-suite.yml", {item["path"] for item in plan["files"]})

    def test_identical_rerun_is_noop_and_preserves_unrelated_ignore_edits(self):
        self.unit_test()
        self.assertEqual(self.call(agent="both")[0], 0)
        before = self.snapshot()
        mtimes = {p: p.stat().st_mtime_ns for p in self.project.rglob("*") if p.is_file()}
        status, plan, error = self.call(agent="both")
        self.assertEqual(status, 0, error)
        self.assertTrue(all(item["action"] == "unchanged" for item in plan["files"]))
        self.assertEqual(before, self.snapshot())
        self.assertEqual(mtimes, {p: p.stat().st_mtime_ns for p in self.project.rglob("*") if p.is_file()})
        ignore = self.project / ".gitignore"
        ignore.write_bytes(ignore.read_bytes() + b"\n# user addition\n*.log\n")
        before = self.snapshot()
        self.assertEqual(self.call(agent="both")[0], 0)
        self.assertEqual(before, self.snapshot())

    def test_preserves_project_code_manifests_and_agent_files(self):
        originals = {"AGENTS.md": "existing codex instructions\n", "CLAUDE.md": "existing claude instructions\n", "package.json": '{"scripts":{"test":"echo \\"Error: no test specified\\" && exit 1"}}\n', "pyproject.toml": '[project]\nname="existing"\n', "main.py": "print('existing')\n", ".gitignore": "# old ignore\nprivate/"}
        for name, value in originals.items():
            self.write(name, value)
        self.assertEqual(self.call(agent="both")[0], 0)
        for name, value in originals.items():
            content = (self.project / name).read_text()
            self.assertTrue(content.startswith(value) if name == ".gitignore" else content == value)
        config = json.loads((self.project / ".testing-suite/config.json").read_text())
        self.assertEqual(config["runners"], [])

    def test_late_agent_collision_aborts_every_write(self):
        self.write(".claude/skills/testing-suite/protocols/GRAPH-CONVENTIONS.md", "user document\n")
        self.write(".gitignore", "preserve me\n")
        before = self.snapshot()
        status, _, error = self.call(agent="both")
        self.assertEqual(status, 2)
        self.assertIn("Collision", error)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.project / ".testing-suite").exists())

    def test_user_modified_generated_file_aborts_without_changes(self):
        self.assertEqual(self.call()[0], 0)
        self.write(".testing-suite/graph.json", '{"user":"mapping"}\n')
        before = self.snapshot()
        self.assertEqual(self.call()[0], 2)
        self.assertEqual(before, self.snapshot())

    def test_symlink_at_owned_directory_rejected_without_escape(self):
        external = self.base / "external"
        external.mkdir()
        self.project.mkdir()
        (self.project / ".testing-suite").symlink_to(external, target_is_directory=True)
        before = self.snapshot()
        self.assertEqual(self.call()[0], 2)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(list(external.iterdir()), [])

    def test_symlink_at_owned_file_and_inside_project_rejected(self):
        target = self.write("user_graph.json", "untouched")
        (self.project / ".testing-suite").mkdir()
        (self.project / ".testing-suite/graph.json").symlink_to(target)
        before = self.snapshot()
        self.assertEqual(self.call()[0], 2)
        self.assertEqual(before, self.snapshot())

    def test_project_and_ancestor_symlink_rejected(self):
        real = self.base / "real"
        real.mkdir()
        self.project.symlink_to(real, target_is_directory=True)
        self.assertEqual(self.call("--dry-run")[0], 2)
        self.project.unlink()
        link = self.base / "link"
        link.symlink_to(real, target_is_directory=True)
        self.project = link / "new-project"
        self.assertEqual(self.call()[0], 2)
        self.assertFalse((real / "new-project").exists())

    def test_file_in_parent_path_aborts_without_changes(self):
        self.write(".agents", "not a directory\n")
        before = self.snapshot()
        self.assertEqual(self.call(agent="codex")[0], 2)
        self.assertEqual(before, self.snapshot())

    def test_malformed_ignore_section_aborts_without_changes(self):
        self.write(".gitignore", bootstrap.IGNORE_BEGIN + "\nuser rule\n")
        before = self.snapshot()
        self.assertEqual(self.call()[0], 2)
        self.assertEqual(before, self.snapshot())

    def test_atomic_write_failure_rolls_back_files_directories_and_ignore(self):
        ignore = self.write(".gitignore", "original ignore\n")
        ignore.chmod(0o640)
        before = self.snapshot()
        original = bootstrap.atomic_write
        calls = 0

        def failing(path, data):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError("injected write failure")
            return original(path, data)

        with mock.patch.object(bootstrap, "atomic_write", side_effect=failing):
            status, _, error = self.call()
        self.assertEqual(status, 2)
        self.assertIn("injected write failure", error)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(ignore.stat().st_mode & 0o777, 0o640)

    def test_spaces_in_test_path_have_valid_ids_and_actual_runner(self):
        self.unit_test("tests with spaces/test_demo.py")
        self.assertEqual(self.call()[0], 0)
        graph = json.loads((self.project / ".testing-suite/graph.json").read_text())
        test = next(node for node in graph["nodes"] if node["kind"] == "test")
        self.assertFalse(re.search(r"\s", test["id"]))
        self.assertEqual(test["path"], "tests with spaces/test_demo.py")
        config = json.loads((self.project / ".testing-suite/config.json").read_text())
        runner = next(r for r in config["runners"] if r["id"] == test["runner"])
        completed = subprocess.run(runner["command"], cwd=self.project, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Ran 1 test", completed.stderr)

    def test_pytest_and_nested_manifest_coverage_are_not_inferred(self):
        self.write("pyproject.toml", '[project]\ndependencies=["pytest"]\n[tool.pytest.ini_options]\ntestpaths=["tests"]\n')
        self.unit_test()
        self.write("nested/pyproject.toml", "[project]\nname='nested'\n")
        self.unit_test("nested/test_hidden.py")
        self.assertEqual(self.call("--ci")[0], 0)
        graph = json.loads((self.project / ".testing-suite/graph.json").read_text())
        self.assertTrue(all("runner" not in node for node in graph["nodes"] if node["kind"] == "test"))
        ci = (self.project / ".github/workflows/testing-suite.yml").read_text()
        self.assertIn("Execution gate unavailable", ci)
        self.assertNotIn(" gate --selection", ci)

    def test_unittest_import_without_test_cases_does_not_enable_execution(self):
        self.write("test_empty.py", "import unittest\n")
        self.assertEqual(self.call("--ci")[0], 0)
        config = json.loads((self.project / ".testing-suite/config.json").read_text())
        self.assertEqual(config["runners"], [])
        self.assertIn("Execution gate unavailable", (self.project / ".github/workflows/testing-suite.yml").read_text())

    def test_unittest_nested_manifest_remains_unmapped(self):
        self.unit_test()
        self.write("nested/pyproject.toml", "[project]\nname='nested'\n")
        self.unit_test("nested/test_hidden.py")
        runners, tests, warnings, detected = bootstrap.infer(self.project, "auto")
        self.assertEqual(len(runners), 1)
        self.assertNotIn("runner", next(test for test in tests if test["path"].startswith("nested/")))
        self.assertTrue(any("Nested manifests" in warning for warning in warnings))

    def test_node_scripts_preserved_but_unknown_coverage_and_manager_conflicts_fail_closed(self):
        self.write("package.json", '{"scripts":{"test":"vitest run","test:watch":"vitest --watch","test:unit":"jest"}}')
        self.write("src/demo.test.ts", "test('example', () => {})\n")
        runners, tests, warnings, _ = bootstrap.infer(self.project, "auto")
        self.assertEqual({tuple(runner["command"]) for runner in runners}, {("npm", "run", "test"), ("npm", "run", "test:unit")})
        self.assertTrue(all("runner" not in test for test in tests))
        self.write("pnpm-lock.yaml", "lockfileVersion: 9\n")
        self.write("yarn.lock", "# conflicting lock\n")
        runners, _, warnings, _ = bootstrap.infer(self.project, "auto")
        self.assertEqual(runners, [])
        self.assertTrue(any("Conflicting" in warning for warning in warnings))

    def test_mixed_runner_inventory_does_not_enable_partial_ci_execution(self):
        self.unit_test()
        self.write("package.json", '{"scripts":{"test":"vitest run"}}')
        status, plan, error = self.call("--ci")
        self.assertEqual(status, 0, error)
        config = json.loads((self.project / ".testing-suite/config.json").read_text())
        self.assertEqual(len(config["runners"]), 2)
        self.assertIn("Execution gate unavailable", (self.project / ".github/workflows/testing-suite.yml").read_text())
        self.assertTrue(any("Mixed Python/Node" in warning for warning in plan["warnings"]))

    def test_source_secrets_and_caches_are_not_distributed(self):
        for name in (".env", ".env.production", "private.pem", "api.key", "module.pyc"):
            (self.package / name).write_text("sensitive fixture")
        (self.package / "scripts/__pycache__").mkdir()
        (self.package / "scripts/__pycache__/module.pyc").write_text("compiled")
        self.assertEqual(self.call(agent="codex")[0], 0)
        installed = self.project / ".agents/skills/testing-suite"
        for name in (".env", ".env.production", "private.pem", "api.key", "module.pyc", "scripts/__pycache__"):
            self.assertFalse((installed / name).exists(), name)

    def test_manifest_hashes_and_complete_agent_package_support_cold_bootstrap(self):
        self.assertEqual(self.call(agent="codex")[0], 0)
        manifest = json.loads((self.project / ".testing-suite/bootstrap-manifest.json").read_text())
        self.assertNotIn(".gitignore", manifest["files"])
        self.assertNotIn(".testing-suite/bootstrap-manifest.json", manifest["files"])
        for relative, metadata in manifest["files"].items():
            self.assertEqual(hashlib.sha256((self.project / relative).read_bytes()).hexdigest(), metadata["sha256"])
        installed = self.project / ".agents/skills/testing-suite"
        for relative in ("scripts/bootstrap.py", "scripts/suite.py", "agent/INSTALL.md", "evaluations/cases.json", "examples/example.json"):
            self.assertTrue((installed / relative).is_file(), relative)
        next_project = self.base / "cold second project"
        result = subprocess.run([sys.executable, str(installed / "scripts/bootstrap.py"), "--project", str(next_project), "--agent", "codex"], cwd=self.base, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((next_project / ".agents/skills/testing-suite/scripts/bootstrap.py").is_file())


if __name__ == "__main__":
    unittest.main()
