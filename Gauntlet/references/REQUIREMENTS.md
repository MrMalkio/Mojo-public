# Source requirements and implementation boundary

The source is the ChatGPT chat **Our super testing suite**, conversation `6abf243b-5d90-83e9-9837-b9fd45ed5f33`, read for this build. The available response contains five recent turns, including the framework research and the user's explicit implementation-instance requirement. There were no older turns available through its cursor. The design below uses that available context; it does not reconstruct unseen discussion.

| Source requirement | Deliverable |
| --- | --- |
| Product intent ↔ implementation ↔ proof | Authored graph, navigation CLI, map-system skill |
| List all implementations of a capability | First-class `instance` nodes, `implements` edges, instance-parity skill |
| Toggle, checkbox, button, read-only variants | Shared invariants plus explicit, reasoned, tested variances |
| File/function/logical-block coordinates | Python AST symbol ranges and named comment anchors; index and drift diagnostics |
| Cross-repo dependency impact | Repository registry, consumer→provider edges, reverse impact traversal, contracts skill |
| Plan before changing implementation | plan-impact skill, node/file/Git based selection |
| Change→tests with conservative fallback | Impact CLI, critical/new/failing inclusion, periodic full policy |
| Unexpected state changes | JSON Pointer state-diff tool and scoped state-diff skill |
| Debug with precise locations | Indexed bindings, bidirectional navigation, diagnose skill |
| Keep the map current | Fingerprints, freshness checks, maintain skill |
| Structured release evidence | Actual runner execution, recorded provenance and strict gate |
| Project setup | Dry-run, collision preflight, portable bootstrapper, opt-in CI |

The framework examples are reference patterns. This package supplies a small control layer and workflow recipes. It does not bundle Tree-sitter, a SCIP indexer, Backstage, Pact, Playwright, OpenTelemetry, Allure, or ReportPortal. Python AST parsing is implemented; other source languages use explicit anchors and file bindings until an adapter supplies stronger information. Anchor locations do not prove function or logical-block boundaries.

The included example is a fictional review capability. It is not a verified map of Steady Stars, Zeus, Wizard, OMA, or Staff. Those systems must be inventoried from their actual repositories before authoring contracts or declaring parity.

## Extension path

1. Establish a complete graph and reliable full test runner in one real project; replace inventory placeholders with reviewed invariant coverage.
2. Import SCIP symbols or Tree-sitter structure, retaining exporter/version/source provenance and stable IDs.
3. Add framework selectors that demonstrate per-test coverage or dependencies; runner-level execution remains the conservative proof unit until then.
4. Verify actual consumer/provider contracts and import redacted runtime observations as observed dependency edges.
5. Export evidence to existing reporting tools; use periodic full-suite comparisons to measure selector misses.

These are extension points, not claims that those integrations execute in this version.
