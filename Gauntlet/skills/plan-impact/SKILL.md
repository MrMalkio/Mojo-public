---
name: testing-suite-plan-impact
description: >-
  Plan a change before editing by tracing affected product behavior, implementation
  instances, state, dependencies, invariants, and tests. Use for impact analysis,
  conservative test selection, or deciding whether a full suite is required.
---

# Plan change impact

Read [selection safety](../../protocols/SELECTION-SAFETY.md). Establish the intended
behavior change and compare it to the existing contract before editing code.

## Inspect the proposed change

1. Identify the baseline covering the entire change: working-tree comparison to
   `HEAD`, a reviewed branch merge-base, or the previous release. Do not choose
   the most recent commit if earlier branch changes also need verification.
2. Inspect the exact files, symbols, anchors, or graph nodes expected to change.
   Traverse back to affected capabilities and implementation instances, then
   forward to consumers, data writes, contracts, invariants, and tests.
3. Check graph freshness and completeness. Re-index current source; investigate
   deleted or ambiguous coordinates and unmapped files. Preserve the previous
   evidence as historical when the source or graph changes.
4. Write a short plan: intended behavior, affected instances, shared invariants,
   intentional differences, state effects, cross-repository boundaries, required
   tests, and reasons a wider run may be needed.

## Produce a selection

```sh
python3 .testing-suite/bin/suite.py --root . index --base HEAD
python3 .testing-suite/bin/suite.py --root . impact --base HEAD --output .testing-suite/state/selection.json
```

For an explicit planned scope before editing:

```sh
python3 .testing-suite/bin/suite.py --root . impact --files src/notifications.py --nodes capability:notifications --output .testing-suite/state/selection.json
```

Replace the sample path and ID with inspected entities. Explicit scope supplements
what is known; it is not proof that unlisted changes are harmless. After editing,
regenerate impact from the complete diff before the final run.

The selector follows graph relationships and adds failing, new, and critical
tests. Missing or stale index data, unmapped changes, uncertain impact, project
configuration changes, or dependency lock changes require full configured scope.
Use `impact --full` for release validation, periodic full runs, or an intentionally
wider check. If a repo has no executable coverage for a selected invariant,
design a meaningful test or report that gap; narrowing scope cannot fix it.

## Review and proceed

Inspect the selection's reasons and required test IDs. Confirm that each selected
test is mapped to an actual configured runner. v0.1 executes whole runner suites
needed by selected tests; it does not translate graph test IDs into framework
filters. Framework-native affected-test tooling can help assess scope but does
not override missing graph evidence.

Proceed with reversible edits within the user's authorized task. Escalate a
product decision only when requirements truly conflict or essential behavior is
unknown; this workflow does not impose an extra approval step. Follow
[design-tests](../design-tests/SKILL.md) for missing coverage and
[run-evidence](../run-evidence/SKILL.md) for execution.
