# Conservative test selection

Targeted execution is an optimization justified by a current, reviewed map.
Uncertainty widens scope. A full configured run still cannot verify behavior that
has no meaningful executable test; retain coverage gaps separately.

## Selection procedure

1. Choose the baseline for the entire intended change. Include committed branch
   changes, tracked working-tree changes, and relevant untracked files. `HEAD`
   compares local uncommitted work; a branch review usually needs its merge-base.
2. Validate the graph/config and index current source against that baseline.
   Inspect index errors and unresolved coordinates before narrowing scope.
3. Seed impact from all changed files/nodes. Trace changed providers backward to
   their consumers and trace source back to the affected capabilities/instances.
   Include tests covering reached invariants, instances, and source.
4. Add all known failing, new, and critical tests regardless of apparent local
   impact. Newly introduced coverage must not be excluded because it has no
   historical result.
5. Read the selection's reasons, `test_reasons`, `selected_tests`, mode, confidence,
   and provenance. Confirm all tests are executable by configured runners.
6. Run the required configured suites and gate against that exact selection.
   Regenerate selection and evidence if source, config, graph, index, or scope
   changes before completion.

## Widen to full scope

Require a full configured run for any of these conditions:

- Missing index, stale hashes/repository revision, unresolved required coordinate,
  ambiguous anchor, graph/config validation failure, or uncertain mapping.
- Changed file/node outside the map or a dependency boundary whose impact cannot
  be established, including unavailable repositories needed for compatibility.
- Project/test configuration, manifest, dependency lockfile, or runner changes.
- The full-run cadence is due or the task explicitly requests full verification.

Index repair is useful, but it does not make missing product relationships known.
Do not create speculative edges merely to restore targeted mode. If full scope
is empty or a required runner/test is absent, report incomplete verification.

## v0.1 execution scope

The selection identifies graph test IDs. `run` invokes all configured runner
suites needed by those IDs; v0.1 does not synthesize Jest/pytest/Playwright filters
or implement Nx/Testmon affected-test algorithms. Full scope includes the
configured suites. Inspect the actual runner command and output because a runner
can return success without discovering every expected framework case.
The strict gate observes verbose unittest/pytest cases and requires matching
path/symbol evidence; unknown/nonverbose runners and zero-test runs cannot pass.
Node runner inventory or external affected-test selection does not provide that
observation adapter.

Use external affected-test tools as supporting evidence, with their own current
dependency models. Do not trust a cached subset when the graph is stale, a lockfile
changed, or required critical/new/failing tests are omitted.

## Gate interpretation

All required scope must pass against matching provenance. Failed, skipped,
missing, unexecuted, manually asserted, or stale results are not green. Never
change the selection to remove a failure without a reviewed scope correction.
Keep first-failure and retry evidence. A passing retry may resolve a transient
execution problem but does not erase a flaky observation.

Explain why selection was targeted or full, which behaviors/instances it covered,
and which boundaries remain unknown. Make no claim of product-wide correctness
from the selector's mode or confidence label alone.
