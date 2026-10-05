---
name: testing-suite-map-system
description: >-
  Build or refresh the reviewed graph connecting product capabilities,
  implementation instances, workflows, source coordinates, data, dependencies,
  invariants, and tests. Use for discovery and bidirectional product/code tracing.
---

# Map a system

Read [graph conventions](../../protocols/GRAPH-CONVENTIONS.md). Inspect requirements,
source, and tests before adding relationships. Retain uncertainty explicitly;
neither a folder tree nor a language index is a complete behavior map.

## Build a traceable slice

1. Inventory repository roots and owners. Choose one user-visible capability,
   then list every implementation instance found in the inspected source:
   page, workflow, API, admin interface, or other surface.
2. Give each entity a stable ID, declared kind, useful name, and repository.
   Record the product/system context and attach implementation instances to
   capabilities with `implements` edges. Use `contains` for actual ownership.
3. For each instance, trace entry points through its page/workflow, UI, actions
   or events, functions and meaningful logical blocks. Record source paths,
   symbols or `@coord` anchors. Avoid mapping every line merely to create volume.
4. Follow data reads/writes and downstream providers across repository boundaries.
   Use consumer-to-provider edges; include the evidence for each relationship.
5. State the invariant in observable language, then link tests to what they
   cover. A file being named “test” is not proof that a behavior is asserted.
6. Declare parity groups and justified differences when multiple instances
   implement a shared invariant. Follow [instance-parity](../instance-parity/SKILL.md).

Work in `.testing-suite/graph.json`; consult the packaged schemas for permitted
fields and kinds. Prefer exact file/symbol references and a short evidence note
over vague “related to” edges. Mark unresolved dependencies in the report and
do not use an incomplete slice to justify narrow test selection.

## Resolve live coordinates

```sh
python3 .testing-suite/bin/suite.py --root . validate
python3 .testing-suite/bin/suite.py --root . index
python3 .testing-suite/bin/suite.py --root . navigate --id capability:notifications
python3 .testing-suite/bin/suite.py --root . navigate --query notifications
```

Example IDs are illustrative. Use actual graph IDs in project commands. In Python,
indexing resolves AST symbols and `@coord` comments. For other languages, comment
anchors and inspected paths provide a starting point; richer language indexing
requires an external adapter recipe, not a claim of built-in support.

An anchor such as `# @coord:notification-save` identifies a stable logical
location while line numbers move. An anchor should be unique within its declared
repository and match a graph node's `anchor`. Preserve IDs on rename or movement
when behavior identity survives. Remove ambiguous duplicates and re-index.

## Verify both directions

For a capability, identify its actual instances, code, data effects, dependencies,
invariants, and tests. For a source symbol or changed block, identify affected
instances and product behavior. Check that dependency and coverage directions
allow both traversals. Stop and repair dangling or unsupported edges.

Report the mapped scope, inspected repositories, evidence sources, unresolved
coordinates, uncovered invariants, and boundaries that remain uncertain. Never
describe generated inventory as a complete product map.
