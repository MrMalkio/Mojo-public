---
name: testing-suite-diagnose
description: >-
  Trace a failing test, contract, parity check, or state change to exact current
  source and affected product behavior. Use for reproducible debugging, stale
  coordinates, ambiguous failures, and flaky test investigation.
---

# Diagnose with exact coordinates

Preserve the first failure, runner output, source revision, selection, and fixture.
Use the smallest reproducible scope that still exercises the failing behavior.
Do not erase failure history by rerunning until something passes.

## Establish the observation

1. Separate assertion failure, runner/setup failure, missing coverage, stale
   provenance, graph validation error, and nondeterministic behavior. Each needs
   different corrective action.
2. Read the failure's actual input, expected/observed result, stack trace, and
   state/event artifacts. Confirm which invariant was violated.
3. Navigate from the test or invariant to its implementation instances and
   dependencies; also navigate from the failing symbol or anchor back to product
   behavior. Inspect neighboring logical blocks rather than guessing from a name.

```sh
python3 .testing-suite/bin/suite.py --root . navigate --id test:notification-save
python3 .testing-suite/bin/suite.py --root . navigate --query notification-save
python3 .testing-suite/bin/suite.py --root . index
```

Use actual project IDs and query terms. Re-index to resolve current coordinates.
If the anchor is missing, duplicated, or moved without a corresponding map
update, repair the mapping before relying on it for narrow selection.

## Trace cause and impact

Inspect source at the current path, symbol, start/end lines or anchor, then follow
the relevant calls, data reads/writes, and provider boundaries. With distributed
trace artifacts, connect spans to the graph's functions or services using real
trace context and source revision; OpenTelemetry is an external tool, not an
automatic runtime capability. Correlation is a lead, not proof of root cause.

For a parity failure, compare the specific shared invariant across its instances
and read any declared variance. For state drift, inspect exact changed JSON
Pointers and every plausible writer. For a contract failure, compare consumer and
provider versions and real request/response semantics.

For a suspected flake, preserve attempts and investigate controlled time, random
seeds, resource isolation, order, asynchronous completion, and environmental
dependencies where the evidence points. Quarantine only under project policy and
keep the coverage gap visible; a skipped test does not become a passing result.

## Repair and verify

Fix the cause or an incorrect assertion according to intended behavior. Add a
meaningful regression test when the gap warrants it. Revalidate/re-index, regenerate
impact from the complete change, and run the selected runners. Expand to full
scope for uncertain or stale impact. Follow [run-evidence](../run-evidence/SKILL.md).

Return the failure and invariant, affected capability/instances, exact current
repository/path/symbol/anchor/line, evidence for cause, fix, and verification.
Separate confirmed findings from hypotheses. If a dependency or environment is
unavailable, name the missing observation and preserve the reproduction.
