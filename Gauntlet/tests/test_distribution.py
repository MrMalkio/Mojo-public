"""Exercise the distributed bootstrapper, installed skill, and native runner."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dist_packager", ROOT / "scripts/package_skill.py")
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


def execute(args, cwd):
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if completed.returncode:
        raise AssertionError(f"Command failed ({completed.returncode}): {args}\n{completed.stdout}\n{completed.stderr}")
    return completed


class DistributionTests(unittest.TestCase):
    def test_archive_install_cold_skill_bootstrap_and_runner_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            out = base / "dist"
            PACKAGER.build(ROOT, out)
            with tarfile.open(out / "testing-suite-0.1.0.tar.gz") as archive:
                for member in archive.getmembers():
                    self.assertTrue(member.isfile())
                    target = base / "unpacked" / member.name
                    self.assertTrue(target.resolve().is_relative_to((base / "unpacked").resolve()))
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
            package = base / "unpacked/testing-suite"
            project = base / "project with spaces"
            (project / "tests").mkdir(parents=True)
            (project / "tests/test_sample.py").write_text(
                "import unittest\nclass SampleTests(unittest.TestCase):\n"
                "    def test_addition(self):\n        self.assertEqual(2 + 3, 5)\n"
            )
            execute(["git", "init", "-q"], project)
            execute(["git", "add", "."], project)
            execute(["git", "-c", "user.name=Suite test", "-c", "user.email=suite@example.invalid", "commit", "-qm", "Fixture"], project)
            execute(["python3", str(package / "scripts/bootstrap.py"), "--project", str(project), "--agent", "both", "--ci"], base)
            installed = project / ".agents/skills/testing-suite"
            for relative in ("scripts/bootstrap.py", "scripts/suite.py", "agent/INSTALL.md", "references/ADAPTERS.md", "evals/evals.json"):
                self.assertTrue((installed / relative).is_file(), f"Missing installed skill dependency: {relative}")
            other = base / "second project"
            execute(["python3", str(installed / "scripts/bootstrap.py"), "--project", str(other), "--agent", "none"], base)
            self.assertTrue((other / ".testing-suite/bin/suite.py").is_file())
            suite = ["python3", str(project / ".testing-suite/bin/suite.py"), "--root", str(project)]
            execute(suite + ["validate"], base)
            execute(suite + ["index"], base)
            selection_path = ".testing-suite/state/selection.json"
            selection = project / selection_path
            execute(suite + ["impact", "--full", "--output", selection_path], base)
            self.assertEqual("FULL", json.loads(selection.read_text())["mode"])
            execute(suite + ["run", "--selection", selection_path], base)
            execute(suite + ["gate", "--selection", selection_path], base)
            # Results must become stale after a source edit, even when HEAD did
            # not move and the last run was green.
            with (project / "tests/test_sample.py").open("a") as handle:
                handle.write("\n# changed after execution\n")
            failed = subprocess.run(suite + ["gate", "--selection", selection_path], cwd=base, capture_output=True, text=True)
            self.assertNotEqual(0, failed.returncode)


if __name__ == "__main__":
    unittest.main()
