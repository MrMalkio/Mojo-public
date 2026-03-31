#!/usr/bin/env python3
"""
package_skill.py — Asana Plugin packager

Bundles all skill files into a single distributable archive and generates
a manifest. Run from the asana-plugin/ directory or pass --root.

Usage:
    python scripts/package_skill.py
    python scripts/package_skill.py --root /path/to/asana-plugin --out /path/to/dist
    python scripts/package_skill.py --validate-only

Output:
    dist/asana-plugin-{version}.tar.gz
    dist/asana-plugin-{version}-manifest.json
"""

import argparse
import hashlib
import json
import os
import tarfile
import sys
from datetime import datetime, timezone
from pathlib import Path

# Files/dirs to exclude from package
EXCLUDE_PATTERNS = {
    "__pycache__",
    ".DS_Store",
    "*.pyc",
    "*.env",          # Never package PATs
    "*.env.*",
    "cirra.env",
    "work-log-*.md",  # Session logs are ephemeral
    "scripts",        # Don't bundle the packager itself
}

# Required files — packaging fails if any are missing
REQUIRED_FILES = [
    "SKILL.md",
    "skills/README.md",
    "skills/searching/SKILL.md",
    "skills/creating/SKILL.md",
    "skills/updating/SKILL.md",
    "skills/commenting/SKILL.md",
    "skills/structuring/SKILL.md",
    "skills/prioritizing/SKILL.md",
    "skills/combos/SKILL.md",
    "skills/work-tracking/SKILL.md",
    "skills/context-validate/SKILL.md",
    "skills/maintenance/SKILL.md",
    "protocols/PROGRESS-FUNNEL.md",
    "protocols/TASK-PREP.md",
    "protocols/NOTIFICATION-HYGIENE.md",
    "protocols/DAILY-UPDATE.md",
    "protocols/INBOX.md",
    "agent/INSTALL.md",
    "evals/evals.json",
]

# Optional files — included if present, no failure if absent
OPTIONAL_FILES = [
    "index/PROJECTS.md",
    "index/FIELDS.md",
    "index/PLAYERS.md",
    "index/options/OPTIONS-core.md",
    "index/options/OPTIONS-work.md",
    "index/options/OPTIONS-feature.md",
    "agent/CONTRIBUTIONS.md",
    "TEST-MATRIX.md",
]


def should_exclude(path: Path) -> bool:
    name = path.name
    for pattern in EXCLUDE_PATTERNS:
        if "*" in pattern:
            import fnmatch
            if fnmatch.fnmatch(name, pattern):
                return True
        elif name == pattern:
            return True
    return False


def hash_file(path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_version(root: Path) -> str:
    """Extract version from SKILL.md frontmatter, fall back to date."""
    skill_md = root / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text()
        for line in content.splitlines():
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip().strip('"')
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def collect_files(root: Path) -> list[Path]:
    """Collect all files to include, respecting exclusions."""
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        # Check each component of the path for exclusions
        if any(should_exclude(Path(part)) for part in rel.parts):
            continue
        files.append(path)
    return files


def validate(root: Path) -> list[str]:
    """Check all required files exist. Returns list of missing files."""
    missing = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            missing.append(rel)
    return missing


def build_manifest(root: Path, files: list[Path], version: str) -> dict:
    manifest = {
        "name": "asana-plugin",
        "version": version,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "workspace_gid": "9526911872029",
        "file_count": len(files),
        "files": {},
        "required_present": [],
        "optional_present": [],
        "optional_absent": [],
    }
    for path in files:
        rel = str(path.relative_to(root))
        manifest["files"][rel] = {
            "size_bytes": path.stat().st_size,
            "sha256": hash_file(path),
        }
    for f in REQUIRED_FILES:
        if (root / f).exists():
            manifest["required_present"].append(f)
    for f in OPTIONAL_FILES:
        if (root / f).exists():
            manifest["optional_present"].append(f)
        else:
            manifest["optional_absent"].append(f)
    return manifest


def package(root: Path, out_dir: Path, version: str, files: list[Path]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    archive_name = f"asana-plugin-{version}.tar.gz"
    archive_path = out_dir / archive_name

    with tarfile.open(archive_path, "w:gz") as tar:
        for path in files:
            arcname = f"asana-plugin/{path.relative_to(root)}"
            tar.add(path, arcname=arcname)

    return archive_path


def main():
    parser = argparse.ArgumentParser(description="Package the Asana plugin skill.")
    parser.add_argument("--root", type=Path, default=Path(__file__).parent.parent,
                        help="Root of the asana-plugin directory")
    parser.add_argument("--out", type=Path, default=None,
                        help="Output directory (default: {root}/dist)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Only validate required files, don't build")
    args = parser.parse_args()

    root = args.root.resolve()
    out_dir = args.out.resolve() if args.out else root / "dist"

    print(f"Root: {root}")

    # Validate
    missing = validate(root)
    if missing:
        print(f"\n❌ VALIDATION FAILED — {len(missing)} required file(s) missing:")
        for f in missing:
            print(f"   missing: {f}")
        if args.validate_only:
            sys.exit(1)
        print("\n⚠️  Packaging anyway with available files...\n")
    else:
        print(f"✅ All {len(REQUIRED_FILES)} required files present.")

    if args.validate_only:
        # Report optional files too
        for f in OPTIONAL_FILES:
            status = "✅" if (root / f).exists() else "⚠️  absent"
            print(f"   {status} {f}")
        sys.exit(0)

    # Collect and package
    version = get_version(root)
    files = collect_files(root)
    print(f"Version: {version}")
    print(f"Files to package: {len(files)}")

    archive_path = package(root, out_dir, version, files)
    manifest = build_manifest(root, files, version)

    manifest_path = out_dir / f"asana-plugin-{version}-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    archive_size_kb = archive_path.stat().st_size / 1024
    print(f"\n✅ Package built:")
    print(f"   Archive:  {archive_path}  ({archive_size_kb:.1f} KB)")
    print(f"   Manifest: {manifest_path}")
    print(f"\nOptional files absent (not blocking):")
    for f in manifest["optional_absent"]:
        print(f"   ⚠️  {f}")


if __name__ == "__main__":
    main()
