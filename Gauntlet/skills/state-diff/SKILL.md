---
name: testing-suite-state-diff
description: >-
  Detect unexpected side effects by comparing bounded before/after JSON state
  against exact allowed changes. Use for persistence regressions, event effects,
  permission checks, transaction behavior, or surprising data mutations.
---

# Inspect state effects

Start with the action's intended reads, writes, and prohibited effects. The
comparison is useful only when snapshots represent a consistent, isolated scope.
The v0.1 runtime compares supplied JSON; it does not connect to databases or
capture application state automatically.

## Capture a bounded scenario

1. Identify the capability instance, actor, action/event, input fixture, data
   nodes, and dependent services. Use synthetic or approved sanitized data.
2. Define the allowed state changes before execution, including exact values or
   semantic assertions in the scenario test. Keep “must not change” fields in
   the snapshot where they represent a meaningful risk.
3. Capture the bounded JSON before state, execute one action, then capture after
   state at a consistent point. Use a local transaction/test database or other
   isolated environment; avoid shared mutable production resources.
4. Normalize only known representation noise, such as test-controlled timestamps
   or non-semantic ordering. Document each normalization. Do not remove a field
   because it produced an inconvenient difference.
5. Store expected allowed paths in an allowlist. Use exact JSON Pointers, with
   `~0` for a literal tilde and `~1` for a literal slash in a key.

```sh
python3 .testing-suite/bin/suite.py --root . state-diff --before .testing-suite/state/state-before.json --after .testing-suite/state/state-after.json --allow .testing-suite/state/state-allow.json
```

The allowlist file is a JSON array, such as `["/preferences/notifications"]`.
All snapshot/allowlist filenames are project-relative; the state directory keeps
these ephemeral artifacts out of version control. A
permitted path allows differences only at that exact pointer, not arbitrarily
under a parent. Avoid broad parent paths and never auto-generate the allowlist
from the observed diff. For a single pointer, the alternate CLI form is
`--allow /preferences/notifications`.

## Interpret the comparison

Read additions, removals, value changes, and unexpected paths. Missing and
explicit `null` are distinct states. Check array semantics before accepting an
index-based difference: a reorder may be meaningful, or the scenario may need
stable IDs and intentional normalization.

An allowed difference is not proof that the expected change happened. A dedicated
test must assert the required new value, event count, idempotency, or transaction
outcome. Combine that assertion with a clean unexpected-difference report.

For unexpected changes, trace the affected data node back through writers,
actions, implementation instances, dependencies, and tests. Follow
[diagnose](../diagnose/SKILL.md) and include this state artifact in the evidence.
The state-diff exit result alone does not establish that the whole test suite
passed; use [run-evidence](../run-evidence/SKILL.md) for the appropriate runners.

Return the scenario scope, snapshots, exact allowed pointers with reasons,
unexpected changes, and the test proving expected behavior. Redact sensitive
values in user-facing reports without obscuring the field or consequence.
