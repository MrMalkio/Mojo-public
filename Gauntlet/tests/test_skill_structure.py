"""Ensure the installed skill router has all of its local workflow dependencies."""
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {"bootstrap", "map-system", "plan-impact", "design-tests", "run-evidence", "contracts", "instance-parity", "state-diff", "diagnose", "maintain"}


class SkillStructureTests(unittest.TestCase):
    def test_router_workflows_and_frontmatter(self):
        router = (ROOT / "SKILL.md").read_text()
        self.assertEqual(SKILLS, {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")})
        for name in sorted(SKILLS):
            with self.subTest(skill=name):
                self.assertIn(f"skills/{name}/SKILL.md", router)
                source = (ROOT / "skills" / name / "SKILL.md").read_text()
                self.assertRegex(source, r"\A---\nname: testing-suite-[a-z-]+\ndescription:")

    def test_local_document_links_resolve(self):
        for source in ROOT.rglob("*.md"):
            if "dist" in source.relative_to(ROOT).parts:
                continue
            for target in re.findall(r"\]\(([^\s)]+)\)", source.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                target = unquote(target.split("#", 1)[0])
                with self.subTest(source=str(source.relative_to(ROOT)), target=target):
                    self.assertTrue((source.parent / target).exists(), f"Broken local link in {source}: {target}")

    def test_evals_are_scenarios_not_fabricated_results(self):
        scenarios = json.loads((ROOT / "evals/evals.json").read_text())
        self.assertTrue(scenarios)
        # Evals are intentionally not an execution-history artifact.
        text = json.dumps(scenarios).lower()
        self.assertNotIn('"all_passed": true', text)
        self.assertNotIn('"passed": true', text)


if __name__ == "__main__":
    unittest.main()
