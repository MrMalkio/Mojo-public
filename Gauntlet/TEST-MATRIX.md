# Local verification

Verified on 2026-10-04 in the client's America/New_York timezone. These are executed local checks of this package and its synthetic fixture. They do not establish production-project coverage or a remote CI result.

```bash
python -m unittest discover -s Gauntlet/tests -v
```

46 tests passed: 19 bootstrap checks, 16 core runtime checks, 5 independent regression checks, 1 archive/install/runner integration, 2 packaging checks, and 3 skill structure checks.

| Area | Executed verification |
| --- | --- |
| Bootstrap | Dry-run creates nothing; identical reruns perform no writes; original files and unrelated ignore edits survive |
| Write safety | Late collisions prevent all writes; symlinks rejected; injected write failure rolls back generated files and preserves original modes |
| Discovery | Real unittest cases map precisely; pytest/Node and nested-project coverage remain unclaimed; mixed runner inventory cannot create a partial green full run |
| Portable installation | Extracted archive bootstraps from another working directory; installed Codex skill bootstraps a second project; both agent directories retain required assets |
| Coordinates | AST ranges and actual Python comment anchors resolve; string examples are ignored; duplicate/missing bindings remain errors |
| Impact | Reverse dependency and provider/API traversal; sibling scope; every changed seed needs coverage; ignored source edits survive reindexing; Git rename/delete/untracked cases |
| Conservative policy | Critical capability inclusion; invalid/stale map fallback; source/revision/index mismatches and edited selection omissions fail |
| Cross-repo proof | Identical module/class/method names cannot credit an unexecuted provider test; an unmapped configured full-suite runner blocks proof |
| Execution | Real observed verbose cases pass; manual claims, unconditional success, zero collection, skipped/missing cases, and source mutations cannot establish green evidence |
| State | Exact JSON Pointer allowlists distinguish absent/null, JSON types, and array removal; unexpected mutations fail |
| Parity | Shared invariants require scoped per-instance tests; variances require reasons and tested alternate behavior |
| Distribution | Deterministic TAR/ZIP bytes; manifests match every file and archive; missing required assets fail packaging; caches/secrets excluded |
| Skills | All ten workflows routed; valid frontmatter and resolvable local links; evaluation scenarios explicitly unexecuted |

The [minimal Python example](examples/minimal-python/README.md) also passed `validate`, `index`, `navigate`, `parity`, full `impact`, `run`, and `gate`, with eight observed real unittest cases. Its allowed state diff passed; its unexpected owner mutation and missing read-only parity coverage correctly failed. Config, graph, index, selection, and result artifacts matched their Draft 2020-12 schemas in an additional local check using the environment's available `jsonschema` library; that library is not a runtime dependency.

The strict gate currently observes verbose unittest and pytest output. Other framework inventories and recipes require a trusted observer before they can pass it. Dependencies and remote services are not installed or exercised by these checks. Native case observations and local fingerprints are not signed remote attestation.

The 17 entries in `evals/evals.json` are declarative model-evaluation scenarios. They were not run as agent evaluations and are not included in the 46-test count. Generated fixture state, logs, and passing evidence are excluded from the distributions.
