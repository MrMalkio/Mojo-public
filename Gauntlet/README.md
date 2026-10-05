# Gauntlet — Testing suite 0.1.0

Modular agent skills and a portable project bootstrapper for connecting product behavior to implementation and test proof. Built from the available **Our super testing suite** chat and inspected examples from testland, Playwright, pytest-testmon, Pact, and Nx. See [source snapshots](references/SOURCES.md) and [requirement coverage](references/REQUIREMENTS.md).

The package contains ten focused skills, a bidirectional graph, source indexing, conservative impact selection, instance parity checks, JSON state-diff checks, actual test-runner execution, and a release evidence gate. It preserves a project's existing testing frameworks and conventions.

## Start with a real project

Requires Python 3.10+. The control tools have no third-party dependencies.

```bash
python Gauntlet/scripts/bootstrap.py --project /path/to/project --name "My project" --profile auto --agent codex --dry-run
python Gauntlet/scripts/bootstrap.py --project /path/to/project --name "My project" --profile auto --agent codex
python /path/to/project/.testing-suite/bin/suite.py --root /path/to/project validate
python /path/to/project/.testing-suite/bin/suite.py --root /path/to/project index
```

Use `--agent claude`, `both`, or `none` for the desired installation. `--ci` opts into a GitHub Actions scaffold. Dry-run writes nothing. Collision preflight and a bootstrap manifest protect existing files; an identical rerun is idempotent. No package installs, commits, uploads, or global settings changes occur during bootstrap. See [installation](agent/INSTALL.md).

Bootstrap seeds actual repository and test inventory. Complete the authored `.testing-suite/graph.json` with the [map-system skill](skills/map-system/SKILL.md); inventory alone does not establish behavioral coverage.

## The model

```text
Product / system / repositories
  → capability → implementation instances
  → pages / workflows / UI → actions / events
  → functions / named blocks / live coordinates
  → data / APIs / cross-repo dependencies
  → invariants → tests → execution evidence
```

Every item has a stable ID. Code bindings use repository, path, and optional Python symbol or `@coord:<id>` comment anchor. Line numbers are refreshed coordinates, not identity. Dependency edges point from consumer to provider; tests `cover` or `verify` their subjects. Navigate in either direction to find code from a product capability or affected behavior from code. See [graph conventions](protocols/GRAPH-CONVENTIONS.md) and [JSON schemas](schemas/graph.schema.json).

Instances of a capability can share an invariant while presenting as a toggle, checkbox, button, or read-only display. Parity groups require coverage per instance. A deliberate behavioral variance names the invariant, explains the reason, and links a test.

## Plan, run, and check proof

```bash
python .testing-suite/bin/suite.py --root . impact --base HEAD --output .testing-suite/state/selection.json
python .testing-suite/bin/suite.py --root . run --selection .testing-suite/state/selection.json
python .testing-suite/bin/suite.py --root . gate --selection .testing-suite/state/selection.json
```

Choose a real baseline for a branch, such as a verified successful base commit. `HEAD` also includes local changes. Explicit `--files` and `--nodes` support pre-implementation planning. The report lists affected nodes, selected tests, and selection reasons.

Missing or stale maps, unknown changes, invalid bindings, config/lockfile changes, and overdue full-suite checks widen selection to `FULL`. Critical, new, and previously failing tests remain included. Full fallback is an executable plan, not a passing result. Unknown or skipped evidence cannot pass the gate.

`run` executes configured native runner commands. A selected test invokes its whole configured runner; the runtime does not convert arbitrary test IDs into framework filters. The strict gate currently recognizes verbose unittest and pytest output and matches observed cases to graph paths/symbols. Zero-test, skipped, missing, nonverbose, and unsupported runner observations cannot pass. Other frameworks need an additional trusted result adapter. Output, exit status, fingerprints, and every attempt are saved locally. `record` imports external results as manual evidence, which cannot satisfy the release gate. See [run-evidence](skills/run-evidence/SKILL.md).

## Focused workflows

| Skill | Use |
| --- | --- |
| [bootstrap](skills/bootstrap/SKILL.md) | Inspect and initialize a project without replacing its conventions |
| [map-system](skills/map-system/SKILL.md) | Connect capabilities, instances, coordinates, dependencies, and proof |
| [plan-impact](skills/plan-impact/SKILL.md) | Predict affected behavior and choose a conservative validation scope |
| [design-tests](skills/design-tests/SKILL.md) | Author meaningful unit, integration, browser, contract, and invariant tests |
| [run-evidence](skills/run-evidence/SKILL.md) | Execute native runners and evaluate fresh evidence |
| [contracts](skills/contracts/SKILL.md) | Verify real consumer/provider expectations across repositories |
| [instance-parity](skills/instance-parity/SKILL.md) | Check shared behavior and tested intentional differences |
| [state-diff](skills/state-diff/SKILL.md) | Detect side effects outside an explicit JSON Pointer allowlist |
| [diagnose](skills/diagnose/SKILL.md) | Trace failures back to behavior and current source coordinates |
| [maintain](skills/maintain/SKILL.md) | Refresh indexes, graph evidence, full-suite cadence, and map coverage |

The root [SKILL.md](SKILL.md) routes these workflows. [Adapter recipes](references/ADAPTERS.md) cover Tree-sitter, SCIP, Backstage, Nx/Jest/Testmon, Pact, Playwright, OpenTelemetry, and Allure/ReportPortal. They describe integrations to configure; those systems are not bundled or active automatically.

## Runnable example and package checks

[minimal-python](examples/minimal-python/) models a fictional review capability with editable and read-only instances. Its README gives exact indexing, impact, parity, state-diff, and execution commands.

```bash
python -m unittest discover -s Gauntlet/tests -v
python Gauntlet/scripts/package_skill.py --validate-only
python Gauntlet/scripts/package_skill.py
```

Packaging produces `dist/testing-suite-0.1.0.tar.gz`, a ZIP-format `.skill`, and a SHA-256 manifest. The archives include the runnable tools, schemas, skills, and example; exclude local evidence, secrets, caches, and previous distributions. [Behavioral evals](evals/evals.json) are review scenarios, not claims of an executed model evaluation.

See [local verification](TEST-MATRIX.md) for the 46 passing package tests, exercised example, negative controls, and verification limits.

Python AST bindings have structural ranges. Other languages currently have file or explicit comment-anchor locations, and need an external adapter for AST/symbol precision. A declared graph can omit real dependencies; conservative full runs and maintained coverage remain essential. Cross-repo execution requires an explicitly configured repository registry, compatible environments, and real runner commands. Execution fingerprints bind evidence to source and graph state; they do not provide signed remote attestation.
