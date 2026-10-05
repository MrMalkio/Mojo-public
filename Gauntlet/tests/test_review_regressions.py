"""Regressions from independent impact and execution-evidence review."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from suite_core import Project, SuiteError, build_index, gate, impact, run_selection


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="testing-suite-review-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write(".gitignore", ".testing-suite/state/\nignored.py\n")
        self.write("a.py", "def a():\n    return 1\n")
        self.write("b.py", "def b():\n    return 1\n")
        self.write("ignored.py", "def ignored():\n    return 1\n")
        self.write("test_all.py", "import unittest\nclass TestAll(unittest.TestCase):\n"
                   "    def test_a(self):\n        self.assertTrue(True)\n"
                   "    def test_b(self):\n        self.assertTrue(True)\n")
        self.config = {
            "schema_version": 1,
            "project": {"id": "product:review", "name": "Review fixture"},
            "repositories": [{"id": "repo:main", "path": "."}],
            "policy": {"full_suite_every_days": 7, "always_include_critical": True},
            "runners": [{"id": "unit", "command": [sys.executable, "-m", "unittest",
                         "discover", "-v", "-s", ".", "-p", "test_all.py"]}],
        }
        self.graph = {
            "schema_version": 1,
            "nodes": [
                {"id": "fn:a", "kind": "function", "name": "A", "repo": "repo:main",
                 "path": "a.py", "symbol": "a"},
                {"id": "fn:b", "kind": "function", "name": "Uncovered B", "repo": "repo:main",
                 "path": "b.py", "symbol": "b"},
                {"id": "fn:ignored", "kind": "function", "name": "Ignored source", "repo": "repo:main",
                 "path": "ignored.py", "symbol": "ignored"},
                {"id": "test:a", "kind": "test", "name": "A test", "repo": "repo:main",
                 "path": "test_all.py", "symbol": "TestAll.test_a", "runner": "unit", "critical": True},
                {"id": "test:b", "kind": "test", "name": "Ignored-source test", "repo": "repo:main",
                 "path": "test_all.py", "symbol": "TestAll.test_b", "runner": "unit"},
            ],
            "edges": [{"source": "test:a", "target": "fn:a", "relation": "covers"},
                      {"source": "test:b", "target": "fn:ignored", "relation": "covers"}],
            "parity_groups": [],
        }
        self.save()
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Testing Suite Review", "-c", "user.email=review@example.test",
                 "commit", "-qm", "Review fixture")

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def save(self):
        self.write(".testing-suite/config.json", json.dumps(self.config))
        self.write(".testing-suite/graph.json", json.dumps(self.graph))

    def git(self, *arguments):
        subprocess.run(["git", "-C", str(self.root), *arguments], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def baseline(self):
        project = Project(self.root)
        self.assertEqual(project.errors, [])
        self.assertEqual(build_index(project)["errors"], [])
        selection = impact(project, full=True)
        result = run_selection(project, selection)
        self.assertTrue(all(record["status"] == "passed" for record in result["results"]), result)
        self.assertTrue(gate(project, selection)["passed"])
        return project, selection

    def test_every_changed_seed_needs_coverage_before_targeting(self):
        project, _ = self.baseline()
        selection = impact(project, nodes=["fn:a", "fn:b"])
        self.assertEqual(selection["mode"], "FULL", selection)
        self.assertEqual(set(selection["selected_tests"]), {"test:a", "test:b"})

    def test_ignored_source_change_survives_reindexing(self):
        project, _ = self.baseline()
        self.write("ignored.py", "def ignored():\n    return 2\n")
        self.assertEqual(build_index(project)["errors"], [])
        selection = impact(project)
        self.assertIn("ignored.py", selection["changed_files"], selection)
        self.assertIn("test:b", selection["selected_tests"], selection)

    def test_duplicate_unittest_modules_cannot_verify_unexecuted_repository(self):
        self.write("consumer/test_shared.py", "import unittest\nclass Check(unittest.TestCase):\n"
                   "    def test_same(self):\n        self.assertTrue(True)\n")
        self.write("provider/test_shared.py", "import unittest\nclass Check(unittest.TestCase):\n"
                   "    def test_same(self):\n        self.assertTrue(False)\n")
        self.config["repositories"] = [{"id": "repo:consumer", "path": "consumer"},
                                       {"id": "repo:provider", "path": "provider"}]
        self.config["runners"][0]["command"] = [sys.executable, "-m", "unittest", "discover",
                                                  "-v", "-s", "consumer", "-p", "test_shared.py"]
        self.graph["nodes"] = [
            {"id": "test:" + repository, "kind": "test", "name": repository + " test",
             "repo": "repo:" + repository, "path": "test_shared.py", "symbol": "Check.test_same",
             "runner": "unit"} for repository in ("consumer", "provider")
        ]
        self.graph["edges"] = []
        self.save()
        project = Project(self.root)
        self.assertEqual(build_index(project)["errors"], [])
        selection = impact(project, full=True)
        try:
            result = run_selection(project, selection)
        except SuiteError:
            return  # Rejecting ambiguous runner-to-file identity is conservative.
        provider = next(record for record in result["results"] if record["id"] == "test:provider")
        self.assertNotEqual(provider["status"], "passed", result)
        self.assertFalse(gate(project, selection)["passed"])

    def test_full_scope_cannot_ignore_unmapped_configured_runner(self):
        self.config["runners"].append({"id": "unmapped", "command": [sys.executable, "-c",
                                                                                "raise SystemExit(1)"]})
        self.save()
        project = Project(self.root)
        self.assertEqual(build_index(project)["errors"], [])
        selection = impact(project, full=True)
        try:
            run_selection(project, selection)
        except SuiteError:
            return  # An incomplete full-suite inventory must not execute as full proof.
        self.assertFalse(gate(project, selection)["passed"])
        full = project.read_state("last-full.json")
        self.assertFalse(full and full.get("status") == "passed")

    def test_external_symlink_cannot_keep_evidence_current(self):
        project, selection = self.baseline()
        with tempfile.TemporaryDirectory(prefix="testing-suite-external-") as directory:
            external = Path(directory) / "external.py"
            external.write_text("VALUE = 1\n", encoding="utf-8")
            (self.root / "linked.py").symlink_to(external)
            self.assertTrue(build_index(project)["errors"])
            external.write_text("VALUE = 2\n", encoding="utf-8")
            self.assertFalse(gate(project, selection)["passed"])
            current = impact(project, full=True)
            with self.assertRaises(SuiteError):
                run_selection(project, current)


if __name__ == "__main__":
    unittest.main()
