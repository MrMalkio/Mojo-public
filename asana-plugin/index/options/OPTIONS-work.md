---
name: asana-options-work
description: |
  Field option GIDs for D&S Daily Tasks project (1209978806020366).
  Load when creating or updating tasks on the Daily Tasks board.
  Includes all core fields plus Daily Tasks-specific: Tasks Category, Transcript Link.
---

# OPTIONS — D&S Daily Tasks (`1209978806020366`)

Inherits all core fields from OPTIONS-core.md. Additional project-specific fields below.

---

## Tasks Category — `1209980251972651`
| Category | GID |
|----------|-----|
| D&S | `1209980251972654` |
| D&S - Client | `1211806924682955` |
| OPDM | `1209980251972655` |
| OPDM Dev | `1211806924682956` |
| Boomerang | `1209980251972656` |
| STR | `1209980251972657` |
| Comms | `1210438381781135` |
| All | `1210915963933024` |
| AR | `1211880289464058` |
| AP | `1211880289464059` |

## Transcript Link — `1209994721938666`
Text field. No options. Set to URL of session transcript if task was created by an agent.

---

## Section GIDs
Run `asana_get_project_sections(project_id="1209978806020366")` to get current section GIDs — sections change more frequently than fields.
