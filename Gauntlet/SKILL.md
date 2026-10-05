---
name: testing-suite
version: "0.1.0"
description: >-
  Bootstrap and operate an evidence-based testing suite for a project or related
  repositories. Use when installing the suite, mapping product behavior to code,
  planning change impact, designing tests, checking implementation parity or
  state changes, running and diagnosing tests, or maintaining test evidence.
---

# Testing suite

Use this skill as a router. Read the matching child skill and its linked protocols
before using its workflow. Existing repository instructions, tests, frameworks,
and user requirements remain authoritative. Installed skills do not create a new
permission barrier for reversible work already authorized by the user.

## Route the task

| Need | Read |
|---|---|
| Install the suite in a new or existing project | [bootstrap](skills/bootstrap/SKILL.md) |
| Connect product behavior, implementation instances, and source | [map-system](skills/map-system/SKILL.md) |
| Understand consequences before changing code or selecting tests | [plan-impact](skills/plan-impact/SKILL.md) |
| Turn requirements and risks into useful tests | [design-tests](skills/design-tests/SKILL.md) |
| Execute tests and establish what is actually verified | [run-evidence](skills/run-evidence/SKILL.md) |
| Verify boundaries between repositories or services | [contracts](skills/contracts/SKILL.md) |
| Compare multiple implementations of one capability | [instance-parity](skills/instance-parity/SKILL.md) |
| Detect unexpected effects on data or state | [state-diff](skills/state-diff/SKILL.md) |
| Trace a failure to exact product and source coordinates | [diagnose](skills/diagnose/SKILL.md) |
| Refresh mappings, suites, and durable evidence | [maintain](skills/maintain/SKILL.md) |

For a feature change, start with **plan-impact**, follow **design-tests** where
coverage is missing, execute **run-evidence**, then use **diagnose** for failures.
Read **map-system** first if mappings are missing or stale. For bootstrap requests,
complete installation and report unmapped behavior and uncovered invariants as
remaining work; installing the package is not evidence of product correctness.

## Shared model

Map the system in both directions:

```text
product / system / repository
  → capability → implementation instance → page or workflow
  → UI → action or event → function or logical block → live source coordinates
  → data reads and writes → cross-repository providers → invariant → tests
```

An implementation instance is a first-class node: a capability may appear on a
settings page, onboarding flow, admin interface, mobile client, or API. Shared
behavior belongs to the capability and its invariants; instance-specific
presentation and permitted differences belong to the instance and parity group.
Graph traversal must also answer “what product behavior could this function
change?” and “where is this behavior implemented and tested?”

Use stable node IDs and `@coord` anchors to preserve identity across line shifts.
Treat paths, lines, symbols, source hashes, and evidence as current observations,
not permanent identity. The graph is a reviewed model; indexing helps locate
source but cannot infer complete product semantics.

## Runtime boundary

The v0.1 runtime is a standard-library Python control layer. It validates a JSON
graph, indexes Python AST symbols and comment anchors, traverses relationships,
selects tests conservatively, invokes configured runner commands, observes verbose
unittest/pytest cases, records results, checks parity declarations, and compares
JSON state. Strict gates require supported observed cases; Node and other runner
commands can be inventoried/executed but need a future trusted observation
adapter to pass that gate. It does not ship live
Tree-sitter, SCIP, Backstage, Nx, Jest, Testmon, Pact, Playwright, OpenTelemetry,
Allure, or ReportPortal integrations. The narrow pytest/unittest output observers
do not supply framework-native affected selection. Follow [adapter recipes](references/ADAPTERS.md)
for using those tools alongside the graph.

After bootstrap, invoke the copied runtime from the project root:

```sh
python3 .testing-suite/bin/suite.py --root . validate
python3 .testing-suite/bin/suite.py --root . index
python3 .testing-suite/bin/suite.py --root . impact --base HEAD --output .testing-suite/state/selection.json
python3 .testing-suite/bin/suite.py --root . run --selection .testing-suite/state/selection.json
python3 .testing-suite/bin/suite.py --root . gate --selection .testing-suite/state/selection.json
```

`HEAD` is suitable for changes in the working tree. For a completed branch, choose
the reviewed merge-base or release baseline that includes all intended changes.
An empty graph cannot produce a meaningful green result.

## Non-negotiable evidence rules

- Missing, stale, or unmapped impact information requires a full configured run.
  Configuration and dependency lock changes also widen selection. Periodically
  run the full suite even when targeted selections pass.
- Always include known failing, newly introduced, and critical tests. Unknown
  coverage, skipped tests, and missing results cannot count as passing evidence.
- Keep evidence tied to its exact source, graph, selection, and runner execution.
  A passing result from another revision is historical evidence.
- Do not invent execution results, count test stubs as proof, hide retry history,
  or change intended product behavior merely to satisfy generated assertions.
- Use deterministic, synthetic or approved sanitized fixtures. Never copy
  production data, secrets, or personal data into a test fixture or report.

Read [graph conventions](protocols/GRAPH-CONVENTIONS.md),
[selection safety](protocols/SELECTION-SAFETY.md), and
[evidence requirements](protocols/EVIDENCE.md) for the operational details.
