---
name: testing-suite-run-evidence
description: >-
  Execute configured test runners, inspect required coverage and results, and
  establish source-bound verification evidence. Use for targeted/full test runs,
  CI gates, result recording, skipped cases, failures, or flaky retry reporting.
---

# Run tests and retain evidence

Read [evidence requirements](../../protocols/EVIDENCE.md) and
[selection safety](../../protocols/SELECTION-SAFETY.md). A green result means all
required scope was executed successfully against the reported source; it does
not mean that every product behavior has been modeled or proven.

## Establish exact scope

1. Inspect `.testing-suite/config.json` runner commands and working directories.
   Running configured commands executes project code. Use the user's existing
   authorization to test the project; inspect unfamiliar commands before use.
2. Validate and index the current source. Select from the complete baseline diff
   or request a full run. Read the selection reasons and required test IDs.
3. Confirm every required test maps to an actual runner. Inspect changed test
   discovery settings and disabled/skipped cases. Fix missing discoverability
   or report the gap before presenting results as complete.

## Supported case observations

Strict v0.1 evidence supports verbose native **unittest** and **pytest** output.
The optional config runner `adapter` is `unittest` or `pytest`; recognizable native
commands can also select the observer. Example runner entries are:

```json
{"id":"python-unit","adapter":"unittest","command":["python3","-m","unittest","discover","-s","tests","-v"]}
```

```json
{"id":"python-pytest","adapter":"pytest","command":["python3","-m","pytest","-v"]}
```

Adapt these to the project's real discovery scope. Ensure pytest `addopts` or
environment options do not suppress verbose case output; preserve intentional
project discovery and other settings while adjusting reporting. Map graph tests
to inspected `path` and qualified `symbol`, such as `PreferenceTests.test_save`.
Prefer individual case symbols over file-only coverage claims.

The unittest observer requires a positive `Ran N tests` summary and individual
module/class/method outcomes. The pytest observer reads `file.py::Class::case`
outcomes and checks zero-collection signals. Strict gating requires both a
successful process and observed passing matches for every selected graph test.
Zero tests, nonverbose/missing observations, absent required cases, skipped
required cases, and unrecognized runner adapters remain unverified. Native Node,
Playwright, and other runner commands can execute and retain logs, but need a
future trusted observation adapter before passing the strict gate. Setting
`adapter` to a known name does not make incompatible output trustworthy.

```sh
python3 .testing-suite/bin/suite.py --root . validate
python3 .testing-suite/bin/suite.py --root . index
python3 .testing-suite/bin/suite.py --root . impact --base HEAD --output .testing-suite/state/selection.json
python3 .testing-suite/bin/suite.py --root . run --selection .testing-suite/state/selection.json
python3 .testing-suite/bin/suite.py --root . gate --selection .testing-suite/state/selection.json
```

For full scope, replace the impact invocation with `impact --full --output
.testing-suite/state/selection.json`. v0.1 runs the configured suites needed by
selected tests and retains command output, exit codes, and supported observed
cases. It does not generate framework selectors or parse every framework report.
Configured commands remain the trusted collection boundary: inspect their scope
and output, and do not claim semantic correctness merely from matching case IDs.

## Interpret outcomes honestly

- Check runner logs, required test IDs, gate result, and the exact commit/source,
  graph, config, index, and selection hashes. Keep source changes after execution
  from inheriting the old green result; regenerate selection and rerun as needed.
- A failure, missing test result, skipped required case, stale provenance, empty
  executable suite, or runner that could not start is not a passing gate.
- Preserve first failure and each retry's scope and output. If a retry passes,
  report the earlier failure and investigate likely nondeterminism. Never replace
  flaky history with an unqualified “passed.”
- Avoid repeated broad testing after appropriate checks pass unless new changes,
  failures, stale evidence, or an unresolved concern justify it. Periodic full
  runs and release policies still apply.

## Record outside results

Manual records help retain external observations, but cannot masquerade as
runtime-verified evidence:

```sh
python3 .testing-suite/bin/suite.py --root . record --results .testing-suite/state/external-results.json --selection .testing-suite/state/selection.json
python3 .testing-suite/bin/suite.py --root . record --test test:notification-save --status failed --selection .testing-suite/state/selection.json
```

Use the documented result shape in the evidence protocol. `record` identifies
these results as manual; the strict gate requires runner evidence. External
framework/reporting integrations need a reviewed adapter and provenance checks
before they can become trusted automation. Do not set statuses from prose,
guess execution from authored code, or hand-edit runtime evidence to green.

Return the exact verified scope and revision, runner commands, required/passed/
failed/skipped counts where available, gate result, artifacts, and any limits.
State which supported cases were observed and when only runner logs are available.
Do not claim unsupported per-case verification or product semantics that the
runtime did not establish.
