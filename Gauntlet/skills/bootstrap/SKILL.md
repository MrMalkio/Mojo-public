---
name: testing-suite-bootstrap
description: >-
  Install the testing suite into a new or existing project while preserving its
  files and conventions. Use for project initialization, suite adoption, agent
  skill installation, profile selection, or CI scaffold requests.
---

# Bootstrap a project

Create a usable starting point, inspect what was discovered, then establish the
first real mapping and evidence. The scaffold is inventory, not a certificate of
test coverage.

## Inspect and preview

1. Read the project's instructions and identify repository roots, supported
   runtimes, package manager, existing test commands, CI files, and test data
   practices. Preserve the user's conventions.
2. Locate this package's `scripts/bootstrap.py`. Do not assume that the project
   already contains the copied runtime.
3. Preview the exact plan:

   ```sh
   python3 /path/to/Gauntlet/scripts/bootstrap.py --project /path/to/project --profile auto --agent both --dry-run
   ```

4. Review detected runners and unmapped test files. `auto` uses manifest evidence;
   it does not install packages, run tests, or invent behavior. Use `python`,
   `node`, or `generic` when project scope calls for an explicit profile.
   `generic` gives a graph and inventory without assuming an executable runner.

## Apply and verify

Run the same command without `--dry-run`; include `--ci` when CI scaffolding is
requested:

```sh
python3 /path/to/Gauntlet/scripts/bootstrap.py --project /path/to/project --profile auto --agent both --ci
cd /path/to/project
python3 .testing-suite/bin/suite.py --root . validate
python3 .testing-suite/bin/suite.py --root . index
```

The bootstrapper writes `.testing-suite/config.json`, `graph.json`, runtime files
under `bin/`, supporting documentation, agent guidance, a manifest, and optional
CI scaffolding. Runtime state belongs under `.testing-suite/state/` and is ignored
by version control. Agent options are `codex`, `claude`, `both`, and `none`;
requested skills are copied to `.agents/skills/testing-suite` and/or
`.claude/skills/testing-suite`. Existing `AGENTS.md` and `CLAUDE.md` are preserved;
read `.testing-suite/agent-instructions.md` before incorporating its guidance into
existing instructions if useful.

Bootstrap preflights managed files. Identical reruns are safe; differing existing
managed content blocks the write rather than overwriting user work. Resolve a
conflict by reading both versions and adapting the project deliberately. Do not
delete existing tests, instructions, manifests, or CI files to bypass a conflict.

## Make the result usable

- Read the generated config. Confirm each `runners` entry's command exists in
  the project and uses its established package manager. Python discovery can
  inventory declared pytest or existing Node scripts. Inferred stdlib unittest
  coverage uses inspected `TestCase.test_method` symbols and exact-file verbose
  runners with `adapter: "unittest"`. Pytest and Node inventories remain unbound
  until actual collection and test-to-runner mappings are reviewed. A discovered
  command still needs a real execution.
- Follow [map-system](../map-system/SKILL.md) to add capabilities, instances,
  invariants, dependency edges, and test coverage from inspected source.
- Follow [run-evidence](../run-evidence/SKILL.md) for a full baseline run. If no
  runner or mapped tests exist, report the specific missing setup instead of
  claiming a passing baseline.
- Strict observation currently supports verbose unittest and pytest only.
  Configure the optional runner `adapter` as `unittest` or `pytest`, enable native
  `-v` case output, and verify mapped path/symbol matches. Node/unknown runners
  can execute and retain logs but cannot pass the strict gate until a trusted
  observer is implemented. Keep those coverage gaps visible.
- Verify optional CI executes from the intended project root and can install
  dependencies through existing project steps. Scaffold presence alone does not
  demonstrate a passing remote job. Bootstrap enables execution only for a
  complete mapped inventory in which every configured runner owns mapped tests;
  mixed unverified runner inventories must not yield partial green CI.

Return the installed paths, detected runners, preservation/conflict outcome,
validation result, and concrete remaining mapping or execution gaps. Use the
fictional example only as a demonstration; never label its mapping as belonging
to the user's production system.
