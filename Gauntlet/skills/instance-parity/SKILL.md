---
name: testing-suite-instance-parity
description: >-
  Compare first-class implementation instances of a shared capability, verify
  common invariants, and document tested intentional differences. Use for parity
  drift across pages, workflows, roles, platforms, or API/UI implementations.
---

# Check implementation parity

Parity means shared semantics hold across the applicable instances. It does not
require identical widgets, layouts, roles, or write permissions. Read the
capability requirements before declaring a difference accidental.

## Define the matrix

1. Inventory every inspected instance of the capability and give each a stable
   `instance` node. Connect instances to the capability with `implements`.
2. Define shared invariant nodes in observable terms. Map the tests for each
   applicable instance through coverage and ownership relationships.
3. Add a `parity_groups` entry containing `id`, `capability`, `instances`, and
   `shared_invariants`. A variance requires `instance`, `invariant`, `reason`,
   and `test`; the referenced test must actually check the permitted behavior.
4. Review widget/presentation, read/write permissions, validation, persistence,
   defaults, errors, and side effects only where they are part of the capability.

A fictional notification capability might use a toggle in settings, a checkbox
during onboarding, and a read-only summary for a viewer role. The first two may
share “persist the chosen value”; the viewer instance intentionally cannot write.
Its variance needs a reason grounded in permissions and a test proving that
read-only behavior. A difference in widget type alone does not imply a failure.

## Run declaration and behavior checks

```sh
python3 .testing-suite/bin/suite.py --root . validate
python3 .testing-suite/bin/suite.py --root . parity
python3 .testing-suite/bin/suite.py --root . impact --nodes capability:notifications --output .testing-suite/state/parity-selection.json
python3 .testing-suite/bin/suite.py --root . run --selection .testing-suite/state/parity-selection.json
python3 .testing-suite/bin/suite.py --root . gate --selection .testing-suite/state/parity-selection.json
```

`parity` checks the graph's declarations and mappings. It is not a browser runner,
does not compare screenshots, and does not execute behavior. Read the mapped
assertions and execute the needed runners to establish parity evidence. For an
actual change, include its complete diff and re-index before final selection.

## Handle drift

When an instance differs, identify the exact invariant, path/symbol/anchor, test,
and observable behavior. Decide from requirements whether to repair a defect,
update a legitimately changed invariant, or add a tested intentional variance.
Do not grant a variance merely to silence a failing parity check. Changes to a
shared invariant require reviewing all its instances and dependent consumers.

Return a compact invariant-by-instance matrix with coverage/evidence state,
intentional differences, accidental drift, and uncovered cells. An unmapped
instance or unexecuted test remains unknown even when another instance passes.
