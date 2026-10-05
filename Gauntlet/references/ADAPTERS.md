# External tool workflow recipes

These recipes explain how to use established tools with the control layer. They
are not installed plugins, executable adapters, or claims of live integration.
Use the project's versions, documented commands, authentication, and existing CI
conventions. Do not install every tool simply because it appears here.

The runtime's native v0.1 features are Python AST/comment-anchor indexing, JSON
graph navigation and conservative selection, configured runner execution,
verbose unittest/pytest case observation, manual result recording, parity
declaration checks, and supplied JSON state comparison. Rich language references,
framework case filtering, contract brokers, browser automation, distributed
tracing, and external dashboards remain in their respective tools.

## Current execution observation boundary

Strict observation supports `unittest` and `pytest` only. Set the optional config
runner `adapter` accordingly, or use recognized native commands. Use native
verbose output (`python3 -m unittest discover -s tests -v` or
`python3 -m pytest -v`) with reviewed project scope. Ensure pytest quiet options
do not override case reporting. Required graph tests need observed path/qualified
symbol matches; positive process exit alone is insufficient. Prefer individual
test symbols over broad file-level nodes.

Unittest requires positive `Ran N tests` collection and individual method outcomes;
pytest observes `file.py::Class::case` statuses and zero-collection signals. Zero
tests, missing/nonverbose observations, absent cases, required skips, and unknown
adapters fail verification. Node/Jest, Pact, and Playwright runner inventories can
execute and retain logs, but cannot pass the strict gate through these recipes.
They need a future tested observation adapter; setting `adapter: "pytest"` on a
Node command does not provide one. Commands remain the trusted collection
boundary, and observations do not establish product semantics by themselves.

## Adapter handoff rules

An adapter should emit machine-readable observations tied to exact repository
revision and source hash, stable graph IDs, observed path/range, tool/version,
command, and artifact. Keep observations distinct from reviewed product semantics.
Validate IDs and provenance before updating graph/index state. Missing, stale,
ambiguous, or unsupported data must widen selection or remain an explicit gap.
Do not convert raw external “success” into trusted gate evidence without verifying
executed scope, failures/skips, retries, and source identity.

Use argument-array runner commands in `.testing-suite/config.json`. A runner can
invoke an existing project script that orchestrates an external tool. v0.1
executes the full configured suite needed by selected tests; it does not translate
test IDs into that tool's filter syntax or import arbitrary per-case reports.

## Source intelligence: Tree-sitter and SCIP

Use [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) for language-aware
syntax ranges and [SCIP](https://github.com/sourcegraph/scip) with an appropriate
language indexer for semantic definitions/references.

1. Produce an index from the exact checked-out source using the project's language
   tooling. Retain source revision, file hashes, language/indexer version, and
   parse/index diagnostics.
2. Match graph `path`/`symbol`/`anchor` entities to unique definitions and ranges.
   Resolve call/reference relationships as code evidence; review whether they
   establish a product dependency before adding graph edges.
3. Keep stable graph IDs while refreshing observed coordinates. Ambiguous symbols,
   generated-code differences, unresolved external references, and stale indexes
   must remain visible.

Do not label lexical proximity as a semantic call or claim Python AST indexing
offers equivalent cross-language reference resolution.

## System ownership: Backstage

[Backstage's software catalog](https://backstage.io/docs/features/software-catalog/)
can supply repository/component/API ownership and declared dependencies.

1. Read the project's existing catalog entities and their source locations.
2. Reconcile repository/system/service/API nodes and dependency edges with actual
   manifests and call sites. Record catalog provenance and unresolved entries.
3. Preserve product capabilities, instances, state effects, and test invariants
   from inspected requirements/source; a service catalog cannot infer them.

No Backstage server or catalog synchronization is provided by v0.1.

## Affected execution: Nx, Jest, and Testmon

Use [Nx affected](https://nx.dev/ci/features/affected) for an existing Nx workspace,
[Jest CLI](https://jestjs.io/docs/cli) for its project-specific related-test
selection, or [Testmon](https://testmon.org/) for an existing Python coverage-based
dependency workflow.

1. Establish the same complete base/head and current dependency/lock state as the
   graph selection. Keep the tool's dependency data fresh.
2. Compare its affected set with required graph tests. Always retain critical,
   new, and failing tests and their owning suites.
3. Full-run when graph/tool data is missing or stale, a lock/config changed, an
   affected test lacks a safe mapping, or full-run cadence is due.
4. Execute the reviewed project command and retain actual test reports. Never
   treat a predicted test list as execution evidence.

Any script used as a configured runner must reliably execute its declared scope.
The suite does not generate framework filters or maintain Testmon databases.

A merged Jest coverage report does not establish which individual test executed
each source block. Testmon's selection mode can change with `-k`, `-m`, `--lf`,
manual node IDs, or debugging; capture actual mode and environment/package/Python
identity rather than assuming a warm database always performs selection. Detect
installed Nx capabilities; project/task impact is not product-flow evidence.

## Boundary contracts: Pact

Use [Pact](https://docs.pact.io/) where consumer-driven contracts fit the boundary.

1. Map consumer call sites, provider API/event/service, involved repositories,
   and compatibility invariants.
2. Run consumer tests with synthetic inputs to produce contract artifacts from
   the actual consumer revision.
3. Verify contracts against the intended provider revision using controlled
   provider states. Retain both revisions, contract identity, verification logs,
   and any broker compatibility outcome if the project uses a broker.
4. Link real contract tests and invariants into the graph; run all affected
   consumer/provider verification commands through existing scripts.

A valid schema or passing isolated provider test does not establish consumer
compatibility. v0.1 does not operate a Pact broker or deployment check.
Regenerate contract artifacts cleanly so obsolete interactions do not survive.
Broker publication/setup is a separate project action, not a bootstrap default.

## User workflows: Playwright

Use [Playwright](https://playwright.dev/docs/intro) with the project's established
test configuration for browser behavior.

1. Choose a small set of workflows whose risk crosses UI/API/state boundaries.
   Map capability instances, actions, invariants, and test IDs.
2. Use isolated contexts, seeded synthetic data, controlled clocks where needed,
   resilient user-facing selectors, and semantic outcome assertions.
3. Capture traces/screenshots/video only as configured and useful for diagnosis;
   preserve source revision and retries. Keep secrets and personal data out.
4. Compare permitted instance differences and before/after state separately from
   visual presentation. A matching screenshot does not establish persistence.

No browser is launched by `parity` or `state-diff`. Configure a real Playwright
project runner when browser verification is needed.
Stable capability/instance tags can help preserve product identity in reports.
Playwright tag selection uses regular expressions; escape generated IDs and
check exact matches rather than confusing similarly prefixed capabilities.

## Runtime diagnosis: OpenTelemetry

Use [OpenTelemetry](https://opentelemetry.io/docs/) instrumentation and exporters
already approved for the project.

1. Reproduce the scenario with a known test/execution ID and source revision.
2. Correlate spans with service/function graph IDs using real instrumented
   attributes and inspected source. Retain trace context and relevant errors.
3. Use temporal order, calls, and data effects to form a hypothesis; confirm it
   with source inspection and a reproducing assertion.

Tracing provides observations, not automatically correct dependency edges or a
test pass. The suite neither instruments services nor configures collectors.

## Reports: Allure and ReportPortal

Use [Allure](https://allurereport.org/docs/) or
[ReportPortal](https://reportportal.io/docs/) reporters already in the project.

1. Retain execution ID, exact source/selection, commands, required test IDs,
   failures, skipped cases, attachments, and retry attempts.
2. Link external report artifacts from the local evidence report. Inspect per-case
   discovery/outcomes when assessing runner-suite success.
3. Keep local gate provenance and actual logs authoritative until a trusted
   importer has been implemented and verified. `record` remains manual evidence.

No report upload, account connection, or reporting server setup is performed by
v0.1. A dashboard's green aggregate must not conceal missing required coverage.

## Selection pattern reference

The inspected [testland/qa impact selector](https://github.com/testland/qa/tree/1257e232b9561d0a6f90c33bf9369da285671ca8/plugins/qa-test-impact-analysis)
informs the fail-safe pattern: retain previous failures and new tests, widen for
unknown/configuration/dependency changes, expose selection reasons, and pair
targeted selection with full runs. Its examples are design references, not
validated universal adapters. Test selection never deletes tests; pruning or
quarantine is a separate reviewed decision. Slow/flaky status alone does not
justify removing coverage. See [source notes](SOURCES.md) for inspected revisions
and licenses; this package does not vendor those
tools' implementation source.
