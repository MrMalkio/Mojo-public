# Skill router

Read the [root skill](../SKILL.md) first. Each child skill has a scoped trigger,
workflow, commands, expected output, and links to shared protocols.

| Skill | Typical input | Concrete output |
|---|---|---|
| [bootstrap](bootstrap/SKILL.md) | Project path and adoption scope | Preserved project scaffold, runners, adoption gaps |
| [map-system](map-system/SKILL.md) | Product requirements and inspected code | Reviewed graph with bidirectional evidence |
| [plan-impact](plan-impact/SKILL.md) | Intended change and complete baseline | Impact plan and conservative selection |
| [design-tests](design-tests/SKILL.md) | Invariants, risks, missing coverage | Executable assertions and coverage mapping |
| [run-evidence](run-evidence/SKILL.md) | Current selection and configured runners | Source-bound execution artifacts and gate outcome |
| [contracts](contracts/SKILL.md) | Consumer/provider boundary | Contract mapping and compatibility evidence |
| [instance-parity](instance-parity/SKILL.md) | Capability with multiple instances | Tested invariant matrix and justified variances |
| [state-diff](state-diff/SKILL.md) | Isolated scenario and JSON snapshots | Unexpected changes and exact allowed pointers |
| [diagnose](diagnose/SKILL.md) | Failure and execution artifacts | Exact coordinates, confirmed cause, verified fix |
| [maintain](maintain/SKILL.md) | Changed project or requested audit | Refreshed mapping, full-run evidence, visible gaps |

The tools listed in [adapter recipes](../references/ADAPTERS.md) are external
ecosystem options. Their mention does not imply installation or live integration.
