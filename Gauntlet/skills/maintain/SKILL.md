---
name: testing-suite-maintain
description: >-
  Keep graph mappings, coordinates, selections, fixtures, runner configuration,
  parity declarations, and evidence aligned with an evolving project. Use for
  suite upkeep, drift repair, full-run cadence, or adoption audits.
---

# Maintain the suite

Keep durable reviewed configuration and graph data in version control. Treat
runtime state as generated evidence. Read [graph conventions](../../protocols/GRAPH-CONVENTIONS.md),
[selection safety](../../protocols/SELECTION-SAFETY.md), and
[evidence requirements](../../protocols/EVIDENCE.md).

## Review a change or requested audit

1. Validate graph/config and re-index current source. Inspect missing, duplicate,
   renamed, or moved anchors and stale symbols. Preserve stable IDs when behavior
   identity survives; remove obsolete nodes only after reviewing their consumers.
2. Compare actual capabilities and instances to the graph. Refresh page/workflow,
   actions, logical blocks, data effects, cross-repository dependencies, and
   invariants where inspected source or requirements changed.
3. Inspect coverage claims: executable assertions, runner discoverability,
   missing instance/invariant cells, critical flags, new/failing tests, skipped
   cases, and tested variance justifications. Delete false coverage claims rather
   than leaving them green.
4. Verify runner commands, dependencies, CI root, fixture isolation, and artifact
   retention against existing project conventions. Inspect config and lock changes
   as full-scope triggers.
5. Run the full suite when its configured cadence is due, after meaningful mapping
   repair, or when targeted evidence cannot establish impact. Record all failures
   and required skipped cases; investigate flakes instead of hiding them.

```sh
python3 .testing-suite/bin/suite.py --root . validate
python3 .testing-suite/bin/suite.py --root . index
python3 .testing-suite/bin/suite.py --root . parity
python3 .testing-suite/bin/suite.py --root . impact --full --output .testing-suite/state/full-selection.json
python3 .testing-suite/bin/suite.py --root . run --selection .testing-suite/state/full-selection.json
python3 .testing-suite/bin/suite.py --root . gate --selection .testing-suite/state/full-selection.json
```

Use the current project policy's `full_suite_every_days`; establish a practical
cadence during adoption if it is absent. A request for upkeep does not itself
request a recurring automation. Create schedules only when the user asks.

## Preserve useful history

Keep source-bound results and runner artifacts long enough to investigate
regressions and retries. Runtime evidence after a source/graph/config change is
historical; do not hand-edit it into a current passing record. If reports go to
Allure or ReportPortal, preserve execution IDs, scope, provenance, and retry
history using the project's existing reporter. See [adapter recipes](../../references/ADAPTERS.md).

Package updates are reviewed upgrades, not forced re-bootstrap overwrites. The
bootstrapper refuses differing managed files. Inspect changed package contents,
project customizations, and schemas; merge deliberately and rerun validation.
Keep modifications within the user's requested scope.

Return changes made, mapping/coverage gaps, coordinate drift repaired, runner and
full-scope results, and required follow-up. Never report “healthy” merely because
the graph validates or the latest targeted runner passed.
