"""Safety and behavior tests for the stdlib control layer, using real Git/runners."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from suite_core import (Project, SuiteError, atomic_json, build_index, changed_files,
                        digest, gate, impact, parity, python_symbols, record_results,
                        run_selection, safe_path, state_diff, verify_selection)


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write("app.py", "# @coord:foo\ndef foo():\n    return 1\n\ndef bar():\n    return 2\n")
        self.write("tests/test_app.py", "import unittest\nfrom app import foo, bar\n\nclass AppTests(unittest.TestCase):\n    def test_foo(self):\n        self.assertEqual(foo(), 1)\n\n    def test_bar(self):\n        self.assertEqual(bar(), 2)\n")
        self.config = {"schema_version": 1, "project": {"id": "product:p", "name": "Fixture"},
                       "repositories": [{"id": "repo:r", "path": "."}],
                       "policy": {"full_suite_every_days": 7, "always_include_critical": True},
                       "runners": [{"id": "unit", "adapter": "unittest", "command": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]}]}
        self.graph = {"schema_version": 1, "nodes": [
            {"id": "product:p", "kind": "product", "name": "Fixture"},
            {"id": "repo:r", "kind": "repository", "name": "Repo", "repo": "repo:r"},
            {"id": "fn:foo", "kind": "function", "name": "foo", "repo": "repo:r", "path": "app.py", "symbol": "foo", "anchor": "foo"},
            {"id": "fn:bar", "kind": "function", "name": "bar", "repo": "repo:r", "path": "app.py", "symbol": "bar"},
            {"id": "test:foo", "kind": "test", "name": "test foo", "repo": "repo:r", "path": "tests/test_app.py", "symbol": "AppTests.test_foo", "runner": "unit"},
            {"id": "test:bar", "kind": "test", "name": "test bar", "repo": "repo:r", "path": "tests/test_app.py", "symbol": "AppTests.test_bar", "runner": "unit"}],
            "edges": [{"source": "product:p", "target": "repo:r", "relation": "contains"}]
            + [{"source": "repo:r", "target": n, "relation": "contains"} for n in ("fn:foo", "fn:bar", "test:foo", "test:bar")]
            + [{"source": "test:foo", "target": "fn:foo", "relation": "covers"},
               {"source": "test:bar", "target": "fn:bar", "relation": "verifies"}], "parity_groups": []}
        self.save()
        self.git("init", "-q")
        self.commit()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def save(self):
        self.write(".testing-suite/config.json", json.dumps(self.config))
        self.write(".testing-suite/graph.json", json.dumps(self.graph))

    def project(self):
        return Project(self.root)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode()

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Testing Suite", "-c", "user.email=suite@example.test", "commit", "-qm", "fixture")

    def baseline(self):
        project = self.project()
        build_index(project)
        selection = impact(project, full=True)
        result = run_selection(project, selection)
        if not all(r["status"] == "passed" for r in result["results"]):
            raise AssertionError(result)
        if not gate(project, selection)["passed"]:
            raise AssertionError(gate(project, selection))
        return selection


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture()
        self.addCleanup(self.fixture.temp.cleanup)

    def test_real_runner_evidence_gates_and_manual_claim_does_not(self):
        selection = self.fixture.baseline()
        project = self.fixture.project()
        full = project.read_state("last-full.json")
        self.assertIn("app.py", full["source_files"])
        record_results(project, selection, [{"id": t, "status": "passed"} for t in selection["selected_tests"]])
        self.assertFalse(gate(project, selection)["passed"])
        self.assertGreaterEqual(len(list((self.fixture.root / ".testing-suite/state/history").glob("*.json"))), 2)

    def test_stale_source_index_and_wrong_head_fail(self):
        selection = self.fixture.baseline()
        self.fixture.write("app.py", "# @coord:foo\ndef foo():\n    return 11\n\ndef bar():\n    return 2\n")
        project = self.fixture.project()
        self.assertEqual(impact(project)["mode"], "FULL")
        self.assertFalse(gate(project, selection)["passed"])
        build_index(project)
        with self.assertRaises(SuiteError):
            verify_selection(project, selection)
        wrong = impact(project, full=True)
        wrong["head"] = "0" * 40
        with self.assertRaises(SuiteError):
            verify_selection(project, wrong)

    def test_skipped_and_zero_collected_tests_fail(self):
        self.fixture.write("tests/test_app.py", "import unittest\n\nclass AppTests(unittest.TestCase):\n    @unittest.skip('deliberate')\n    def test_foo(self):\n        pass\n    def test_bar(self):\n        pass\n")
        project = self.fixture.project()
        build_index(project)
        selection = impact(project, full=True)
        result = run_selection(project, selection)
        self.assertEqual(next(r for r in result["results"] if r["id"] == "test:foo")["status"], "skipped")
        self.assertFalse(gate(project, selection)["passed"])
        self.fixture.config["runners"][0]["command"][-1:] = ["-p", "nothing_matches.py", "-v"]
        self.fixture.save()
        project = self.fixture.project()
        build_index(project)
        selection = impact(project, full=True)
        result = run_selection(project, selection)
        self.assertTrue(result["runners"][0]["zero_tests"])
        self.assertFalse(gate(project, selection)["passed"])

    def test_successful_arbitrary_command_is_not_test_evidence(self):
        self.fixture.config["runners"][0] = {"id": "unit", "command": [sys.executable, "-c", "print('done')"]}
        self.fixture.save()
        project = self.fixture.project()
        build_index(project)
        selection = impact(project, full=True)
        self.assertTrue(any(r["status"] != "passed" for r in run_selection(project, selection)["results"]))
        self.assertFalse(gate(project, selection)["passed"])

    def test_uncollected_mapped_case_cannot_pass(self):
        self.fixture.write("other/test_extra.py", "import unittest\n\nclass Extra(unittest.TestCase):\n    def test_extra(self):\n        pass\n")
        self.fixture.graph["nodes"].append({"id": "test:extra", "kind": "test", "name": "extra", "repo": "repo:r", "path": "other/test_extra.py", "symbol": "Extra.test_extra", "runner": "unit"})
        self.fixture.save()
        project = self.fixture.project()
        build_index(project)
        selection = impact(project, full=True)
        result = run_selection(project, selection)
        self.assertEqual(next(r for r in result["results"] if r["id"] == "test:extra")["status"], "skipped")
        self.assertFalse(gate(project, selection)["passed"])

    def test_targeted_rollup_does_not_pull_in_siblings(self):
        self.fixture.baseline()
        result = impact(self.fixture.project(), nodes=["fn:foo"])
        self.assertEqual(result["mode"], "TARGETED")
        self.assertEqual(result["selected_tests"], ["test:foo"])
        self.assertIn("product:p", result["affected_nodes"])
        self.assertNotIn("fn:bar", result["affected_nodes"])

    def test_each_changed_seed_needs_coverage(self):
        self.fixture.graph["edges"] = [e for e in self.fixture.graph["edges"] if not (e["source"] == "test:bar" and e["target"] == "fn:bar")]
        self.fixture.save()
        self.fixture.commit()
        self.fixture.baseline()
        result = impact(self.fixture.project(), nodes=["fn:foo", "fn:bar"])
        self.assertEqual(result["mode"], "FULL")
        self.assertTrue(any(r["code"] == "no_coverage" and r["node"] == "fn:bar" for r in result["reasons"]))

    def test_critical_capability_guard_and_provides_propagation(self):
        graph = self.fixture.graph
        graph["nodes"] += [{"id": "cap:x", "kind": "capability", "name": "x", "critical": True},
                           {"id": "inst:x", "kind": "instance", "name": "x impl"},
                           {"id": "api:x", "kind": "api", "name": "x api"}]
        graph["edges"] += [{"source": "inst:x", "target": "cap:x", "relation": "implements"},
                           {"source": "inst:x", "target": "fn:foo", "relation": "contains"},
                           {"source": "fn:foo", "target": "api:x", "relation": "provides"},
                           {"source": "fn:bar", "target": "api:x", "relation": "consumes"}]
        self.fixture.save()
        self.fixture.commit()
        self.fixture.baseline()
        result = impact(self.fixture.project(), nodes=["fn:bar"])
        self.assertIn("critical", result["test_reasons"]["test:foo"])
        result = impact(self.fixture.project(), nodes=["fn:foo"])
        self.assertIn("test:bar", result["selected_tests"])

    def test_ignored_mapped_file_change_survives_reindex(self):
        self.fixture.write(".gitignore", "ignored.py\n.testing-suite/state/\n")
        self.fixture.write("ignored.py", "def hidden():\n    return 1\n")
        self.fixture.graph["nodes"].append({"id": "fn:hidden", "kind": "function", "name": "hidden", "repo": "repo:r", "path": "ignored.py", "symbol": "hidden"})
        self.fixture.graph["edges"].append({"source": "test:bar", "target": "fn:hidden", "relation": "covers"})
        self.fixture.save()
        self.fixture.commit()
        self.fixture.baseline()
        self.fixture.write("ignored.py", "def hidden():\n    return 2\n")
        project = self.fixture.project()
        build_index(project)
        result = impact(project)
        self.assertIn("ignored.py", result["changed_files"])
        self.assertIn("test:bar", result["selected_tests"])

    def test_git_rename_delete_untracked_and_inherited_repo_paths(self):
        self.fixture.git("mv", "app.py", "renamed.py")
        self.fixture.git("rm", "tests/test_app.py")
        self.fixture.write("new.py", "pass\n")
        changes, problems = changed_files(self.fixture.project(), "HEAD")
        self.assertFalse(problems)
        self.assertTrue({"app.py", "renamed.py", "tests/test_app.py", "new.py"} <= changes)
        self.fixture.write("component/a.py", "pass\n")
        self.fixture.git("add", "component/a.py")
        self.fixture.git("-c", "user.name=Testing Suite", "-c", "user.email=suite@example.test", "commit", "-qm", "component")
        self.fixture.config["repositories"] = [{"id": "repo:c", "path": "component"}]
        self.fixture.graph["nodes"] = []
        self.fixture.graph["edges"] = []
        self.fixture.save()
        self.fixture.write("component/a.py", "changed = True\n")
        changes, _ = changed_files(self.fixture.project(), "HEAD")
        self.assertEqual(changes, {"component/a.py"})

    def test_stable_symbols_anchors_duplicates_and_string_literals(self):
        self.fixture.write("app.py", "# @coord:foo\ntext = '# @coord:foo'\ndef foo():\n    def inner():\n        return 'é'\n    return inner()\ndef bar():\n    return 2\n")
        project = self.fixture.project()
        index = build_index(project)
        self.assertFalse(index["errors"])
        self.assertIn("foo.inner", {s["name"] for s in index["files"]["app.py"]["symbols"]})
        self.assertEqual(index["nodes"]["fn:foo"]["start"], {"line": 3, "column": 0})
        self.fixture.write("extra.js", "// @coord:foo\nlet x = 1;\n")
        self.assertTrue(any(e["code"] == "duplicate_anchor" for e in build_index(project)["errors"]))
        symbols = python_symbols("def café():\n    return 'é'\n")
        self.assertEqual(symbols[0]["end"]["column"], len("    return 'é'"))

    def test_paths_symlink_flags_and_percent_ids(self):
        self.fixture.graph["nodes"][2]["critical"] = "yes"
        self.fixture.graph["nodes"][3]["id"] = "fn:bar%20stable"
        self.fixture.save()
        errors = self.fixture.project().errors
        self.assertTrue(any(e["code"] == "node_flag" for e in errors))
        self.assertFalse(any(e["code"] == "node_id" for e in errors))
        with self.assertRaises(SuiteError):
            safe_path(self.fixture.root, "../escape")
        external = tempfile.TemporaryDirectory()
        self.addCleanup(external.cleanup)
        (self.fixture.root / "external").symlink_to(external.name)
        with self.assertRaises(SuiteError):
            atomic_json(self.fixture.root, "external/file.json", {})
        self.fixture.graph["nodes"][2]["critical"] = True
        self.fixture.graph["nodes"][3]["id"] = "fn:bar"
        self.fixture.save()
        self.assertTrue(any(e["code"] == "unindexed_symlink" for e in build_index(self.fixture.project())["errors"]))

    def test_missing_and_malformed_graphs_produce_full_unverified_plans(self):
        self.fixture.graph["nodes"][2]["kind"] = ["function"]
        self.fixture.graph["edges"][0]["source"] = ["product:p"]
        self.fixture.save()
        result = impact(self.fixture.project())
        self.assertEqual(result["mode"], "FULL")
        self.assertFalse(result["provenance_valid"])
        (self.fixture.root / ".testing-suite/graph.json").unlink()
        result = impact(self.fixture.project())
        self.assertEqual(result["selected_tests"], [])
        self.assertFalse(result["provenance_valid"])
        self.assertTrue(any(r["code"] == "invalid_document" for r in result["reasons"]))

    def test_editing_selection_cannot_omit_required_tests(self):
        self.fixture.baseline()
        project = self.fixture.project()
        selection = impact(project, full=True)
        selection["selected_tests"] = ["test:foo"]
        with self.assertRaises(SuiteError):
            verify_selection(project, selection)
        selection = impact(project, nodes=["fn:foo", "fn:bar"])
        selection["selected_tests"] = ["test:foo"]
        with self.assertRaises(SuiteError):
            verify_selection(project, selection)

    def test_exact_state_allowlist_absent_null_array_removal_types(self):
        before = {"a/b": None, "array": [1, 2], "flag": True}
        after = {"array": [1], "flag": 1}
        result = state_diff(before, after, ["/a~1b", "/array/1"])
        self.assertFalse(result["passed"])
        self.assertEqual([change["path"] for change in result["unexpected"]], ["/flag"])
        self.assertEqual(next(c for c in result["changes"] if c["path"] == "/a~1b")["operation"], "remove")
        self.assertFalse(state_diff({"x": {"y": 1}}, {"x": {"y": 2}}, ["/x"])["passed"])
        with self.assertRaises(SuiteError):
            state_diff({}, {}, ["/bad~2escape"])

    def test_parity_requires_scoped_invariant_coverage_and_tested_variance(self):
        graph = self.fixture.graph
        graph["nodes"] += [{"id": "cap:x", "kind": "capability", "name": "x"},
                           {"id": "inst:a", "kind": "instance", "name": "a"},
                           {"id": "inst:b", "kind": "instance", "name": "b"},
                           {"id": "inv:x", "kind": "invariant", "name": "same"}]
        graph["edges"] += [{"source": i, "target": "cap:x", "relation": "implements"} for i in ("inst:a", "inst:b")]
        graph["edges"] += [{"source": "test:foo", "target": "inv:x", "relation": "verifies"},
                           {"source": "test:foo", "target": "inst:a", "relation": "covers"}]
        graph["parity_groups"] = [{"id": "parity:x", "capability": "cap:x", "instances": ["inst:a", "inst:b"], "shared_invariants": ["inv:x"], "variances": []}]
        self.fixture.save()
        self.assertFalse(parity(self.fixture.project())["passed"])
        graph["edges"] += [{"source": "test:bar", "target": "inv:x", "relation": "verifies"},
                           {"source": "test:bar", "target": "inst:b", "relation": "covers"}]
        graph["parity_groups"][0]["variances"] = [{"instance": "inst:b", "invariant": "inv:x", "reason": "different locale", "test": "test:bar"}]
        self.fixture.save()
        self.assertTrue(parity(self.fixture.project())["passed"])
        graph["parity_groups"][0]["variances"][0]["test"] = "test:foo"
        self.fixture.save()
        self.assertFalse(parity(self.fixture.project())["passed"])


if __name__ == "__main__":
    unittest.main()
