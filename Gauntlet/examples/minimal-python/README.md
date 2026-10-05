# Runnable synthetic review fixture

This stdlib-only example implements one review capability on an editable toggle
and a read-only summary. The read-only surface deliberately refuses writes.
Everything here is synthetic; it makes no claims about a production repository.
The graph maps exact methods, stable `@coord` anchors, eight real test cases,
shared invariants, and a tested permission variance. Initial test evidence is
unknown until execution.

From this directory, run:

```sh
python3 -m unittest discover -s tests -v
python3 ../../scripts/suite.py --root . validate
python3 ../../scripts/suite.py --root . index
python3 ../../scripts/suite.py --root . parity
python3 ../../scripts/suite.py --root . navigate --id function:editable-toggle
python3 ../../scripts/suite.py --root . impact --full --output .testing-suite/state/selection.json
python3 ../../scripts/suite.py --root . run --selection .testing-suite/state/selection.json
python3 ../../scripts/suite.py --root . gate --selection .testing-suite/state/selection.json
```

No installation or dependency download is required. The existing graph is
already mapped; bootstrap is for a fresh project and will preserve this graph by
reporting a collision if its generated inventory differs.

`EditableReviewTests.test_toggle_changes_only_reviewed_field` executes the action
and asserts the exact expected new state. The supplied state-diff inputs are
explicit synthetic examples, not captured execution evidence:

```sh
python3 ../../scripts/suite.py --root . state-diff --before inputs/state-before.json --after inputs/state-after-allowed.json --allowlist inputs/allowed-pointers.json
python3 ../../scripts/suite.py --root . state-diff --before inputs/state-before.json --after inputs/state-after-unexpected.json --allowlist inputs/allowed-pointers.json
```

The first comparison permits only `/r1/reviewed`. The second exits unsuccessfully
because `/r1/owner` also changes. Permitted changes alone do not prove required
behavior; the real unit test supplies that assertion.

The mapped graph's parity check succeeds because each instance has a scoped
review-display test and the read-only update variance has its own refusal test.
`inputs/parity-missing-coverage.json` is a complete negative graph that removes
one read-only display coverage edge. To exercise the missing-coverage control,
copy this fixture to a temporary directory, replace the copy's
`.testing-suite/graph.json` with that input, and run the original package's
`scripts/suite.py --root /absolute/path/to/the/copy parity`. It must report the
uncovered `(instance:readonly, invariant:display)` cell. Parity checks declarations;
the executed tests establish the behavior.

Local `.testing-suite/state/` and `__pycache__/` are ignored. No passing run state
is shipped. Editing source, graph, test declarations or anchors requires re-indexing
and fresh execution before the gate can pass again.
