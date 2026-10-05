"""Conservative testing graph tooling. Python standard library only.

This module never runs project commands implicitly. ``run`` is the explicit
boundary: a configured runner's exit status is suite-level evidence, not a
claim that individual cases were independently observed.
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import tokenize
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


KINDS = {"product", "system", "repository", "capability", "instance", "page",
         "ui", "action", "function", "block", "data", "api", "service",
         "resource", "invariant", "test", "file"}
RELATIONS = {"contains", "implements", "depends_on", "invokes", "reads", "writes",
             "consumes", "provides", "covers", "verifies"}
DEPENDENCIES = RELATIONS - {"contains", "implements"}
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", ".venv", "venv",
             "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
             "htmlcov", "coverage", "dist", "build", ".next", ".agents", ".claude"}
SKIP_FILES = {".coverage", ".DS_Store"}
IDENTIFIER = re.compile(r"^[^\s\x00]+$")
ANCHOR = re.compile(r"@coord:(?:<([A-Za-z0-9][A-Za-z0-9_.:/-]*)>|([A-Za-z0-9][A-Za-z0-9_.:/-]*))")


class SuiteError(Exception):
    """A reviewable input or evidence error, rather than an internal traceback."""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode("utf-8")).hexdigest()


def file_hash(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def safe_path(root, relative, *, allow_dot=False):
    """Resolve project-relative paths without traversing any symlinks."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise SuiteError("Paths must be nonempty portable relative paths")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or (relative == "." and not allow_dot):
        raise SuiteError("Path escapes the project or names its root: " + relative)
    root = Path(root).resolve()
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise SuiteError("Symlink paths are not followed: " + relative)
    if not current.resolve().is_relative_to(root):
        raise SuiteError("Path escapes project: " + relative)
    return current


def read_json(path):
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, UnicodeError, ValueError) as exc:
        raise SuiteError("Cannot read JSON {}: {}".format(path, exc)) from exc


def atomic_json(root, relative, value):
    path = safe_path(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Recheck after mkdir; an existing state-directory symlink is never accepted.
    path = safe_path(root, relative)
    descriptor, temporary = tempfile.mkstemp(prefix=".suite-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def git(root, *args, check=False):
    try:
        completed = subprocess.run(["git", "-C", str(root), *args],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        if check:
            raise SuiteError("Git unavailable: " + str(exc)) from exc
        return None
    if completed.returncode:
        if check:
            raise SuiteError("Git command failed: " + completed.stderr.decode("utf-8", "replace").strip())
        return None
    return completed.stdout


def git_head(path):
    result = git(path, "rev-parse", "--verify", "HEAD")
    return result.decode().strip() if result else None


def excluded(relative):
    parts = Path(relative).parts
    return (any(part in SKIP_DIRS for part in parts)
            or Path(relative).name in SKIP_FILES
            or any(parts[i:i + 2] == (".testing-suite", "state") for i in range(len(parts) - 1))
            or Path(relative).suffix in {".pyc", ".pyo"})


def source_snapshot(root):
    """Hash source bytes, including untracked files; never dereference symlinks."""
    files, warnings = {}, []
    for directory, directories, names in os.walk(root, followlinks=False):
        base = Path(directory)
        kept = []
        for name in sorted(directories):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if excluded(relative):
                continue
            if path.is_symlink():
                files[relative] = "symlink:" + os.readlink(path)
                warnings.append({"code": "symlink_ignored", "path": relative,
                                 "message": "Symlink directory was fingerprinted but not followed"})
            else:
                kept.append(name)
        directories[:] = kept
        for name in sorted(names):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if excluded(relative):
                continue
            if path.is_symlink():
                files[relative] = "symlink:" + os.readlink(path)
                warnings.append({"code": "symlink_ignored", "path": relative,
                                 "message": "Symlink file was fingerprinted but not followed"})
                continue
            if not path.is_file():
                raise SuiteError("Source contains a nonregular file: " + relative)
            try:
                files[relative] = file_hash(path)
            except OSError as exc:
                raise SuiteError("Cannot fingerprint " + relative + ": " + str(exc)) from exc
    return files, warnings


def issue(code, message, **fields):
    return {"code": code, "message": message, **fields}


class Project:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise SuiteError("Project root is not a directory")
        load_errors = []
        documents = {}
        for name in ("config", "graph"):
            try:
                documents[name] = read_json(safe_path(self.root, ".testing-suite/" + name + ".json"))
            except SuiteError as exc:
                documents[name] = {}
                load_errors.append(issue("invalid_document", str(exc), document=name))
        self.config, self.graph = documents["config"], documents["graph"]
        self.errors = load_errors + self._validate()
        def array(document, field):
            value = document.get(field, []) if isinstance(document, dict) else []
            return value if isinstance(value, list) else []
        self.nodes = {n["id"]: n for n in array(self.graph, "nodes")
                      if isinstance(n, dict) and isinstance(n.get("id"), str)}
        self.edges = [e for e in array(self.graph, "edges") if isinstance(e, dict)]
        self.repositories = {r["id"]: r for r in array(self.config, "repositories")
                             if isinstance(r, dict) and isinstance(r.get("id"), str)}
        self.runners = {r["id"]: r for r in array(self.config, "runners")
                        if isinstance(r, dict) and isinstance(r.get("id"), str)}

    def _validate(self):
        errors = []
        for name, document in (("config", self.config), ("graph", self.graph)):
            if (not isinstance(document, dict) or type(document.get("schema_version")) is not int
                    or document.get("schema_version") != 1):
                errors.append(issue("schema_version", name + " must be an object with schema_version 1"))
        if errors:
            return errors
        project = self.config.get("project")
        if not isinstance(project, dict) or not all(isinstance(project.get(k), str) and project[k] for k in ("id", "name")):
            errors.append(issue("project", "config.project requires id and name"))
        repositories = self.config.get("repositories")
        repo_ids = set()
        if not isinstance(repositories, list) or not repositories:
            errors.append(issue("repositories", "At least one repository is required"))
            repositories = []
        for repository in repositories:
            if not isinstance(repository, dict) or not self._id(repository.get("id")):
                errors.append(issue("repository", "Repository requires a stable id"))
                continue
            if repository["id"] in repo_ids:
                errors.append(issue("duplicate_id", "Duplicate repository id: " + repository["id"]))
            repo_ids.add(repository["id"])
            try:
                path = safe_path(self.root, repository.get("path"), allow_dot=True)
                if not path.is_dir():
                    raise SuiteError("Repository path must be an existing directory")
            except SuiteError as exc:
                errors.append(issue("repository_path", str(exc), repo=repository["id"]))
        policy = self.config.get("policy", {})
        if not isinstance(policy, dict):
            errors.append(issue("policy", "policy must be an object"))
        else:
            days = policy.get("full_suite_every_days", 7)
            if isinstance(days, bool) or not isinstance(days, int) or days < 1:
                errors.append(issue("policy", "full_suite_every_days must be greater than zero"))
            if not isinstance(policy.get("always_include_critical", True), bool):
                errors.append(issue("policy", "always_include_critical must be a boolean"))
        runners = self.config.get("runners", [])
        runner_ids = set()
        if not isinstance(runners, list):
            errors.append(issue("runners", "runners must be an array"))
            runners = []
        for runner in runners:
            if not isinstance(runner, dict) or not self._id(runner.get("id")):
                errors.append(issue("runner", "Runner requires a stable id"))
                continue
            if runner["id"] in runner_ids:
                errors.append(issue("duplicate_id", "Duplicate runner id: " + runner["id"]))
            runner_ids.add(runner["id"])
            command = runner.get("command")
            if not isinstance(command, list) or not command or not all(isinstance(a, str) and a and "\x00" not in a for a in command):
                errors.append(issue("runner_command", "Runner command must be a nonempty string argument array", runner=runner["id"]))
            timeout = runner.get("timeout_seconds", 300)
            if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
                errors.append(issue("runner_timeout", "timeout_seconds must be positive", runner=runner["id"]))
            try:
                cwd = safe_path(self.root, runner.get("cwd", "."), allow_dot=True)
                if not cwd.is_dir():
                    raise SuiteError("Runner cwd is not an existing directory")
            except SuiteError as exc:
                errors.append(issue("runner_cwd", str(exc), runner=runner["id"]))
        nodes = self.graph.get("nodes")
        node_ids = set()
        if not isinstance(nodes, list):
            errors.append(issue("nodes", "graph.nodes must be an array"))
            nodes = []
        repo_map = {r.get("id"): r for r in repositories
                    if isinstance(r, dict) and isinstance(r.get("id"), str)}
        for node in nodes:
            if not isinstance(node, dict) or not self._id(node.get("id")):
                errors.append(issue("node_id", "Every node requires a stable id; line numbers are not identities"))
                continue
            node_id = node["id"]
            if node_id in node_ids:
                errors.append(issue("duplicate_id", "Duplicate node: " + node_id))
            node_ids.add(node_id)
            if not isinstance(node.get("kind"), str) or node["kind"] not in KINDS:
                errors.append(issue("node_kind", "Unknown node kind", node=node_id))
            if not isinstance(node.get("name"), str) or not node["name"]:
                errors.append(issue("node_name", "Every node requires a name", node=node_id))
            if "repo" in node and (not isinstance(node["repo"], str) or node["repo"] not in repo_ids):
                errors.append(issue("node_repo", "Unknown repository", node=node_id))
            if "path" in node:
                if not isinstance(node.get("repo"), str) or node["repo"] not in repo_ids:
                    errors.append(issue("node_repo", "Path-bound nodes require a repository", node=node_id))
                else:
                    try:
                        repository = repo_map[node["repo"]]
                        repo_path = safe_path(self.root, repository["path"], allow_dot=True)
                        path = safe_path(repo_path, node["path"])
                        if not path.is_file():
                            raise SuiteError("Node path is not an existing file: " + node["path"])
                    except SuiteError as exc:
                        errors.append(issue("node_path", str(exc), node=node_id))
            for field in ("symbol", "anchor"):
                if field in node and (not isinstance(node[field], str) or not node[field] or "path" not in node):
                    errors.append(issue("node_binding", field + " requires nonempty text and a path", node=node_id))
            for field in ("critical", "new"):
                if field in node and not isinstance(node[field], bool):
                    errors.append(issue("node_flag", field + " must be a boolean", node=node_id))
            if "runner" in node and (not isinstance(node["runner"], str) or node["runner"] not in runner_ids):
                errors.append(issue("node_runner", "Unknown runner", node=node_id))
            if "last_status" in node and (not isinstance(node["last_status"], str) or node["last_status"] not in {"passed", "failed", "skipped", "unknown"}):
                errors.append(issue("node_status", "Unknown last_status", node=node_id))
        edges = self.graph.get("edges")
        if not isinstance(edges, list):
            errors.append(issue("edges", "graph.edges must be an array"))
            edges = []
        seen_edges = set()
        contains = defaultdict(list)
        for edge in edges:
            if not isinstance(edge, dict):
                errors.append(issue("edge", "Edges must be objects"))
                continue
            if (not isinstance(edge.get("source"), str) or edge["source"] not in node_ids
                    or not isinstance(edge.get("target"), str) or edge["target"] not in node_ids):
                errors.append(issue("edge_target", "Edge references a missing node", edge=edge))
                continue
            if not isinstance(edge.get("relation"), str) or edge["relation"] not in RELATIONS:
                errors.append(issue("edge_relation", "Unknown relation", edge=edge))
                continue
            identity = (edge.get("source"), edge.get("target"), edge.get("relation"))
            if identity in seen_edges:
                errors.append(issue("duplicate_edge", "Duplicate edge", edge=edge))
            seen_edges.add(identity)
            if edge.get("relation") == "contains":
                contains[edge.get("source")].append(edge.get("target"))
        visited, visiting = set(), set()
        def visit(node):
            if node in visiting:
                errors.append(issue("contains_cycle", "Containment must be acyclic", node=node))
                return
            if node in visited:
                return
            visiting.add(node)
            for child in contains[node]:
                visit(child)
            visiting.remove(node)
            visited.add(node)
        for node in node_ids:
            visit(node)
        if not isinstance(self.graph.get("parity_groups", []), list):
            errors.append(issue("parity_groups", "parity_groups must be an array"))
        return errors

    @staticmethod
    def _id(value):
        return (isinstance(value, str) and bool(IDENTIFIER.fullmatch(value))
                and not re.search(r"(?:#L|:line:)\d+", value))

    def require_valid(self):
        if self.errors:
            raise SuiteError("Project validation failed: " + "; ".join(e["message"] for e in self.errors[:8]))

    def bound_path(self, node):
        repository = self.repositories[node["repo"]]
        repo_path = safe_path(self.root, repository["path"], allow_dot=True)
        return safe_path(repo_path, node["path"]).relative_to(self.root).as_posix()

    def provenance(self):
        files, warnings = source_snapshot(self.root)
        heads = {repo_id: git_head(safe_path(self.root, repository["path"], allow_dot=True))
                 for repo_id, repository in self.repositories.items()}
        return {"head": git_head(self.root), "heads": heads,
                "graph_hash": digest(self.graph), "config_hash": digest(self.config),
                "source_hash": digest(files)}, files, warnings

    def read_state(self, name):
        path = safe_path(self.root, ".testing-suite/state/" + name)
        return read_json(path) if path.exists() else None


def character_column(lines, line, byte_column):
    if line < 1 or line > len(lines):
        return 0
    return len(lines[line - 1].encode("utf-8")[:byte_column].decode("utf-8", "ignore"))


def python_symbols(text):
    tree = ast.parse(text)
    lines = text.splitlines()
    symbols = []
    def walk(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualified = prefix + child.name
                start_line = min([child.lineno] + [d.lineno for d in child.decorator_list])
                symbols.append({"name": qualified,
                                "kind": "class" if isinstance(child, ast.ClassDef) else "function",
                                "start": {"line": start_line, "column": character_column(lines, start_line, child.col_offset)},
                                "end": {"line": child.end_lineno,
                                        "column": character_column(lines, child.end_lineno, child.end_col_offset)}})
                walk(child, qualified + ".")
            else:
                walk(child, prefix)
    walk(tree)
    return symbols


def comment_anchors(text, python=False):
    anchors = []
    if python:
        try:
            comments = [(token.start[0], token.start[1], token.string)
                        for token in tokenize.generate_tokens(io.StringIO(text).readline)
                        if token.type == tokenize.COMMENT]
        except (tokenize.TokenError, IndentationError):
            comments = []
    else:
        # This is intentionally a lexical fallback, not a parser for these languages.
        comments = []
        for number, line in enumerate(text.splitlines(), 1):
            if ANCHOR.search(line) and re.search(r"#|//|/\*|<!--|^\s*[;*]", line):
                comments.append((number, 0, line))
    for line, column, comment in comments:
        for match in ANCHOR.finditer(comment):
            anchors.append({"id": match.group(1) or match.group(2), "line": line,
                            "column": column + match.start(), "end_column": column + match.end()})
    return anchors


def build_index(project, base=None):
    project.require_valid()
    provenance, snapshot, warnings = project.provenance()
    files, bindings, errors = {}, {}, []
    repo_paths = sorted(((Path(r["path"]).parts if r["path"] != "." else (), repo_id)
                         for repo_id, r in project.repositories.items()), reverse=True)
    global_anchors = defaultdict(list)
    explicitly_bound = {project.bound_path(n) for n in project.nodes.values() if "path" in n}
    for warning in warnings:
        if warning["code"] == "symlink_ignored":
            errors.append(issue("unindexed_symlink", "Source symlink target cannot establish reproducible provenance", path=warning["path"]))
    for relative, hash_value in snapshot.items():
        if hash_value.startswith("symlink:"):
            continue
        repo_id = next((rid for prefix, rid in repo_paths if Path(relative).parts[:len(prefix)] == prefix), None)
        if repo_id is None:
            continue
        path = safe_path(project.root, relative)
        try:
            # A large/binary file remains fingerprinted, but is not parsed as source.
            raw = path.read_bytes() if path.stat().st_size <= 4 * 1024 * 1024 else None
            text = raw.decode("utf-8") if raw is not None and b"\x00" not in raw else None
        except (UnicodeError, OSError):
            text = None
        entry = {"hash": hash_value, "repo": repo_id, "language": "python" if path.suffix == ".py" else "text",
                 "symbols": [], "anchors": []}
        if text is not None:
            if path.suffix == ".py":
                try:
                    entry["symbols"] = python_symbols(text)
                except SyntaxError as exc:
                    errors.append(issue("syntax_error", str(exc), path=relative))
            if path.suffix not in {".md", ".rst", ".txt", ".json", ".csv"} or relative in explicitly_bound:
                entry["anchors"] = comment_anchors(text, python=path.suffix == ".py")
            for anchor in entry["anchors"]:
                global_anchors[(repo_id, anchor["id"])].append((relative, anchor))
        files[relative] = entry
    for (repo_id, anchor_id), matches in global_anchors.items():
        if len(matches) > 1:
            errors.append(issue("duplicate_anchor", "Anchor appears more than once: " + anchor_id,
                                repo=repo_id, paths=[path for path, _ in matches]))
    for node_id, node in project.nodes.items():
        if "path" not in node:
            continue
        relative = project.bound_path(node)
        entry = files.get(relative)
        if entry is None:
            errors.append(issue("missing_file", "Node file was not indexed", node=node_id, path=relative))
            continue
        binding = {"path": relative, "repo": node["repo"], "file_hash": entry["hash"]}
        coordinates = None
        if "symbol" in node:
            matches = [s for s in entry["symbols"] if s["name"] == node["symbol"]]
            if len(matches) != 1:
                errors.append(issue("unresolvable_symbol", "Symbol must resolve exactly once: " + node["symbol"],
                                    node=node_id, path=relative))
            else:
                coordinates = {"start": matches[0]["start"], "end": matches[0]["end"]}
                binding["symbol"] = node["symbol"]
        if "anchor" in node:
            matches = global_anchors.get((node["repo"], node["anchor"]), [])
            if len(matches) != 1 or matches[0][0] != relative:
                errors.append(issue("missing_anchor" if not matches else "anchor_drift",
                                    "Anchor must resolve exactly once in its declared file: " + node["anchor"],
                                    node=node_id, path=relative))
            else:
                anchor = matches[0][1]
                binding["anchor"] = node["anchor"]
                anchor_coordinates = {"start": {"line": anchor["line"], "column": anchor["column"]},
                                      "end": {"line": anchor["line"], "column": anchor["end_column"]}}
                binding["anchor_coordinates"] = anchor_coordinates
                if coordinates is None:
                    coordinates = anchor_coordinates
        if coordinates is None:
            # A file binding has a file span; unresolved explicit bindings remain errors.
            raw = safe_path(project.root, relative).read_bytes()
            lines = raw.decode("utf-8", "replace").splitlines()
            coordinates = {"start": {"line": 1, "column": 0},
                           "end": {"line": max(1, len(lines)), "column": len(lines[-1]) if lines else 0}}
        binding.update(coordinates)
        bindings[node_id] = binding
    baseline = provenance["head"]
    if base:
        result = git(project.root, "rev-parse", "--verify", base + "^{commit}", check=True)
        baseline = result.decode().strip()
    result = {"schema_version": 1, "generated_at": now(), "baseline": baseline,
              **provenance, "files": files, "nodes": bindings, "errors": errors, "warnings": warnings}
    atomic_json(project.root, ".testing-suite/state/index.json", result)
    return result


PROVENANCE_FIELDS = ("head", "heads", "graph_hash", "config_hash", "source_hash")


def index_problems(project, provenance):
    try:
        index = project.read_state("index.json")
    except SuiteError as exc:
        return None, [issue("missing_index", str(exc))]
    if not isinstance(index, dict) or index.get("schema_version") != 1:
        return index, [issue("missing_index", "A valid index is required; run index after changing source")]
    problems = []
    if index.get("errors"):
        problems.append(issue("index_drift", "Index contains unresolved bindings or duplicate anchors"))
    for field in PROVENANCE_FIELDS:
        if index.get(field) != provenance[field]:
            problems.append(issue("stale_index", "Index provenance differs: " + field))
    for node_id, node in project.nodes.items():
        if "path" in node and node_id not in index.get("nodes", {}):
            problems.append(issue("missing_binding", "Index has no binding", node=node_id))
    return index, problems


def changed_files(project, base):
    changed, problems = set(), []
    for repo_id, repository in project.repositories.items():
        repo_path = safe_path(project.root, repository["path"], allow_dot=True)
        prefix = repo_path.relative_to(project.root)
        head = git_head(repo_path)
        if head is None:
            problems.append(issue("unknown_git_baseline", "Repository has no Git HEAD", repo=repo_id))
            continue
        target = base or "HEAD"
        result = git(repo_path, "diff", "--relative", "--name-status", "-z", "--find-renames", target, "--")
        if result is None:
            problems.append(issue("unknown_git_baseline", "Cannot diff requested Git base: " + target, repo=repo_id))
            continue
        entries = result.decode("utf-8", "surrogateescape").split("\x00")
        offset = 0
        while offset < len(entries) and entries[offset]:
            status = entries[offset]
            offset += 1
            count = 2 if status.startswith(("R", "C")) else 1
            for _ in range(count):
                if offset >= len(entries) or not entries[offset]:
                    raise SuiteError("Git returned malformed changed paths")
                relative = (prefix / entries[offset]).as_posix()
                offset += 1
                if not excluded(relative):
                    changed.add(relative)
        untracked = git(repo_path, "ls-files", "--others", "--exclude-standard", "-z")
        if untracked is None:
            problems.append(issue("unknown_untracked", "Cannot enumerate untracked files", repo=repo_id))
        else:
            for name in untracked.decode("utf-8", "surrogateescape").split("\x00"):
                if name:
                    relative = (prefix / name).as_posix()
                    if not excluded(relative):
                        changed.add(relative)
    return changed, problems


def relation_maps(project):
    outgoing, incoming = defaultdict(list), defaultdict(list)
    for edge in project.edges:
        if edge.get("source") in project.nodes and edge.get("target") in project.nodes:
            outgoing[edge["source"]].append(edge)
            incoming[edge["target"]].append(edge)
    return outgoing, incoming


def descendants(seed, outgoing):
    seen, pending = {seed}, [seed]
    while pending:
        for edge in outgoing[pending.pop()]:
            if edge["relation"] == "contains" and edge["target"] not in seen:
                seen.add(edge["target"])
                pending.append(edge["target"])
    return seen


def affected_nodes(project, seeds, outgoing, incoming):
    affected, pending = set(), deque(n for n in seeds if n in project.nodes)
    # Expand explicit containers, but never descend from a containment rollup.
    for seed in list(pending):
        pending.extend(descendants(seed, outgoing))
        if project.nodes[seed].get("kind") == "capability":
            for edge in incoming[seed]:
                if edge["relation"] == "implements":
                    pending.extend(descendants(edge["source"], outgoing))
    while pending:
        current = pending.popleft()
        if current in affected:
            continue
        affected.add(current)
        for edge in incoming[current]:
            if edge["relation"] in DEPENDENCIES or edge["relation"] == "contains":
                pending.append(edge["source"])
        for edge in outgoing[current]:
            if edge["relation"] in {"implements", "provides"}:
                pending.append(edge["target"])
    return affected


def periodic_problems(project):
    try:
        full = project.read_state("last-full.json")
        if not isinstance(full, dict) or full.get("evidence") != "runner" or full.get("status") != "passed":
            raise ValueError("No verified full-suite run is recorded")
        completed = datetime.fromisoformat(full["completed_at"].replace("Z", "+00:00"))
        if completed.tzinfo is None:
            raise ValueError("Timestamp lacks timezone")
        age = (datetime.now(timezone.utc) - completed).total_seconds() / 86400
        if age < -1 / 86400:
            raise ValueError("Full-suite completion time is in the future")
        if full.get("graph_hash") != digest(project.graph) or full.get("config_hash") != digest(project.config):
            return [issue("full_suite_policy_changed", "Graph or runner policy changed since last full suite")]
        if age >= project.config.get("policy", {}).get("full_suite_every_days", 7):
            return [issue("full_suite_overdue", "Periodic full suite is overdue")]
        return []
    except (SuiteError, ValueError, KeyError, TypeError) as exc:
        return [issue("full_suite_unknown", str(exc))]


def impact(project, base=None, files=None, nodes=None, full=False):
    files, nodes = files or [], nodes or []
    tests = sorted(nid for nid, node in project.nodes.items() if node.get("kind") == "test")
    if project.errors:
        return {"schema_version": 1, "generated_at": now(), "mode": "FULL",
                "head": git_head(project.root), "heads": {}, "graph_hash": digest(project.graph),
                "config_hash": digest(project.config), "source_hash": None, "index_hash": None,
                "base": base, "changed_files": sorted(files), "changed_nodes": sorted(nodes),
                "affected_nodes": sorted(project.nodes), "selected_tests": tests,
                "reasons": [issue("invalid_graph", "Project invalid; graph inventory cannot establish coverage")] + project.errors,
                "test_reasons": {test: ["full_fallback"] for test in tests}, "confidence": "fallback",
                "provenance_valid": False}
    provenance, snapshot, _ = project.provenance()
    index, problems = index_problems(project, provenance)
    changes, git_problems = changed_files(project, base)
    problems.extend(git_problems)
    try:
        previous_full = project.read_state("last-full.json")
        baseline_files = previous_full.get("source_files") if isinstance(previous_full, dict) else None
        if isinstance(baseline_files, dict):
            changes.update(path for path in set(snapshot) | set(baseline_files)
                           if snapshot.get(path) != baseline_files.get(path))
        else:
            problems.append(issue("unknown_source_baseline", "No full-suite source snapshot; ignored/untracked changes cannot be bounded"))
    except SuiteError as exc:
        problems.append(issue("unknown_source_baseline", str(exc)))
    for path in files:
        # Deleted paths are accepted; escaping paths are not.
        changes.add(safe_path(project.root, path).relative_to(project.root).as_posix())
    problems.extend(periodic_problems(project))
    if full:
        problems.append(issue("requested_full", "Full suite was explicitly requested"))
    if not tests:
        problems.append(issue("no_known_tests", "No known tests; inventory must be established before gating"))
    seeds = set(nodes)
    for node_id in nodes:
        if node_id not in project.nodes:
            problems.append(issue("missing_target", "Unknown requested node: " + node_id))
    by_path = defaultdict(set)
    for node_id, node in project.nodes.items():
        if "path" in node:
            by_path[project.bound_path(node)].add(node_id)
    for path in sorted(changes):
        matches = by_path.get(path, set())
        if not matches:
            problems.append(issue("unmapped_change", "Changed file has no graph binding", path=path))
        seeds.update(matches)
        name = Path(path).name.lower()
        repo_local = next((Path(path).relative_to(Path(r["path"])).as_posix()
                           for r in project.repositories.values()
                           if Path(path).is_relative_to(Path(r["path"])) and r["path"] != "."), path)
        if (repo_local.startswith(".testing-suite/") or "lock" in name
                or name in {"package.json", "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
                            "cargo.toml", "go.mod", "gemfile", "dockerfile", "tsconfig.json", "tox.ini"}
                or repo_local.startswith(".github/")):
            problems.append(issue("configuration_change", "Configuration or dependency change requires full suite", path=path))
    outgoing, incoming = relation_maps(project)
    affected = affected_nodes(project, seeds, outgoing, incoming)
    test_reasons = defaultdict(list)
    selected = {test for test in tests if test in affected}
    for test in selected:
        test_reasons[test].append("graph_impact")
    try:
        previous = project.read_state("failures.json")
    except SuiteError:
        previous = None
        problems.append(issue("invalid_failure_history", "Failure history cannot be read"))
    failed = set(previous.get("tests", [])) if isinstance(previous, dict) else set()
    for test in tests:
        node = project.nodes[test]
        critical = bool(node.get("critical"))
        for edge in outgoing[test]:
            if edge["relation"] in {"covers", "verifies"}:
                subject = edge["target"]
                ancestors, queue = set(), [subject]
                while queue:
                    ancestor = queue.pop()
                    if ancestor in ancestors:
                        continue
                    ancestors.add(ancestor)
                    critical = critical or bool(project.nodes[ancestor].get("critical"))
                    queue.extend(e["source"] for e in incoming[ancestor] if e["relation"] == "contains")
                    queue.extend(e["target"] for e in outgoing[ancestor] if e["relation"] == "implements")
        for condition, reason in ((critical and project.config.get("policy", {}).get("always_include_critical", True), "critical"),
                                  (node.get("new", False), "new"),
                                  (node.get("last_status") == "failed" or test in failed, "previously_failed")):
            if condition:
                selected.add(test)
                test_reasons[test].append(reason)
    fine_paths = {project.bound_path(project.nodes[n]) for n in seeds if n in project.nodes
                  and "path" in project.nodes[n] and project.nodes[n].get("kind") != "file"}
    for seed in sorted(seeds & set(project.nodes)):
        node = project.nodes[seed]
        if node.get("kind") == "file" and "path" in node and project.bound_path(node) in fine_paths and seed not in nodes:
            continue
        if not set(tests) & affected_nodes(project, {seed}, outgoing, incoming):
            problems.append(issue("no_coverage", "Changed node has no reachable covering tests", node=seed))
    if problems:
        selected = set(tests)
        for test in tests:
            test_reasons[test].append("full_fallback" if not full else "requested_full")
    result = {"schema_version": 1, "generated_at": now(), "mode": "FULL" if problems else "TARGETED",
              **provenance, "index_hash": digest(index) if isinstance(index, dict) else None, "base": base,
              "changed_files": sorted(changes), "changed_nodes": sorted(seeds), "affected_nodes": sorted(affected),
              "selected_tests": sorted(selected), "reasons": problems,
              "test_reasons": {key: value for key, value in sorted(test_reasons.items())},
              "confidence": "fallback" if problems and not full else "high",
              "provenance_valid": not bool(project.errors or any(p["code"] in {"missing_index", "stale_index", "index_drift", "missing_binding"} for p in problems))}
    return result


def verify_selection(project, selection):
    project.require_valid()
    if not isinstance(selection, dict) or selection.get("schema_version") != 1:
        raise SuiteError("Selection must be a schema_version 1 object")
    provenance, _, _ = project.provenance()
    index, problems = index_problems(project, provenance)
    if problems:
        raise SuiteError("Cannot use selection with missing or stale index: " + "; ".join(p["message"] for p in problems))
    for field in PROVENANCE_FIELDS:
        if selection.get(field) != provenance[field]:
            raise SuiteError("Selection is stale or belongs to another source state: " + field)
    if selection.get("index_hash") != digest(index):
        raise SuiteError("Selection index provenance is stale")
    if selection.get("provenance_valid") is not True:
        raise SuiteError("Selection was produced without valid provenance")
    tests = selection.get("selected_tests")
    if not isinstance(tests, list) or not all(isinstance(t, str) for t in tests) or len(tests) != len(set(tests)):
        raise SuiteError("Selection selected_tests must contain unique test ids")
    if not tests:
        raise SuiteError("A selection without tests cannot establish coverage")
    all_tests = {nid for nid, node in project.nodes.items() if node.get("kind") == "test"}
    if not set(tests) <= all_tests:
        raise SuiteError("Selection references missing or non-test nodes")
    if selection.get("mode") not in {"FULL", "TARGETED"}:
        raise SuiteError("Selection mode must be FULL or TARGETED")
    if selection["mode"] == "FULL" and set(tests) != all_tests:
        raise SuiteError("FULL selection does not include every known test")
    if selection["mode"] == "FULL":
        bound_runners = {project.nodes[test].get("runner") for test in all_tests}
        missing_runners = sorted(set(project.runners) - bound_runners)
        if missing_runners:
            raise SuiteError("FULL scope contains runners with no mapped test inventory: " + ", ".join(missing_runners))
    for key in ("changed_files", "changed_nodes"):
        if not isinstance(selection.get(key), list) or not all(isinstance(s, str) for s in selection[key]):
            raise SuiteError("Selection requires string array " + key)
    # Recompute actual Git changes; an edited manifest cannot erase required coverage.
    required = impact(project, base=selection.get("base"), files=selection["changed_files"],
                      nodes=selection["changed_nodes"], full=selection["mode"] == "FULL")
    if not set(required["selected_tests"]) <= set(tests):
        raise SuiteError("Selection omits tests required by current impact and policy")
    if required["mode"] == "FULL" and selection["mode"] != "FULL":
        raise SuiteError("Current policy requires a FULL selection")
    return provenance, index


def navigate(project, query, direction="both", exact=False):
    project.require_valid()
    if not query:
        raise SuiteError("navigate requires an id or name query")
    matches = [node for node in project.nodes.values()
               if node["id"] == query or (not exact and query.casefold() in node["name"].casefold())]
    outgoing, incoming = relation_maps(project)
    try:
        index = project.read_state("index.json") or {}
    except SuiteError:
        index = {}
    provenance, _, _ = project.provenance()
    _, drift = index_problems(project, provenance)
    return {"schema_version": 1, "query": query, "index_current": not drift, "warnings": drift,
            "matches": [{"node": node, "coordinate": index.get("nodes", {}).get(node["id"]),
                         "incoming": incoming[node["id"]] if direction in {"both", "incoming"} else [],
                         "outgoing": outgoing[node["id"]] if direction in {"both", "outgoing"} else []}
                        for node in matches]}


def parity(project):
    project.require_valid()
    outgoing, _ = relation_maps(project)
    issues, reports, group_ids = [], [], set()
    for group in project.graph.get("parity_groups", []):
        if not isinstance(group, dict) or not Project._id(group.get("id")):
            issues.append(issue("parity_group", "Parity group requires a stable id"))
            continue
        group_id = group["id"]
        if group_id in group_ids:
            issues.append(issue("duplicate_parity_group", "Duplicate parity group", group=group_id))
        group_ids.add(group_id)
        capability = group.get("capability")
        if project.nodes.get(capability, {}).get("kind") != "capability":
            issues.append(issue("parity_capability", "Group capability is missing or not a capability", group=group_id))
        instances, invariants = group.get("instances"), group.get("shared_invariants")
        if (not isinstance(instances, list) or not instances or not all(isinstance(i, str) for i in instances)
                or len(instances) != len(set(instances))):
            issues.append(issue("parity_instances", "Group requires unique nonempty instances", group=group_id))
            continue
        if (not isinstance(invariants, list) or not invariants or not all(isinstance(i, str) for i in invariants)
                or len(invariants) != len(set(invariants))):
            issues.append(issue("parity_invariants", "Group requires unique nonempty shared_invariants", group=group_id))
            continue
        scopes = {}
        for instance in instances:
            if project.nodes.get(instance, {}).get("kind") != "instance":
                issues.append(issue("parity_instance", "Instance missing or wrong kind", group=group_id, instance=instance))
            if not any(e["relation"] == "implements" and e["target"] == capability for e in outgoing[instance]):
                issues.append(issue("parity_implementation", "Instance must implement group capability", group=group_id, instance=instance))
            scopes[instance] = descendants(instance, outgoing)
        for invariant in invariants:
            if project.nodes.get(invariant, {}).get("kind") != "invariant":
                issues.append(issue("parity_invariant", "Shared invariant missing or wrong kind", group=group_id, invariant=invariant))
        variance_map = {}
        variances = group.get("variances", [])
        if not isinstance(variances, list):
            issues.append(issue("parity_variances", "variances must be an array", group=group_id))
            variances = []
        for variance in variances:
            if not isinstance(variance, dict):
                issues.append(issue("parity_variance", "Variance must be an object", group=group_id))
                continue
            instance, invariant, test = variance.get("instance"), variance.get("invariant"), variance.get("test")
            pair = (instance, invariant)
            reason = variance.get("reason")
            if (instance not in instances or invariant not in invariants or not isinstance(reason, str)
                    or not reason.strip() or project.nodes.get(test, {}).get("kind") != "test"):
                issues.append(issue("parity_variance", "Variance requires known instance/invariant, reason, and test", group=group_id))
                continue
            if pair in variance_map:
                issues.append(issue("duplicate_variance", "Duplicate variance for instance/invariant", group=group_id))
            variance_map[pair] = variance
        coverage = []
        for instance in instances:
            for invariant in invariants:
                covering = []
                for test, node in project.nodes.items():
                    if node.get("kind") != "test":
                        continue
                    subjects = {e["target"] for e in outgoing[test] if e["relation"] in {"covers", "verifies"}}
                    if invariant in subjects and (test in scopes[instance] or bool(subjects & scopes[instance])):
                        covering.append(test)
                variance = variance_map.get((instance, invariant))
                if variance and variance["test"] not in covering:
                    issues.append(issue("untested_variance", "Variance test must cover invariant in this instance", group=group_id,
                                        instance=instance, invariant=invariant, test=variance["test"]))
                if not covering:
                    issues.append(issue("missing_parity_coverage", "No scoped test covers shared invariant", group=group_id,
                                        instance=instance, invariant=invariant))
                coverage.append({"instance": instance, "invariant": invariant, "tests": sorted(covering),
                                 "variance": variance})
        reports.append({"id": group_id, "coverage": coverage})
    return {"schema_version": 1, "passed": not issues, "groups": reports, "issues": issues,
            "limitation": "Checks declared invariant/test coverage; behavioral equivalence requires executing these tests"}


def pointer_part(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def json_changes(before, after, pointer=""):
    if type(before) is not type(after):
        return [{"path": pointer, "operation": "replace", "before": before, "after": after}]
    changes = []
    if isinstance(before, dict):
        for key in sorted(set(before) | set(after)):
            path = pointer + "/" + pointer_part(key)
            if key not in before:
                changes.append({"path": path, "operation": "add", "after": after[key]})
            elif key not in after:
                changes.append({"path": path, "operation": "remove", "before": before[key]})
            else:
                changes.extend(json_changes(before[key], after[key], path))
    elif isinstance(before, list):
        for index in range(max(len(before), len(after))):
            path = pointer + "/" + str(index)
            if index >= len(before):
                changes.append({"path": path, "operation": "add", "after": after[index]})
            elif index >= len(after):
                changes.append({"path": path, "operation": "remove", "before": before[index]})
            else:
                changes.extend(json_changes(before[index], after[index], path))
    elif before != after:
        changes.append({"path": pointer, "operation": "replace", "before": before, "after": after})
    return changes


def state_diff(before, after, allowlist):
    if not isinstance(allowlist, list) or not all(isinstance(p, str) and (p == "" or p.startswith("/")) for p in allowlist):
        raise SuiteError("Allowlist must be an array of exact JSON Pointer paths; empty string names the root")
    for pointer in allowlist:
        if re.search(r"~(?![01])", pointer):
            raise SuiteError("Invalid JSON Pointer escape: " + pointer)
    allowed = set(allowlist)
    changes = json_changes(before, after)
    unexpected = [change for change in changes if change["path"] not in allowed]
    return {"schema_version": 1, "passed": not unexpected, "changes": changes,
            "unexpected": unexpected, "allowlist": sorted(allowed)}


def save_results(project, selection, records, *, evidence, runners=None, valid=True):
    provenance, index = verify_selection(project, selection)
    seen = set()
    for record in records:
        if not isinstance(record, dict) or record.get("id") not in selection["selected_tests"]:
            raise SuiteError("Result references a test outside the selection")
        if record["id"] in seen:
            raise SuiteError("Duplicate result id: " + record["id"])
        if record.get("status") not in {"passed", "failed", "skipped"}:
            raise SuiteError("Results require actual passed, failed, or skipped status")
        seen.add(record["id"])
    result = {"schema_version": 1, "generated_at": now(), "evidence": evidence,
              "selection_hash": digest(selection), **provenance, "index_hash": digest(index),
              "mode": selection["mode"], "results": records, "runners": runners or [], "provenance_valid": valid}
    atomic_json(project.root, ".testing-suite/state/results.json", result)
    atomic_json(project.root, ".testing-suite/state/last-selection.json", selection)
    retain_attempt(project, result)
    update_failures(project, records, verified=False)
    return result


def record_results(project, selection, records):
    return save_results(project, selection, records, evidence="manual")


def retain_attempt(project, result):
    history_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex
    atomic_json(project.root, ".testing-suite/state/history/" + history_id + ".json", result)


def update_failures(project, records, verified):
    previous = project.read_state("failures.json")
    failed = set(previous.get("tests", [])) if isinstance(previous, dict) else set()
    for record in records:
        if record["status"] == "failed":
            failed.add(record["id"])
        elif verified and record["status"] == "passed":
            failed.discard(record["id"])
    atomic_json(project.root, ".testing-suite/state/failures.json",
                {"schema_version": 1, "updated_at": now(), "tests": sorted(failed)})


def unittest_file(project, runner, module):
    """Recover real discovery paths from runner start/top-level arguments."""
    command = runner["command"]
    cwd = Path(runner.get("cwd", "."))
    start, top = ".", None
    if "discover" in command:
        arguments = command[command.index("discover") + 1:]
        for index, argument in enumerate(arguments):
            if argument in {"-s", "--start-directory"} and index + 1 < len(arguments):
                start = arguments[index + 1]
            elif argument.startswith("--start-directory="):
                start = argument.split("=", 1)[1]
            elif argument in {"-t", "--top-level-directory"} and index + 1 < len(arguments):
                top = arguments[index + 1]
            elif argument.startswith("--top-level-directory="):
                top = argument.split("=", 1)[1]
        # Positional discovery syntax is accepted only without option arguments.
        if arguments and not arguments[0].startswith("-"):
            start = arguments[0]
            if len(arguments) > 2 and not arguments[2].startswith("-"):
                top = arguments[2]
        root = cwd / (top if top is not None else start)
    else:
        root = cwd
    if module == "__main__":
        script = next((a for a in command if a.endswith(".py")), None)
        relative = (cwd / script).as_posix() if script else None
    else:
        relative = (root / Path(*module.split("."))).with_suffix(".py").as_posix()
    if relative is None:
        return None
    try:
        path = safe_path(project.root, relative)
        return path.relative_to(project.root).as_posix() if path.is_file() else None
    except SuiteError:
        return None


def observe_runner(project, runner, stdout_path, stderr_path):
    """Recognize real case output. Unknown runners cannot manufacture green cases."""
    text = stdout_path.read_text(encoding="utf-8", errors="replace") + "\n" + stderr_path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
    command = runner["command"]
    adapter = runner.get("adapter")
    if not adapter:
        adapter = "unittest" if "unittest" in command else "pytest" if any(Path(a).name == "pytest" for a in command) else None
    observations = []
    count = None
    if adapter == "unittest":
        summaries = re.findall(r"Ran\s+(\d+)\s+tests?\s+in", text)
        count = int(summaries[-1]) if summaries else None
        current = None
        for line in text.splitlines():
            started = re.match(r"^(\w+) \(([^)]+)\)", line)
            if started:
                method, identity = started.groups()
                current = identity if identity.endswith("." + method) else identity + "." + method
            status = re.search(r"\.\.\.\s+(ok|FAIL|ERROR|skipped\b.*)$", line)
            if current and status:
                raw = status.group(1)
                module = current.rsplit(".", 2)[0] if current.count(".") >= 2 else ""
                observations.append({"id": current, "path": unittest_file(project, runner, module),
                                     "status": "passed" if raw == "ok" else "skipped" if raw.startswith("skipped") else "failed"})
                current = None
    elif adapter == "pytest":
        for line in text.splitlines():
            match = re.match(r"^([^\s]+\.py(?:::[^\s]+)+)\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b", line)
            if match:
                identity, status = match.groups()
                observations.append({"id": identity, "status": "passed" if status == "PASSED" else "failed" if status in {"FAILED", "ERROR", "XPASS"} else "skipped"})
        count = len(observations) if observations else None
        collected = re.findall(r"collected\s+(\d+)\s+items?", text)
        if collected and int(collected[-1]) == 0:
            count = 0
    zero_output = bool(re.search(r"(?:Ran\s+0\s+tests?|collected\s+0\s+items?|no tests (?:ran|found)|0 tests? (?:passed|collected))", text, re.I))
    if zero_output:
        count = 0
    return {"adapter": adapter, "observed_count": count, "observed_tests": observations,
            "verified": adapter in {"unittest", "pytest"} and count is not None and count > 0 and bool(observations),
            "zero_tests": zero_output or count == 0}


def observed_test_status(project, test, runner, observation):
    if not observation["verified"]:
        return "skipped"
    node = project.nodes[test]
    if "path" not in node:
        return "skipped"
    matches = []
    if observation["adapter"] == "unittest":
        path = project.bound_path(node)
        symbol = node.get("symbol")
        for observed in observation["observed_tests"]:
            identity = observed["id"]
            if observed.get("path") != path:
                continue
            if symbol:
                suffix = "." + symbol
                if identity.endswith(suffix):
                    matches.append(observed["status"])
            else:
                matches.append(observed["status"])
    elif observation["adapter"] == "pytest":
        path = project.bound_path(node)
        cwd = Path(runner.get("cwd", "."))
        symbol = node.get("symbol")
        for observed in observation["observed_tests"]:
            parts = observed["id"].split("::")
            observed_path = (cwd / parts[0]).as_posix()
            identity = ".".join(parts[1:]).split("[", 1)[0]
            if observed_path == path and (not symbol or identity == symbol):
                matches.append(observed["status"])
    if not matches:
        return "skipped"
    return "failed" if "failed" in matches else "skipped" if "skipped" in matches else "passed"


def run_selection(project, selection):
    provenance, index = verify_selection(project, selection)
    _, source_files, _ = project.provenance()
    needed = set()
    for test in selection["selected_tests"]:
        runner_id = project.nodes[test].get("runner")
        if runner_id not in project.runners:
            raise SuiteError("Selected test has no configured runner: " + test)
        needed.add(runner_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    runner_results, statuses, observations = [], {}, {}
    for number, runner_id in enumerate(sorted(needed)):
        runner = project.runners[runner_id]
        stdout_relative = ".testing-suite/state/runs/{}/{}.stdout.log".format(run_id, number)
        stderr_relative = ".testing-suite/state/runs/{}/{}.stderr.log".format(run_id, number)
        stdout_path = safe_path(project.root, stdout_relative)
        stderr_path = safe_path(project.root, stderr_relative)
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        started = now()
        error = None
        returncode = None
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            try:
                result = subprocess.run(runner["command"],
                                        cwd=safe_path(project.root, runner.get("cwd", "."), allow_dot=True),
                                        stdout=stdout, stderr=stderr,
                                        timeout=runner.get("timeout_seconds", 300), check=False,
                                        shell=False)
                returncode = result.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                error = str(exc)
        observation = observe_runner(project, runner, stdout_path, stderr_path)
        observations[runner_id] = observation
        status = "passed" if returncode == 0 and observation["verified"] else "failed"
        statuses[runner_id] = status
        runner_results.append({"id": runner_id, "command": runner["command"], "status": status,
                               "exit_code": returncode, "started_at": started, "finished_at": now(),
                               "stdout_path": stdout_relative, "stderr_path": stderr_relative,
                               "stdout_hash": file_hash(stdout_path), "stderr_hash": file_hash(stderr_path),
                               **observation,
                               **({"error": error} if error else {})})
    after, _, _ = project.provenance()
    unchanged = all(after[field] == provenance[field] for field in PROVENANCE_FIELDS)
    records = [{"id": test, "status": (observed_test_status(project, test, project.runners[project.nodes[test]["runner"]], observations[project.nodes[test]["runner"]])
                                        if statuses[project.nodes[test]["runner"]] == "passed" else "failed"),
                "runner": project.nodes[test]["runner"]} for test in selection["selected_tests"]]
    # Preserve evidence even if a runner mutates source; it must never pass a gate.
    result = {"schema_version": 1, "generated_at": now(), "evidence": "runner",
              "selection_hash": digest(selection), **provenance, "index_hash": digest(index),
              "mode": selection["mode"], "results": records, "runners": runner_results,
              "provenance_valid": unchanged,
              "observation": "Unittest/pytest verbose cases are matched by file and symbol; configured runner commands remain the trusted collection boundary"}
    if not unchanged:
        result["issues"] = [issue("source_mutated_during_run", "Runner changed fingerprinted project source")]
    atomic_json(project.root, ".testing-suite/state/results.json", result)
    atomic_json(project.root, ".testing-suite/state/last-selection.json", selection)
    retain_attempt(project, result)
    update_failures(project, records, verified=unchanged)
    if unchanged and selection["mode"] == "FULL" and all(r["status"] == "passed" for r in records):
        atomic_json(project.root, ".testing-suite/state/last-full.json",
                    {"schema_version": 1, "completed_at": now(), "evidence": "runner", "status": "passed",
                     **provenance, "selection_hash": digest(selection), "tests": selection["selected_tests"], "source_files": source_files})
    return result


def gate(project, selection=None, require_full=False):
    issues = []
    if selection is None:
        try:
            selection = project.read_state("last-selection.json")
        except SuiteError as exc:
            return {"schema_version": 1, "passed": False, "issues": [issue("invalid_selection", str(exc))]}
        if selection is None:
            selection = impact(project, full=require_full)
    try:
        provenance, index = verify_selection(project, selection)
    except SuiteError as exc:
        return {"schema_version": 1, "passed": False, "issues": [issue("invalid_selection", str(exc))]}
    if require_full and selection["mode"] != "FULL":
        issues.append(issue("full_required", "Gate requires full-suite evidence"))
    try:
        results = project.read_state("results.json")
    except SuiteError as exc:
        results = None
        issues.append(issue("invalid_results", str(exc)))
    if not isinstance(results, dict) or results.get("schema_version") != 1:
        issues.append(issue("missing_results", "No result evidence is recorded"))
        return {"schema_version": 1, "passed": False, "issues": issues}
    if results.get("evidence") != "runner":
        issues.append(issue("unverified_evidence", "Manual records are useful history, but gate requires explicit run evidence"))
    if results.get("provenance_valid") is not True:
        issues.append(issue("invalid_provenance", "Runner provenance is invalid"))
    for field in PROVENANCE_FIELDS:
        if results.get(field) != provenance[field]:
            issues.append(issue("stale_results", "Result provenance differs: " + field))
    if results.get("index_hash") != digest(index):
        issues.append(issue("stale_results", "Result index provenance differs"))
    if results.get("selection_hash") != digest(selection):
        issues.append(issue("wrong_selection", "Results were not produced for this exact selection"))
    runner_evidence = {}
    for runner in results.get("runners", []):
        if not isinstance(runner, dict) or runner.get("id") not in project.runners or runner.get("id") in runner_evidence:
            issues.append(issue("runner_evidence", "Invalid or duplicate runner evidence"))
            continue
        runner_evidence[runner["id"]] = runner
        config = project.runners[runner["id"]]
        if (runner.get("command") != config["command"] or runner.get("exit_code") != 0
                or runner.get("status") != "passed" or runner.get("verified") is not True
                or not isinstance(runner.get("observed_count"), int) or runner["observed_count"] <= 0):
            issues.append(issue("runner_failed", "Configured runner did not pass", runner=runner["id"]))
        for stream in ("stdout_path", "stderr_path"):
            try:
                path = safe_path(project.root, runner.get(stream))
                if not runner[stream].startswith(".testing-suite/state/runs/") or not path.is_file():
                    raise SuiteError("Missing runner log")
                if runner.get(stream.replace("_path", "_hash")) != file_hash(path):
                    raise SuiteError("Runner log fingerprint changed")
            except SuiteError as exc:
                issues.append(issue("runner_log", str(exc), runner=runner["id"]))
    records = {}
    for record in results.get("results", []):
        if not isinstance(record, dict) or record.get("id") in records:
            issues.append(issue("duplicate_result", "Invalid or duplicate test result"))
            continue
        records[record.get("id")] = record
    for test in selection["selected_tests"]:
        record = records.get(test)
        if not record:
            issues.append(issue("missing_result", "Required test has no result", test=test))
            continue
        if record.get("status") != "passed":
            issues.append(issue("test_not_passed", "Required test failed or was skipped", test=test, status=record.get("status")))
        expected_runner = project.nodes[test].get("runner")
        if record.get("runner") != expected_runner or expected_runner not in runner_evidence:
            issues.append(issue("unverified_test", "Test is not backed by its configured runner", test=test))
        elif observed_test_status(project, test, project.runners[expected_runner], runner_evidence[expected_runner]) != "passed":
            issues.append(issue("unobserved_test", "Required test was not observed passing in verbose runner output", test=test))
    if results.get("mode") != selection["mode"]:
        issues.append(issue("coverage_mode", "Result coverage mode differs from selection"))
    parity_report = parity(project)
    if not parity_report["passed"]:
        issues.extend(parity_report["issues"])
    return {"schema_version": 1, "passed": not issues, "mode": selection["mode"],
            "required_tests": selection["selected_tests"], "issues": issues}
