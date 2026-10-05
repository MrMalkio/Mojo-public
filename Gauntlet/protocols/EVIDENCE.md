# Execution evidence

Passing evidence belongs to an actual execution of the required scope against
the reported source. Prose, generated test code, graph status fields, validated
declarations, and manually entered statuses cannot establish a runner-verified
gate.

## Provenance

Retain these runtime fields with the execution:

| Evidence | Meaning |
|---|---|
| `head`, `heads` | Root and declared repository revisions, where available |
| `source_hash` | Current indexed source, including working-tree state |
| `graph_hash`, `config_hash`, `index_hash` | Exact model, runner setup, and coordinates |
| `selection_hash`, `mode` | Exact required selection and full/targeted scope |
| `generated_at`, `provenance_valid` | Observation time and provenance validity |
| `evidence` | `runner` or `manual` origin |
| `results`, `runners` | Declared test outcomes and actual runner executions |
| Runner `adapter`, `observed_count`, `observed_tests`, `verified` | Supported observer, positive collection, case outcomes, and observation validity |

See [results schema](../schemas/results.schema.json) and
[selection schema](../schemas/selection.schema.json). Runtime state is generated;
do not hand-edit hashes, origin, validity, or result statuses to bypass the gate.
Capture all declared repository revisions for cross-repository work. If a repo
cannot be resolved, report that limit instead of substituting the root revision.

## Execute and inspect

Use `run --selection FILE` after reviewing commands. Runtime runner entries retain
command argument arrays, timestamps, exit code, status, and output artifact paths.
Check output for discovery, skipped cases, unexpected failures, and suppressed
errors; an exit code alone cannot prove every expected framework case ran.

v0.1 parses verbose native unittest and pytest output. Config runner `adapter`
may be `unittest` or `pytest`; recognized native commands can infer that observer.
Use native `-v` commands, such as `python3 -m unittest discover -s tests -v` or
`python3 -m pytest -v`, with the project's real discovery scope. Ensure quiet
pytest configuration/environment options do not suppress individual outcomes.
Preserve intentional project settings while adjusting reporting.

Unittest requires a positive `Ran N tests` summary and individual module/class/
method statuses. Pytest observes `file.py::Class::case` statuses and zero-collection
signals. A selected graph test must have a `path` and preferably a qualified
`symbol` matching observed passing cases. Prefer individual case nodes; a file-only
node is a broader claim and should be reviewed against actual discovery.
Required skipped/XFAIL outcomes cannot pass; XPASS is not treated as a clean pass.

The strict gate requires successful commands, valid supported observations,
positive collection, and matching passes for every required graph test. Zero
tests, nonverbose output, unknown adapters, absent cases, skipped required cases,
or source mismatch remain unverified. Node/Jest/Playwright/Pact and other runner
commands can be inventoried and executed with logs, but need a future trusted
observation adapter to satisfy this gate. A manual record cannot substitute.

Commands remain the trusted collection boundary; matching case identities does
not prove semantic coverage or equivalence to every possible framework report.
Inspect assertions, scope, and logs. Use framework artifacts for additional retry,
discovery, and per-case detail. Unconditional success or simulated report output
does not constitute a meaningful test execution.

The gate compares required selection, actual outcomes, and provenance. Every
required test needs passing evidence. Failed, missing, skipped, or stale evidence
fails completion. A zero-test scaffold is incomplete even when its JSON validates.

## Manual observations and external artifacts

`record --results FILE --selection FILE` or the single-test record form retains
outside observations as `manual`. The strict gate does not promote them to
runner execution. The imported file is a JSON array such as
`[{"id":"test:notification-save","status":"failed"}]`, or an object with that
array under `results`. IDs must belong to the exact supplied selection and
statuses are `passed`, `failed`, or `skipped`. Do not manufacture the complete
runner-provenance envelope yourself. Artifact filenames must be relative to the
project root; place temporary records and snapshots in `.testing-suite/state/`.

External test/reporting tools can retain more detailed results. A future trusted
adapter must validate source revision, graph/selection scope, executed test IDs,
artifact identity, failures/skips, and runner authenticity before gate use.
Listing a tool in this package is not implementation of that adapter.

## Failure and retry history

Preserve the first failing command, output, fixture/seed, source revision, and
selection. Retain every retry separately, including any scope or environment
change. A later pass is reported alongside the earlier failure. Investigate flaky
behavior rather than discarding failed artifacts or replacing statuses silently.

Store only synthetic or approved sanitized fixture data. Keep secrets and personal
data out of logs, snapshots, reports, and checked-in fixtures. Redact sensitive
values before presenting artifacts while preserving enough structure to diagnose
the issue. Artifact retention follows project conventions and the task's needs.

## Report the verified result

State exact revision and working-tree scope, baseline, affected behavior/instances,
required runners/test IDs, command outcomes, gate result, and artifact locations.
Provide per-case counts only when available from inspected framework evidence.
Name skipped/missing tests, unknown coverage, external boundaries, or environment
limits. Keep historical observations separate from current verification.
