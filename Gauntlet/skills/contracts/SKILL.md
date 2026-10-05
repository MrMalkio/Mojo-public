---
name: testing-suite-contracts
description: >-
  Map and verify consumer/provider contracts across services, repositories, APIs,
  events, and shared resources. Use when a boundary or dependency changes or
  consumers may be affected by provider behavior.
---

# Verify system boundaries

Contracts capture what an actual consumer needs from its provider. Inspect both
sides where available; an API schema alone does not establish that consumers
handle behavior, errors, or compatibility correctly.

## Map the boundary

1. Identify the calling instance/action/function, provider API/service/resource,
   repository owners, and version or deployment relationship.
2. Add consumer-to-provider `consumes`, `invokes`, or `depends_on` relationships,
   plus data `reads`/`writes` edges where relevant. Cite the inspected call site,
   handler, schema, or event evidence. Record unresolved external boundaries.
3. Specify observed request/event shape, response, errors, authorization,
   timeouts, compatibility expectations, and prohibited side effects. Include
   ordering/idempotency only where the real workflow depends on them.
4. Link the boundary invariant to executable consumer and provider tests. Keep
   provider-wide conformance tests separate from a particular consumer's needs.

## Exercise the contract

Use the project's existing contract tooling. For Pact, follow the
[adapter recipe](../../references/ADAPTERS.md): run the real consumer test to
produce a contract, verify it against the relevant provider revision with bounded
synthetic provider states, and retain both revisions and verification output.
The suite runtime orchestrates configured runner commands; it neither downloads
Pact contracts nor implements broker compatibility checks.
Pact-only output is outside the v0.1 unittest/pytest observation boundary: logs can
be retained, but the strict gate cannot certify it without a trusted adapter.
Report actual external contract verification and that runtime limit separately.

Where no contract framework exists, use focused integration tests with explicit
fixtures and assertions at the boundary. Avoid mocks that always return the
desired response without checking the consumer's assumptions. Use isolated local
dependencies or approved test environments and deterministic failure cases.

```sh
python3 .testing-suite/bin/suite.py --root . navigate --id api:notification-preferences
python3 .testing-suite/bin/suite.py --root . impact --nodes api:notification-preferences --output .testing-suite/state/contract-selection.json
python3 .testing-suite/bin/suite.py --root . run --selection .testing-suite/state/contract-selection.json
```

The ID is illustrative. For an actual code change, regenerate selection from its
complete baseline diff. A provider change should traverse back to consumers and
their product instances, including other repositories. If a consumer repo is
unavailable or its tests cannot run, identify that coverage gap; a local provider
pass does not establish cross-repository compatibility.

## Review compatibility

Distinguish additive changes, renamed/removed fields, semantic default changes,
authorization changes, error handling, and event evolution. An unchanged schema
can still hide changed semantics. Check rollout order when consumer and provider
cannot be deployed atomically.

Return the boundary and invariant, consumer/provider revisions, executed commands,
contract artifacts, dependency impact, and unresolved verification. Add justified
compatibility behavior to the graph; do not weaken an assertion merely to make a
new provider response pass.
