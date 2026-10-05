#!/usr/bin/env python3
"""Install an evidence-aware testing suite without altering project implementation."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from urllib.parse import quote
from dataclasses import dataclass

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
IGNORE_BEGIN = "# BEGIN testing-suite managed local state"
IGNORE_END = "# END testing-suite managed local state"
IGNORE_SECTION = (IGNORE_BEGIN + "\n.testing-suite/state/\n.testing-suite/cache/\n" + IGNORE_END + "\n").encode()
EXCLUDED = {".git", ".testing-suite", ".agents", ".claude", "node_modules", ".venv", "venv", "dist", "build", "coverage", "__pycache__", ".tox", ".mypy_cache", ".pytest_cache"}


class BootstrapError(Exception):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "project"


def inspect_path(root: Path, relative: str = "") -> None:
    """Reject symlinks and file ancestors before using a managed output path."""
    current = root
    for ancestor in reversed((root,) + tuple(root.parents)):
        if ancestor.is_symlink():
            raise BootstrapError(f"Project path has a symlink: {ancestor}")
        if ancestor != root and ancestor.exists() and not ancestor.is_dir():
            raise BootstrapError(f"Project parent is not a directory: {ancestor}")
    parts = Path(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            raise BootstrapError(f"Managed output has a symlink: {current}")
        if current.exists() and index < len(parts) - 1 and not current.is_dir():
            raise BootstrapError(f"Managed output parent is not a directory: {current}")


def read_optional(path: Path) -> str:
    if path.is_symlink():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def project_files(root: Path) -> list[Path]:
    result: list[Path] = []
    if not root.exists():
        return result
    for folder, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not (Path(folder) / d).is_symlink())
        for name in sorted(files):
            path = Path(folder) / name
            if not path.is_symlink():
                result.append(path)
    return result


def unittest_methods(path: Path) -> list[str]:
    try:
        tree = ast.parse(read_optional(path))
    except SyntaxError:
        return []
    modules = {alias.asname or alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names if alias.name == "unittest"}
    case_names = {alias.asname or alias.name for node in tree.body if isinstance(node, ast.ImportFrom) and node.module == "unittest" for alias in node.names if alias.name == "TestCase"}
    if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "load_tests" for node in tree.body):
        return []
    methods = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            is_case = any((isinstance(base, ast.Name) and base.id in case_names) or (isinstance(base, ast.Attribute) and base.attr == "TestCase" and isinstance(base.value, ast.Name) and base.value.id in modules) for base in node.bases)
            if is_case:
                methods.extend(node.name + "." + method.name for method in node.body if isinstance(method, ast.FunctionDef) and method.name.startswith("test"))
    return methods


def infer(root: Path, profile: str) -> tuple[list[dict], list[dict], list[str], list[str]]:
    """Read manifests and source conventions; never execute detection commands."""
    files = project_files(root)
    nested_roots = {p.parent for p in files if p.name in {"package.json", "pyproject.toml"} and p.parent != root}
    python_tests = [p for p in files if p.suffix == ".py" and (p.name.startswith("test_") or p.name.endswith("_test.py"))]
    node_tests = [p for p in files if p.suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"} and (re.search(r"\.(?:test|spec)\.", p.name) or "__tests__" in p.relative_to(root).parts)]
    python_declared = any((root / name).is_file() for name in ("pyproject.toml", "setup.py", "setup.cfg", "pytest.ini", "tox.ini"))
    node_declared = (root / "package.json").is_file() and not (root / "package.json").is_symlink()
    detected = []
    if python_declared or python_tests:
        detected.append("python")
    if node_declared or node_tests:
        detected.append("node")
    enabled = detected if profile == "auto" else ([] if profile == "generic" else [profile])
    runners: list[dict] = []
    tests: list[dict] = []
    warnings: list[str] = []
    for language, paths in (("python", python_tests), ("node", node_tests)):
        for path in paths:
            relative = path.relative_to(root).as_posix()
            tests.append({"id": "test:" + quote(relative, safe="/._-"), "kind": "test", "name": relative, "repo": "repo:main", "path": relative, "last_status": "unknown"})
    if "python" in enabled:
        declaration = "\n".join(read_optional(root / name) for name in ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt", "requirements-test.txt", "pytest.ini", "tox.ini"))
        pytest_declared = bool(re.search(r"\bpytest\b", declaration)) or (root / "pytest.ini").is_file()
        if pytest_declared and python_tests:
            runners.append({"id": "python-pytest", "command": ["python3", "-m", "pytest"]})
            warnings.append("Pytest runner inventory is available, but testpaths, collection filters and subproject boundaries require verified manual test-to-runner mappings; no inferred pytest coverage is claimed.")
        else:
            for number, path in enumerate(sorted(python_tests), 1):
                methods = unittest_methods(path)
                if not path.stem.isidentifier() or any(parent in path.parents for parent in nested_roots) or not methods:
                    continue
                parent = path.parent.relative_to(root).as_posix()
                runner_id = f"python-unittest-{number}"
                runners.append({"id": runner_id, "adapter": "unittest", "command": ["python3", "-m", "unittest", "discover", "-s", parent, "-p", path.name, "-v"]})
                original = next(test for test in tests if test["path"] == path.relative_to(root).as_posix())
                tests.remove(original)
                tests.extend({**original, "id": original["id"] + "::" + quote(method, safe="._-"), "name": original["path"] + "::" + method, "symbol": method, "runner": runner_id} for method in methods)
            if runners:
                warnings.append("Unittest mappings use explicit TestCase classes and test methods with exact-file discovery. Gate evidence records the configured runner invocation; review custom loaders, skipped cases and environment requirements.")
    if "node" in enabled and node_declared:
        try:
            package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise BootstrapError(f"Cannot read package.json: {error}") from error
        if not isinstance(package, dict):
            raise BootstrapError("package.json must contain an object")
        scripts = package.get("scripts", {})
        if not isinstance(scripts, dict):
            raise BootstrapError("package.json scripts must contain an object")
        lock_managers = {manager for manager, names in (("npm", ("package-lock.json", "npm-shrinkwrap.json")), ("pnpm", ("pnpm-lock.yaml",)), ("yarn", ("yarn.lock",)), ("bun", ("bun.lock", "bun.lockb"))) if any((root / name).is_file() for name in names)}
        explicit = package.get("packageManager", "")
        declared_manager = explicit.split("@", 1)[0] if isinstance(explicit, str) else ""
        if len(lock_managers) > 1 or (declared_manager and lock_managers and declared_manager not in lock_managers) or (declared_manager and declared_manager not in {"npm", "pnpm", "yarn", "bun"}):
            warnings.append("Conflicting or unsupported package manager declarations; Node runner inference is unavailable. Choose and record the real command manually.")
        else:
            manager = declared_manager or next(iter(lock_managers), "npm")
            candidates = [(name, command) for name, command in scripts.items() if isinstance(name, str) and isinstance(command, str) and (name == "test" or name.startswith("test:")) and command.strip() and not re.search(r"no test specified|(?:^|[\s:-])watch(?:$|[\s:-])|--watch|--ui", name + " " + command, re.I)]
            for name, _ in sorted(candidates):
                runners.append({"id": "node:" + quote(name, safe=":._-"), "command": [manager, "run", name]})
            if candidates:
                warnings.append("Node scripts were preserved as configured runners. Their test-file coverage must be verified and mapped manually; no inferred Node coverage is claimed.")
    if len(detected) > 1:
        warnings.append("Mixed Python/Node project detected. Auto profile retains both runner inventories; review mappings for every language.")
    nested = [p.relative_to(root).as_posix() for p in files if p.name in {"package.json", "pyproject.toml"} and p.parent != root]
    if nested:
        warnings.append("Nested manifests detected: " + ", ".join(nested) + ". Root bootstrap does not infer workspace/subproject execution; add their repositories and runners explicitly.")
    unbound = sum("runner" not in test for test in tests)
    if unbound:
        warnings.append(f"{unbound} discovered test file(s) have no verified runner mapping. Execution gate setup needs manual mapping.")
    unmapped_runners = {runner["id"] for runner in runners} - {test.get("runner") for test in tests}
    if unmapped_runners:
        warnings.append("Runner inventory has no verified test mapping for: " + ", ".join(sorted(unmapped_runners)) + ". Execution gate setup remains unavailable until coverage is mapped.")
    if not runners:
        warnings.append("No supported existing test runner was discovered. Inventory validation is available; test execution is unavailable until an actual runner is configured.")
    return runners, tests, warnings, detected


def ignore_contents(root: Path) -> bytes:
    inspect_path(root, ".gitignore")
    path = root / ".gitignore"
    if path.exists() and not path.is_file():
        raise BootstrapError(f"Managed output is not a file: {path}")
    existing = path.read_bytes() if path.exists() else b""
    begin, end = IGNORE_BEGIN.encode(), IGNORE_END.encode()
    if begin in existing or end in existing:
        if existing.count(begin) != 1 or existing.count(end) != 1:
            raise BootstrapError(".gitignore contains duplicate or incomplete testing-suite managed markers")
        start = existing.index(begin)
        finish = existing.index(end) + len(end)
        if start and existing[start - 1:start] != b"\n":
            raise BootstrapError(".gitignore managed marker is not on its own line")
        if existing[finish:finish + 1] not in (b"", b"\n"):
            raise BootstrapError(".gitignore managed end marker is not on its own line")
        section = existing[start:finish] + b"\n"
        if section != IGNORE_SECTION:
            raise BootstrapError(".gitignore has a modified testing-suite managed section")
        return existing
    return existing + (b"\n" if existing and not existing.endswith(b"\n") else b"") + IGNORE_SECTION


def package_payload() -> dict[str, bytes]:
    # Ship a complete, relocatable source package so routed skills retain their
    # references, bootstrap command, fixtures and verification material.
    payload: dict[str, bytes] = {}
    for required in ("SKILL.md", "README.md", "skills", "protocols", "references", "schemas"):
        source = PACKAGE_ROOT / required
        if not source.exists() or source.is_symlink():
            raise BootstrapError(f"Suite package is incomplete: {source}")
    excluded = {".git", "dist", "__pycache__", "node_modules", ".venv", "venv", ".agents", ".claude", "cache", "state"}
    for folder, dirs, files in os.walk(PACKAGE_ROOT, followlinks=False):
        for directory in dirs:
            if directory not in excluded and (Path(folder) / directory).is_symlink():
                raise BootstrapError(f"Suite package contains a symlink: {Path(folder) / directory}")
        dirs[:] = sorted(directory for directory in dirs if directory not in excluded)
        for filename in sorted(files):
            path = Path(folder) / filename
            if filename.startswith(".env") or path.suffix.lower() in {".pyc", ".pyo", ".pem", ".key"}:
                continue
            if path.is_symlink():
                raise BootstrapError(f"Suite package contains a symlink: {path}")
            payload[path.relative_to(PACKAGE_ROOT).as_posix()] = path.read_bytes()
    return payload


def ci_contents(execution_ready: bool) -> bytes:
    steps = """      - name: Validate inventory
        run: python3 .testing-suite/bin/suite.py --root . validate
      - name: Build source index
        run: python3 .testing-suite/bin/suite.py --root . index
"""
    if execution_ready:
        steps += """      - name: Select full suite
        run: python3 .testing-suite/bin/suite.py --root . impact --full --output .testing-suite/state/selection.json
      - name: Execute configured runners and record evidence
        run: python3 .testing-suite/bin/suite.py --root . run --selection .testing-suite/state/selection.json
      - name: Require passed execution evidence
        run: python3 .testing-suite/bin/suite.py --root . gate --selection .testing-suite/state/selection.json
"""
    else:
        steps += """      - name: Report execution setup status
        run: echo 'Inventory validated. Execution gate unavailable; configure and verify runner mappings before enabling execution steps.'
"""
    return ("""name: Testing suite
on: [push, pull_request]
permissions:
  contents: read
jobs:
  testing-suite:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      # Add this project's approved dependency/environment setup before execution.
""" + steps).encode()


def build_plan(root: Path, name: str, profile: str, agent: str, ci: bool, capability: str | None) -> tuple[dict[str, bytes], list[str], list[str]]:
    runners, tests, warnings, detected = infer(root, profile)
    project_id = "project:" + slug(name)
    graph = {"schema_version": 1, "nodes": [{"id": project_id, "kind": "product", "name": name}, {"id": "repo:main", "kind": "repository", "name": root.name or name, "repo": "repo:main"}] + tests, "edges": [{"source": project_id, "target": "repo:main", "relation": "contains"}] + [{"source": "repo:main", "target": test["id"], "relation": "contains"} for test in tests], "parity_groups": []}
    config = {"schema_version": 1, "project": {"id": project_id, "name": name}, "repositories": [{"id": "repo:main", "path": "."}], "policy": {"full_suite_every_days": 7, "always_include_critical": True}, "runners": runners}
    ready = bool(tests) and bool(runners) and all("runner" in test for test in tests) and {test["runner"] for test in tests} == {runner["id"] for runner in runners}
    inventory = "# Source map and mapping inventory\n\nOnly project/repository identities and actual discovered test paths are seeded. No capability coverage or passing evidence is asserted.\n\n"
    if capability:
        inventory += "Requested capability to map: " + json.dumps(capability, ensure_ascii=False) + ". This is an unclaimed mapping task, not a coverage claim.\n\n"
    inventory += "Map real capabilities → behaviors → code units → tests in graph.json. Use stable function coordinates such as `@coord:review.toggle`, exact repo-relative paths and symbol names where available. Confirm each test's runner actually collects it; record concrete evidence on dependency, covers and parity edges. Assign critical/new flags only from project facts. Add parity groups only when equivalent implementations and their shared contract have been verified. Run index after mapping changes. Read the installed protocols/GRAPH-CONVENTIONS.md and references for the complete contract.\n\n"
    inventory += "Detected profiles: " + (", ".join(detected) or "generic") + ".\n\n"
    inventory += "\n".join("- " + warning for warning in warnings) + "\n"
    readme = """# Project testing suite

This bootstrap preserved project code, manifests and agent instruction files. Edit config.json and graph.json to map verified project facts; SOURCE-MAP.md lists inference limits. No tests were run during installation. No dependencies were installed.

From the project root:

```sh
python3 .testing-suite/bin/suite.py --root . validate
python3 .testing-suite/bin/suite.py --root . index
python3 .testing-suite/bin/suite.py --root . impact --full --output .testing-suite/state/selection.json
python3 .testing-suite/bin/suite.py --root . run --selection .testing-suite/state/selection.json
python3 .testing-suite/bin/suite.py --root . gate --selection .testing-suite/state/selection.json
```

Execution requires actual runner commands, test mappings and this project's normal approved environment setup. Unmapped tests block a gate. Local state and cache are ignored by Git. Generated inventories remain reviewable tracked files; they contain no fabricated pass results.

Agent skills live in the selected agent's native skills directory. agent-instructions.md contains optional text to append to an existing AGENTS.md or CLAUDE.md yourself. This bootstrap never overwrites those files.

Rerun the same bootstrap command to verify an unchanged installation. Any differing generated file is a collision and stops the entire operation; review changes manually to upgrade or change the inventory. The manifest records installed file hashes. To remove the installation, review that manifest and remove only files still matching its hashes, the exact managed .gitignore section and empty managed directories. Preserve files you edited.
"""
    if ci:
        readme += "\nGitHub CI was requested. " + ("The workflow runs the full mapped suite and requires execution evidence; add the project's dependency/environment setup before using it.\n" if ready else "The workflow validates and indexes inventory only. Execution is unavailable until real runner mappings are supplied and verified.\n")
    instructions = """# Optional project agent instructions

Append the following text to the project's existing AGENTS.md or CLAUDE.md when appropriate:

Use the installed `testing-suite` skill to maintain `.testing-suite/config.json` and `.testing-suite/graph.json`. Map verified capabilities, behaviors, code coordinates and tests before claiming coverage. Run `.testing-suite/bin/suite.py --root . validate` and `index`, select impacted tests with `impact`, then execute `run` and require a passing `gate`. Include critical tests, regression tests for fixes and the periodic full suite. A source map, manual note or mocked expectation is not execution evidence. Record missing infrastructure and unmapped coverage honestly. Obtain project-required approval for external effects or destructive commands.
"""
    outputs = {".testing-suite/config.json": encoded(config), ".testing-suite/graph.json": encoded(graph), ".testing-suite/README.md": readme.encode(), ".testing-suite/SOURCE-MAP.md": inventory.encode(), ".testing-suite/agent-instructions.md": instructions.encode(), ".gitignore": ignore_contents(root)}
    for filename in ("suite.py", "suite_core.py"):
        source = PACKAGE_ROOT / "scripts" / filename
        if not source.is_file() or source.is_symlink():
            raise BootstrapError(f"Suite package is incomplete: {source}")
        outputs[".testing-suite/bin/" + filename] = source.read_bytes()
    directories = [".testing-suite/state", ".testing-suite/cache"]
    if agent != "none":
        payload = package_payload()
        for selected in (("codex", "claude") if agent == "both" else (agent,)):
            prefix = ".agents/skills/testing-suite" if selected == "codex" else ".claude/skills/testing-suite"
            outputs.update({prefix + "/" + key: data for key, data in payload.items()})
            directories.extend(prefix + "/" + required for required in ("skills", "protocols", "references", "schemas"))
    if ci:
        outputs[".github/workflows/testing-suite.yml"] = ci_contents(ready)
    manifest = {"schema_version": 1, "tool": "testing-suite-bootstrap", "options": {"name": name, "profile": profile, "agent": agent, "ci": ci, "capability": capability}, "files": {path: {"sha256": digest(data)} for path, data in sorted(outputs.items()) if path != ".gitignore"}, "gitignore_section_sha256": digest(IGNORE_SECTION), "directories": sorted(directories)}
    outputs[".testing-suite/bootstrap-manifest.json"] = encoded(manifest)
    return outputs, warnings, directories


@dataclass
class PlannedFile:
    relative: str
    content: bytes
    previous: bytes | None
    action: str


def preflight(root: Path, outputs: dict[str, bytes], directories: list[str]) -> list[PlannedFile]:
    if root.exists() and not root.is_dir():
        raise BootstrapError(f"Project path is not a directory: {root}")
    inspect_path(root)
    plan: list[PlannedFile] = []
    for relative in sorted(outputs):
        inspect_path(root, relative)
        path = root / relative
        if path.exists() and not path.is_file():
            raise BootstrapError(f"Managed output is not a file: {path}")
        previous = path.read_bytes() if path.exists() else None
        if previous is not None and previous != outputs[relative] and relative != ".gitignore":
            raise BootstrapError(f"Collision: existing file differs: {path}. No files were changed.")
        plan.append(PlannedFile(relative, outputs[relative], previous, "unchanged" if previous == outputs[relative] else ("append-managed-section" if relative == ".gitignore" and previous is not None else "create")))
    for relative in directories:
        inspect_path(root, relative)
        if (root / relative).exists() and not (root / relative).is_dir():
            raise BootstrapError(f"Managed directory is not a directory: {root / relative}")
    return plan


def atomic_write(path: Path, data: bytes) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".testing-suite-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install(root: Path, plan: list[PlannedFile], directories: list[str]) -> None:
    created_dirs: list[Path] = []
    written: list[PlannedFile] = []

    def mkdir(path: Path) -> None:
        missing: list[Path] = []
        current = path
        while not current.exists():
            if current.is_symlink():
                raise BootstrapError(f"Directory is a symlink: {current}")
            missing.append(current)
            current = current.parent
        if current.is_symlink() or not current.is_dir():
            raise BootstrapError(f"Output parent is unsafe: {current}")
        for directory in reversed(missing):
            directory.mkdir()
            created_dirs.append(directory)

    try:
        for item in plan:
            inspect_path(root, item.relative)
            destination = root / item.relative
            current = destination.read_bytes() if destination.exists() else None
            if current != item.previous:
                raise BootstrapError(f"Concurrent change detected: {destination}")
            if item.action == "unchanged":
                continue
            mkdir(destination.parent)
            inspect_path(root, item.relative)
            atomic_write(destination, item.content)
            written.append(item)
        for relative in directories:
            inspect_path(root, relative)
            mkdir(root / relative)
    except Exception:
        for item in reversed(written):
            destination = root / item.relative
            # Never overwrite a subsequent user edit during rollback.
            if not destination.is_symlink() and destination.is_file() and destination.read_bytes() == item.content:
                if item.previous is None:
                    destination.unlink()
                else:
                    atomic_write(destination, item.previous)
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--name")
    parser.add_argument("--profile", choices=("auto", "python", "node", "generic"), default="auto")
    parser.add_argument("--agent", choices=("codex", "claude", "both", "none"), default="codex")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ci", action="store_true", help="Opt in to a GitHub workflow; dependency setup remains project-owned")
    parser.add_argument("--capability", help="Requested capability to inventory; does not assert coverage")
    args = parser.parse_args(argv)
    root = Path(os.path.abspath(args.project.expanduser()))
    name = args.name or root.name or "project"
    try:
        inspect_path(root)
        if root.exists() and not root.is_dir():
            raise BootstrapError(f"Project path is not a directory: {root}")
        outputs, warnings, directories = build_plan(root, name, args.profile, args.agent, args.ci, args.capability)
        plan = preflight(root, outputs, directories)
        summary = {"schema_version": 1, "dry_run": args.dry_run, "project": str(root), "files": [{"path": item.relative, "action": item.action, "sha256": digest(item.content)} for item in plan], "directories": [{"path": relative, "action": "unchanged" if (root / relative).is_dir() else "create"} for relative in directories], "warnings": warnings}
        if not args.dry_run:
            install(root, plan, directories)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    except (BootstrapError, OSError) as error:
        print(f"bootstrap: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
