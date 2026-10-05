#!/usr/bin/env python3
"""Build portable skill archives and a SHA-256 manifest using only the stdlib."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
import zipfile


EXCLUDED_DIRS = {"dist", ".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "state"}
REQUIRED = [
    "SKILL.md", "README.md", "agent/INSTALL.md", "references/SOURCES.md",
    "references/ADAPTERS.md", "skills/README.md", "evals/evals.json",
    "scripts/bootstrap.py", "scripts/suite.py", "scripts/suite_core.py",
    "schemas/config.schema.json", "schemas/graph.schema.json",
    "schemas/index.schema.json", "schemas/selection.schema.json", "schemas/results.schema.json",
    "protocols/GRAPH-CONVENTIONS.md", "protocols/SELECTION-SAFETY.md", "protocols/EVIDENCE.md",
    "examples/minimal-python/README.md",
]
REQUIRED += [f"skills/{name}/SKILL.md" for name in (
    "bootstrap", "map-system", "plan-impact", "design-tests", "run-evidence",
    "contracts", "instance-parity", "state-diff", "diagnose", "maintain",
)]


def collect(root: Path) -> list[Path]:
    paths = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.name.startswith(".env") or path.suffix in {".pyc", ".pyo", ".pem", ".key"}:
            continue
        if path.is_symlink():
            raise ValueError(f"Refusing to package symlink: {rel}")
        if path.is_file():
            paths.append(path)
    return paths


def validate(root: Path) -> tuple[str, list[Path]]:
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        raise ValueError("Missing required files: " + ", ".join(missing))
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^version:\s*[\"\']?([0-9]+\.[0-9]+\.[0-9]+)', text, re.MULTILINE)
    if not match:
        raise ValueError("SKILL.md requires a semantic version")
    files = collect(root)
    for path in files:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        if path.name == "SKILL.md":
            content = path.read_text(encoding="utf-8")
            if not content.startswith("---\n") or not re.search(r"^name: .+", content, re.MULTILINE) or not re.search(r"^description:", content, re.MULTILINE):
                raise ValueError(f"Invalid skill frontmatter: {path.relative_to(root)}")
    return match.group(1), files


def build(root: Path, out: Path) -> dict:
    version, files = validate(root)
    # Cache bytes before writing, so outputs never enter the same build's inputs.
    payload = [(str(path.relative_to(root)), path.read_bytes()) for path in files]
    if out.resolve() == root.resolve():
        raise ValueError("Output directory must differ from the package root")
    if out.resolve().is_relative_to(root.resolve()) and out.resolve() != (root / "dist").resolve():
        raise ValueError("An output inside the package must use its excluded dist directory")
    out.mkdir(parents=True, exist_ok=True)
    basename = f"testing-suite-{version}"
    archive = out / f"{basename}.tar.gz"
    with archive.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as tar:
            for name, content in payload:
                info = tarfile.TarInfo("testing-suite/" + name)
                info.size = len(content)
                info.mode = 0o644
                info.mtime = 0
                tar.addfile(info, io.BytesIO(content))
    skill = out / f"{basename}.skill"
    with zipfile.ZipFile(skill, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, content in payload:
            info = zipfile.ZipInfo("testing-suite/" + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, content)
    manifest = {
        "name": "testing-suite", "version": version, "file_count": len(payload),
        "files": {name: {"size_bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()} for name, content in payload},
        "archives": {path.name: {"size_bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in (archive, skill)},
    }
    (out / f"{basename}-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if args.validate_only:
            version, files = validate(root)
            print(json.dumps({"valid": True, "version": version, "file_count": len(files)}))
        else:
            print(json.dumps(build(root, args.out or root / "dist"), indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
