# Testing-suite reference research

Verified on 2026-10-04 (America/New_York). These are design references, not instructions to execute or code copied into Mojo. Repository snapshots were read through the GitHub connector and pinned raw files; direct executor requests to `api.github.com` were blocked by the environment network policy. The links below identify the inspected sources.

## Verified snapshots and licenses

| Repository | Inspected commit | License |
| --- | --- | --- |
| [testland/qa](https://github.com/testland/qa) | `1257e232b9561d0a6f90c33bf9369da285671ca8` | MIT |
| [microsoft/playwright](https://github.com/microsoft/playwright) | `7ad3fba1aad9471c7e46d67a11b0e710a5d77ea8` | Apache-2.0 |
| [tarpas/pytest-testmon](https://github.com/tarpas/pytest-testmon) | `dccc58d2ed8edec98096ff1974acb7c07d3e3482` | MIT |
| [pact-foundation/pact-js](https://github.com/pact-foundation/pact-js) | `45d92bf5799a7758cf32babff506c71b7b0b9df2` | MIT; verified LICENSE text, although GitHub metadata reported NOASSERTION |
| [nrwl/nx](https://github.com/nrwl/nx) | `ead04276f840b920ffab97eb3f809fef2baf130b` | MIT |

Licenses: [testland](https://github.com/testland/qa/blob/1257e232b9561d0a6f90c33bf9369da285671ca8/LICENSE), [Playwright](https://github.com/microsoft/playwright/blob/7ad3fba1aad9471c7e46d67a11b0e710a5d77ea8/LICENSE), [testmon](https://github.com/tarpas/pytest-testmon/blob/dccc58d2ed8edec98096ff1974acb7c07d3e3482/LICENSE), [Pact](https://github.com/pact-foundation/pact-js/blob/45d92bf5799a7758cf32babff506c71b7b0b9df2/LICENSE), [Nx](https://github.com/nrwl/nx/blob/ead04276f840b920ffab97eb3f809fef2baf130b/LICENSE). Dependencies and browser bundles can have their own licenses. Reuse the concepts; preserve notices if copying substantial source.

## Patterns worth adopting

**testland test-impact analysis:** Keep a bidirectional test-to-source map. Selection includes impacted tests, previous failures, and new tests. Build/dependency/CI changes and unmapped files trigger a full run. Pair selection with periodic full runs that reveal missed regressions; show the chosen tests and reasons. [Selector](https://github.com/testland/qa/blob/1257e232b9561d0a6f90c33bf9369da285671ca8/plugins/qa-test-impact-analysis/skills/regression-suite-selector/SKILL.md).

Its [removal skill](https://github.com/testland/qa/blob/1257e232b9561d0a6f90c33bf9369da285671ca8/plugins/qa-test-impact-analysis/skills/test-removal-criteria/SKILL.md) treats pruning as a separate decision with evidence and a default to retain tests. Slow or flaky tests alone are poor removal candidates. Adopt separate selection, quarantine, and pruning workflows; never have the impact selector delete tests.

Caveats: The [instrumentation examples](https://github.com/testland/qa/blob/1257e232b9561d0a6f90c33bf9369da285671ca8/plugins/qa-test-impact-analysis/skills/regression-suite-selector/references/instrumentation-and-ci.md) are starting points. A merged Jest coverage file does not establish which test hit which source. PR-number modulo sampling is not a measured cadence since the last full run. Framework IDs, filenames, shell word splitting, rename/deletion cases, and artifact freshness require additional engineering. Do not advertise these snippets as validated universal adapters.

**Playwright:** Native `@` tags and typed annotations can carry feature, capability, and flow IDs into reports. `--grep` supports tag selection, and group metadata propagates to its tests. The documented config includes CI `forbidOnly`, bounded workers/retries, traces, artifact directories, browser projects, and managed web-server startup. [Tags](https://github.com/microsoft/playwright/blob/7ad3fba1aad9471c7e46d67a11b0e710a5d77ea8/docs/src/test-annotations-js.md), [configuration](https://github.com/microsoft/playwright/blob/7ad3fba1aad9471c7e46d67a11b0e710a5d77ea8/docs/src/test-configuration-js.md).

Adopt stable metadata instead of inferring product identity from test titles. Preserve distinct first-attempt pass, retried pass, and exhausted failure outcomes. [Retries](https://github.com/microsoft/playwright/blob/7ad3fba1aad9471c7e46d67a11b0e710a5d77ea8/docs/src/test-retries-js.md). Tags are regex filters; escape generated expressions and do not conflate `@feature:cart` with `@feature:cart-admin`. Shared state can invalidate full parallelism. Traces can contain sensitive app data; follow repository artifact policy.

**pytest-testmon:** Use the existing plugin for Python execution-level dependency tracking. Its first `pytest --testmon` run creates `.testmondata`; later runs reuse the database for affected tests. [README](https://github.com/tarpas/pytest-testmon/blob/dccc58d2ed8edec98096ff1974acb7c07d3e3482/README.md). The database tracks environment, installed packages, Python version, test outcomes, and source fingerprints. [Database](https://github.com/tarpas/pytest-testmon/blob/dccc58d2ed8edec98096ff1974acb7c07d3e3482/testmon/db.py).

Prefer an adapter or import seam over reimplementing its tracer. Testmon can disable selection when manual `-k`, `-m`, `--lf`, or node IDs are used, and collection under a debugger also differs. [Configuration](https://github.com/tarpas/pytest-testmon/blob/dccc58d2ed8edec98096ff1974acb7c07d3e3482/testmon/configure.py). Capture the actual execution mode. A dynamic trace from one configuration does not prove all conditional runtime dependencies have been covered.

**Pact:** Separate consumer assumptions from provider verification. Consumers exercise their real API client against Pact's mock and publish contract artifacts; providers replay those artifacts with deterministic state handlers. Record consumer/provider version, contract identity, and verification state in the graph. [Consumer](https://github.com/pact-foundation/pact-js/blob/45d92bf5799a7758cf32babff506c71b7b0b9df2/docs/consumer.md), [provider](https://github.com/pact-foundation/pact-js/blob/45d92bf5799a7758cf32babff506c71b7b0b9df2/docs/provider.md).

Contract coverage is limited to authored interactions and does not replace full journeys. A generated contract alone is not a verified contract. Keep test fixtures isolated, remove obsolete generated pact artifacts before regeneration, and use versioned broker selectors when a broker is already configured. A new bootstrap should not invent a broker or publish contracts automatically.

**Nx:** Native affected execution combines Git changes with project dependencies and follows reverse dependencies. CI should compare against a known successful main commit with enough history. Lockfile changes default to affecting every project as a failsafe. [Affected guide](https://github.com/nrwl/nx/blob/ead04276f840b920ffab97eb3f809fef2baf130b/astro-docs/src/content/docs/features/CI%20Features/affected.mdoc), [reverse traversal](https://github.com/nrwl/nx/blob/ead04276f840b920ffab97eb3f809fef2baf130b/packages/nx/src/project-graph/affected/affected-project-graph.ts).

The inspected development snapshot additionally describes optional task-level selection. That mode depends on accurate declared inputs/outputs; ordering `dependsOn` edges alone do not establish an impact edge. Treat Nx version capabilities as detected, not assumed. Native affected results describe projects/tasks, not product-flow evidence.

## Decisions for Mojo's thin control layer

1. Keep existing runners and build graphs as executors. Add a portable, schema-validated graph connecting flows, features/capabilities, source paths/symbols, contracts, tests, owners, and run evidence.
2. Each edge should retain its origin (declared, imported, static inference, dynamic trace), capture commit/environment, and freshness. Planning inference is useful but should not silently become verified coverage.
3. Select reverse impact plus changed/new tests and previous failures. Widen for unknown inputs, config/dependency changes, invalid graph references, missing Git base, stale evidence, or empty uncertain selection. Emit both IDs and reasons. Explicit documented-only exclusions need maintained policy.
4. Use PR merge-base diff for branch changes and a last successful baseline for continued mainline failure coverage. Do not equate these two comparisons.
5. Bootstrap incrementally: inspect stack and current tests, preserve existing configuration, generate owned files with an idempotent manifest, and leave optional adapters inactive until configured. Bootstrap plans should name assumptions and missing coverage rather than claim comprehensive test success.
6. Keep full-run execution and result reporting separate from selection. Preserve retried passes and quarantines, and compare occasional full runs against selection to assess misses.
