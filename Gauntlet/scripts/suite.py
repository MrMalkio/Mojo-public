#!/usr/bin/env python3
"""JSON CLI for testing-suite. Run from a checkout or an installed bin directory."""
import argparse
import json
import sys

from suite_core import (Project, SuiteError, atomic_json, build_index, gate, impact,
                        navigate, parity, read_json, record_results, run_selection,
                        safe_path, state_diff)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", default=".", help="project root (before the subcommand)")
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("validate", "index", "impact", "navigate", "record", "run", "gate", "state-diff", "parity"):
        command = commands.add_parser(name)
        command.add_argument("--output", help="also atomically save JSON to a project-relative path")
        if name in {"index", "impact"}:
            command.add_argument("--base", help="Git base commit/ref; default working changes against HEAD")
        if name == "impact":
            command.add_argument("--files", nargs="+", default=[])
            command.add_argument("--nodes", nargs="+", default=[])
            command.add_argument("--full", action="store_true")
        elif name == "navigate":
            command.add_argument("query", nargs="?")
            command.add_argument("--id", dest="node_id")
            command.add_argument("--query", dest="name_query")
            command.add_argument("--direction", choices=["both", "incoming", "outgoing"], default="both")
        elif name == "record":
            command.add_argument("--selection", required=True)
            command.add_argument("--results", help="JSON array or object containing a results array")
            command.add_argument("--test")
            command.add_argument("--status", choices=["passed", "failed", "skipped"])
        elif name == "run":
            command.add_argument("--selection", required=True)
        elif name == "gate":
            command.add_argument("--selection")
            command.add_argument("--full", action="store_true")
        elif name == "state-diff":
            command.add_argument("before", nargs="?")
            command.add_argument("after", nargs="?")
            command.add_argument("--before", dest="before_file")
            command.add_argument("--after", dest="after_file")
            command.add_argument("--allow", action="append", default=[], help="exact JSON pointer or allowlist JSON filename")
            command.add_argument("--allowlist", help="JSON array of exact allowed pointers")
    return result


def load(root, relative):
    return read_json(safe_path(root, relative))


def load_allowlist(root, relative):
    values = load(root, relative)
    if not isinstance(values, list):
        raise SuiteError("Allowlist file must contain a JSON array of exact pointers")
    return values


def dispatch(args):
    # state-diff works without bootstrapping a project.
    if args.command == "state-diff":
        from pathlib import Path
        root = Path(args.root).resolve()
        before, after = args.before_file or args.before, args.after_file or args.after
        if not before or not after:
            raise SuiteError("state-diff requires before and after JSON files")
        allowed = []
        if args.allowlist:
            allowed.extend(load_allowlist(root, args.allowlist))
        for value in args.allow:
            if value == "" or value.startswith("/"):
                allowed.append(value)
            else:
                allowed.extend(load_allowlist(root, value))
        report = state_diff(load(root, before), load(root, after), allowed)
        return root, report, 0 if report["passed"] else 1
    project = Project(args.root)
    if args.command == "validate":
        report = {"schema_version": 1, "valid": not project.errors, "errors": project.errors,
                  "nodes": len(project.nodes), "edges": len(project.edges),
                  "note": "Source bindings are checked by index; parity coverage is checked by parity and gate"}
        status = 0 if report["valid"] else 2
    elif args.command == "index":
        report = build_index(project, args.base)
        status = 0 if not report["errors"] else 2
    elif args.command == "impact":
        report = impact(project, args.base, args.files, args.nodes, args.full)
        status = 0  # FULL fallback is a successful, conservative plan.
    elif args.command == "navigate":
        query = args.node_id or args.name_query or args.query
        report = navigate(project, query, args.direction, exact=bool(args.node_id))
        status = 0 if report["matches"] else 1
    elif args.command == "parity":
        report = parity(project)
        status = 0 if report["passed"] else 1
    elif args.command == "record":
        if args.results and (args.test or args.status):
            raise SuiteError("Use --results or --test with --status, not both")
        if args.results:
            records = load(project.root, args.results)
            if isinstance(records, dict):
                records = records.get("results")
        elif args.test and args.status:
            records = [{"id": args.test, "status": args.status}]
        else:
            raise SuiteError("record requires --results or both --test and --status")
        if not isinstance(records, list):
            raise SuiteError("Results input must contain an array")
        report = record_results(project, load(project.root, args.selection), records)
        status = 0 if all(r["status"] == "passed" for r in records) else 1
    elif args.command == "run":
        report = run_selection(project, load(project.root, args.selection))
        status = 0 if report["provenance_valid"] and all(r["status"] == "passed" for r in report["results"]) else 1
    elif args.command == "gate":
        report = gate(project, load(project.root, args.selection) if args.selection else None, args.full)
        status = 0 if report["passed"] else 1
    else:
        raise SuiteError("Unsupported command")
    return project.root, report, status


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        root, report, status = dispatch(args)
        if args.output:
            atomic_json(root, args.output, report)
    except (SuiteError, OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        report, status = {"schema_version": 1, "error": str(exc)}, 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return status


if __name__ == "__main__":
    sys.exit(main())
