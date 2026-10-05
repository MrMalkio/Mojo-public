---
name: testing-suite-design-tests
description: >-
  Design and implement meaningful tests from product invariants, change impact,
  boundaries, implementation differences, and data effects. Use when coverage is
  missing, requirements change, or existing tests fail to assert real behavior.
---

# Design tests from behavior

Start with the requirement and its failure risk. Read the impact plan and relevant
source before choosing assertions or frameworks. A test should detect an actual
regression, not reproduce the implementation line by line.

## Choose the right scope

| Risk | Useful scope |
|---|---|
| Deterministic transformation or branch | Unit/property test with boundary inputs |
| Persistence, transaction, cache, or permission boundary | Integration test with realistic local dependencies |
| Consumer/provider request or response assumption | Contract test plus provider verification |
| User action across UI, API, and storage | Small workflow test with observable outcomes |
| Shared capability across multiple surfaces | Invariant matrix and instance-specific tests |
| Unexpected writes or side effects | Before/after state assertions with a narrow allowlist |

Use frameworks already established by the project. Select external tools by scope:
Pact can verify consumer/provider assumptions, Playwright can exercise browser
workflows, and property-testing frameworks can explore invariants. The control
layer does not implement those frameworks. See [adapter recipes](../../references/ADAPTERS.md).

## Build a behavior contract

1. State the invariant in observable terms: inputs, actor/permissions, action,
   expected result, expected persisted state, and prohibited side effects.
2. Include a representative success case and relevant boundaries: absent or
   invalid data, repeated action/idempotency, authorization, time, concurrency,
   or upstream failure. Add cases only where the capability or change warrants
   them; avoid a universal checklist that bloats a simple fix.
3. Enumerate implementation instances. Shared semantics must hold across them;
   record intended differences such as toggle versus checkbox, or editable versus
   read-only, before asserting parity.
4. Select the smallest test scope that catches the regression. Reserve costly
   end-to-end tests for behavior that lower scopes cannot establish reliably.
5. Use deterministic clocks, seeded inputs, isolated resources, and synthetic
   fixtures. Keep setup bounded and cleanup explicit; do not depend on production
   data, ambient users, network availability, or test execution order.
6. Implement the test in the existing test tree and confirm it is discoverable by
   its configured runner. Add graph `covers`/`verifies` relationships only after
   inspecting the assertions.

When practical, demonstrate that a new regression test fails with the old defect
and passes with the intended fix. Do not keep a deliberate product regression in
the workspace to demonstrate this. For a new feature, verify meaningful negative
and boundary cases instead of treating initial implementation agreement as proof.

## Review test quality

Check that removing the relevant behavior would fail the test. A stub, skipped
case, always-true assertion, broad mock that hides the dependency, or snapshot
without understood semantics does not verify the invariant. Assertions should
survive harmless refactoring while rejecting behavior changes that violate the
requirement.

If the test and product disagree, inspect the contract. Fix an incorrect test or
implementation based on the intended behavior; do not alter product behavior
merely because a generated assertion expects something else. Surface unresolved
product decisions with a concrete example and continue independent work.

Return implemented test IDs, the invariants and instances they cover, fixture
choices, runner command, and remaining gaps. Follow [run-evidence](../run-evidence/SKILL.md)
to establish execution evidence; authored tests alone have no passing status.
