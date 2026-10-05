# Graph and coordinate conventions

The reviewed graph is `.testing-suite/graph.json`; project and runner configuration
is `.testing-suite/config.json`. Generated index, selections, results, and command
artifacts live under `.testing-suite/state/`. Use the packaged JSON schemas and
runtime `validate` command together: structural validity does not prove that a
relationship matches the application.

## Entities and identity

Graph root fields are `schema_version: 1`, `nodes`, `edges`, and `parity_groups`.
Every node requires `id`, `kind`, and `name`. Add `repo` to establish ownership;
it is required for path-bound source nodes and must identify a configured
repository. IDs are unique, stable, nonempty strings without whitespace. A
readable convention is `kind:meaning`, but the schema does not require that prefix.

| Kind | Represents |
|---|---|
| `product`, `system`, `repository` | Product context, composed system, repository ownership |
| `capability`, `instance` | Behavior and one concrete implementation of it |
| `page`, `ui`, `action` | Page/workflow surface, UI element, action or event |
| `function`, `block`, `file` | Source function, meaningful logical block, file |
| `data`, `api`, `service`, `resource` | State and dependency boundaries |
| `invariant`, `test` | Observable requirement and executable verification |

Represent a workflow using its pages and actions; there is no separate `workflow`
kind in v1. An implementation instance can be a UI or API surface. Do not
conflate two instances because they happen to call the same function.

Optional source fields are `path`, `symbol`, and `anchor`; paths are relative to
the declared repository, and repositories are configured relative to the project
root. For multiple repositories, use a common checkout/workspace root containing
the configured repositories. v0.1 rejects absolute paths, `..` traversal, and
symlink paths; an unavailable external checkout remains a reported boundary.
Optional behavior/testing fields include `behavior`, `critical`, `new`,
`last_status`, `runner`, and `command`. Only actual observed execution may update
a status. A declared `last_status` affects conservative selection but does not
constitute current passing evidence. Runner IDs refer to config `runners` entries,
whose commands are argument arrays rather than shell strings. Optional runner
`adapter` is `unittest` or `pytest`; verbose native case output is required for
strict v0.1 observation. Node and other commands remain unverified until a trusted
observer exists. Prefer individual test nodes with current path/qualified symbol
over file-only coverage declarations.

## Relationships

Edges contain `source`, `target`, `relation`, and preferably `evidence` describing
the inspected requirement, source, schema, or assertion behind the relationship.
Both endpoints must exist.

| Relation | Direction |
|---|---|
| `contains` | Parent/container → child/member |
| `implements` | Implementation instance → capability |
| `depends_on`, `invokes`, `consumes` | Consumer/caller → provider/dependency |
| `reads`, `writes` | Reader/writer → data node |
| `provides` | Provider → offered API/resource |
| `covers`, `verifies` | Test → behavior, instance, invariant, or source it checks |

Prefer dependency edges to a mere shared folder when reasoning about impact.
Cross-repository providers remain nodes with repository ownership; preserve the
consumer-to-provider direction so changed providers can be traced back to
consumers. `contains` helps navigation but is not proof of an execution dependency.

For parity coverage, connect a test to its instance and the shared invariant it
asserts, directly or through the graph's supported coverage traversal. Inspect
the assertion before adding the edge. A mocked provider without checked behavior
must not receive a claim of verified compatibility.

## Stable coordinates and drift

Canonical source anchors are comments containing `@coord:<stable-id>`, for example:

```python
# @coord:notification-save
def save_preference(value):
    ...
```

```js
// @coord:notification-submit
```

The graph's `anchor` stores only the stable ID, such as `notification-save`.
Keep anchors unique within each declared repository. Use existing comments where
practical; the anchor is a locator and should not change application behavior.
For Python symbols use the indexed qualified symbol identity. When both symbol
and anchor are declared, check the resolver's output; do not assume they select
the same block without inspection.

The index records current path, start/end coordinates, file hash, source hash,
graph/config hash, and repository heads. Python AST positions and lexical comment
anchors are supported in v0.1. Other-language semantic references require an
external index recipe. Missing/ambiguous anchors, moved symbols, parse errors,
and mismatched provenance must remain visible. Do not hard-code permanent line
numbers or ignore stale coordinates to keep targeted mode working.

Preserve node identity across harmless renames and movement when its behavior
identity is unchanged. Re-index after edits; review relationship changes after
semantic changes. If identity actually changed, add a new node and update its
consumers, tests, and parity declaration deliberately.

## Parity declaration

Each group has `id`, `capability`, `instances`, `shared_invariants`, and optionally
`variances`. Each variance has `instance`, `invariant`, `reason`, and `test`.
References must identify existing nodes of the appropriate kinds. State why the
instance differs and verify the alternate behavior with the referenced test.
Declaration validation is distinct from execution evidence.
