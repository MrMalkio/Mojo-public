"""Distribution checks: the runnable bootstrapper must survive packaging."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_skill", ROOT / "scripts/package_skill.py")
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


class PackagingTests(unittest.TestCase):
    def test_archive_manifest_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            manifest = PACKAGER.build(ROOT, out)
            first = {name: (out / name).read_bytes() for name in manifest["archives"]}
            second = PACKAGER.build(ROOT, out)
            self.assertEqual(manifest, second)
            self.assertEqual(first, {name: (out / name).read_bytes() for name in second["archives"]})
            for filename, metadata in manifest["archives"].items():
                self.assertEqual(hashlib.sha256(first[filename]).hexdigest(), metadata["sha256"])
            with tarfile.open(out / "testing-suite-0.1.0.tar.gz") as archive:
                names = archive.getnames()
                self.assertIn("testing-suite/scripts/bootstrap.py", names)
                self.assertIn("testing-suite/scripts/suite_core.py", names)
                self.assertTrue(all("/__pycache__/" not in name and "/dist/" not in name for name in names))
                for name, metadata in manifest["files"].items():
                    self.assertEqual(hashlib.sha256(archive.extractfile("testing-suite/" + name).read()).hexdigest(), metadata["sha256"])
            with zipfile.ZipFile(out / "testing-suite-0.1.0.skill") as archive:
                self.assertEqual(set(names), set(archive.namelist()))

    def test_missing_required_file_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Missing required files"):
                PACKAGER.validate(Path(directory))


if __name__ == "__main__":
    unittest.main()
