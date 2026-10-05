# Install and bootstrap

Requires Python 3.10 or later. The control tools use the standard library. Your project's existing test framework remains responsible for executing tests.

## Bootstrap a project

From a repository checkout:

```bash
python Gauntlet/scripts/bootstrap.py --project /path/to/project --name "My project" --profile auto --agent codex --dry-run
python Gauntlet/scripts/bootstrap.py --project /path/to/project --name "My project" --profile auto --agent codex
```

The repository folder is `Gauntlet`; extracted archives retain their portable `testing-suite/` directory. Adjust the source path above when using an archive. The bootstrapper installs the control tools under `.testing-suite/bin/`, seeds project facts in `.testing-suite/config.json` and `graph.json`, and installs the routed skill under `.agents/skills/testing-suite/`. Use `--agent claude` for `.claude/skills/testing-suite/`, `both` for both agents, or `none` for the tools alone. Run from any working directory; source assets are located relative to the bootstrapper. Artifact paths passed to the runtime are project-relative; save selections and results under `.testing-suite/state/`.

Read the JSON dry-run plan before applying it to a repository with existing configuration. An identical rerun is safe. A differing managed file is a collision and stops the operation before writes. Existing manifests, tests, `AGENTS.md`, and `CLAUDE.md` are preserved. The bootstrapper supplies `.testing-suite/agent-instructions.md`; incorporate its routing note into an existing instruction file if useful. It appends a managed ignore block for local evidence and logs.

`--profile auto` inspects existing manifests. Inspect `.testing-suite/config.json` afterward: runner discovery establishes commands, not coverage. A project with no usable runner starts without one, and cannot pass a release evidence gate. Add an actual runner and tests using the design-tests skill. No dependencies are installed automatically. Node execution needs the project's chosen package manager and dependencies; Python execution needs the project's existing environment. The strict v0.1 gate observes verbose unittest/pytest cases. Other frameworks remain unverified until a trusted result adapter is implemented. Pytest and Node discovery deliberately leave inferred test-to-runner mappings unclaimed for manual collection review.

## Fill the map

```bash
python /path/to/project/.testing-suite/bin/suite.py --root /path/to/project validate
python /path/to/project/.testing-suite/bin/suite.py --root /path/to/project index
```

The seed graph is an inventory, not a complete behavioral model. Follow the map-system skill to add capabilities, implementation instances, code bindings, dependencies, invariants, and `covers`/`verifies` edges. Keep IDs stable when source lines move. Keep the authored graph in Git; local indexes, execution logs, and evidence are generated state.

## Optional CI

`--ci` creates an opt-in GitHub Actions workflow after collision preflight. Read the generated workflow and configure dependency installation, services, fixtures, and any project-specific runner requirements before relying on it. Bootstrapping does not create repository secrets, change branch protection, or publish anything.

## Install only the routed skill

Copy the whole `Gauntlet/` directory into a project's `.agents/skills/testing-suite/` or `.claude/skills/testing-suite/`. Keep its `scripts/`, `schemas/`, `references/`, `protocols/`, and `skills/` together. Load the root `SKILL.md`, which routes to the focused workflows. The `.skill` distribution is a ZIP archive with the portable `testing-suite/` directory layout; import support varies by client, so directory installation is the portable route.

## Updating

The bootstrapper deliberately rejects modified managed files. Keep authored `config.json` and `graph.json`; review a newer tool/skill package and replace only its runtime and skill assets deliberately. Reindex afterward and discard old evidence. Do not delete a project's authored graph to work around a collision. The tools make no global agent configuration changes.
