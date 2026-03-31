---
name: asana-fields-index
description: |
  Master reference for all workspace-level custom field GIDs, types, and descriptions.
  Load as fallback when project OPTIONS file is unavailable. For specific option GIDs
  per project, load index/options/OPTIONS-{project}.md instead — faster and scoped.
  Last refreshed: 2026-03-31 by Cirra via T10 (asana_get_project + custom_field_settings).
---

# Fields Index

Workspace GID: `9526911872029`

---

## Core Progress Funnel Fields (Memorize These)

These appear on virtually every active project. GIDs are workspace-level and stable.

| Field | GID | Type | Purpose |
|-------|-----|------|---------|
| Stage | `1189628845814528` | enum | Progress funnel position. Single source of truth. |
| Priority | `1103808807953314` | enum | Q-rank score (Q1–Q4 with numeric weight). |
| DoD Status | `1210940116708566` | enum | Definition of Done gate. Blocks Addressing entry. |
| Update Status | `1210940175173699` | enum | Staleness flag. Flip to ping assignee/followers. |
| Driver | `1210780889704728` | people | Person executing work. Set before assignee. |
| Owner | `1210780803968113` | people | Person accountable for outcome. |
| Time Est | `1210940166437340` | text | Hour estimate before work starts. |
| Time Spent | `1210940333553164` | number | Rolling effort log. |
| Deadline Band | `1210940190130576` | enum | SLA category (Same day / 24h / 48h / 72h / 5d / 1wk). |

---

## Stage Field Options

Field GID: `1189628845814528`

| Option | GID | Color |
|--------|-----|-------|
| Unsorted | `1189628845815554` | cool-gray |
| Todo | `1189628845815620` | orange |
| Focus | `1189628845880136` | yellow-orange |
| Addressing | `1189628845880138` | yellow-green |
| Resolved | `1189628845880139` | green |
| Roadblocked | `1211591968992295` | red |

---

## Priority Field Options (Q-rank)

Field GID: `1103808807953314`

| Option | GID | Quadrant |
|--------|-----|----------|
| 10 - Q1 Urgent & Important - 10 | `1103808807953315` | Q1 |
| 09 - Q1 Urgent & Important - 5 | `1131782234280223` | Q1 |
| 08 - Q1 Urgent & Important - 3 | `1131782234280224` | Q1 |
| 07 - Q1 Urgent & Important - 1 | `1131782234280225` | Q1 |
| 06 - Q2 Important/Not Urgent - 10 | `1103808807953316` | Q2 |
| 05 - Q2 Important/Not Urgent - 5 | `1131782234280226` | Q2 |
| 04 - Q2 Important/Not Urgent - 3 | `1131782234280227` | Q2 |
| 03 - Q2 Important/Not Urgent - 1 | `1131782234280228` | Q2 |
| 02 - Q3 Urgent/Not Important | `1103808807953317` | Q3 |
| 01 - Q4 Not Urgent or Important | `1103808807953318` | Q4 |
| 0 - Unsure | `1103808807953319` | — |
| 0 - Backlog | `1107824218019856` | — |

---

## DoD Status Field Options

Field GID: `1210940116708566`

| Option | GID |
|--------|-----|
| Ready ✔ | `1210940116708569` |
| Not Ready | `1210940116708570` |

---

## Update Status Field Options

Field GID: `1210940175173699`

| Option | GID |
|--------|-----|
| Up-to-date | `1210940175173702` |
| ⚠ Needs update | `1210940175173703` |
| Not yet required | `1212850329788387` |

---

## Deadline Band Field Options

Field GID: `1210940190130576`

| Option | GID |
|--------|-----|
| Same day | `1211223873335011` |
| 24 h | `1210940190130579` |
| 48 h | `1210940190130580` |
| 72 h | `1210940190130581` |
| 5 days | `1210940190130582` |
| 1 week | `1210940190130583` |

---

## Project-Specific Fields

These appear only on certain projects. For full option lists, load the relevant OPTIONS file.

| Field | GID | Type | Projects |
|-------|-----|------|---------|
| Working Status | `1162095947772596` | enum | SS Dev, others |
| Feature Status | `1213246488752197` | enum | SS Dev |
| Component | `1213194483049635` | multi_enum | SS Dev |
| Type | `1213246488697421` | enum | SS Dev |
| Task weight | `1205390331390811` | enum | SS Dev, others |
| Reference link | `1188126729754775` | text | SS Dev, others |
| Branch | `1213731361063686` | text | SS Dev |
| Test link | `1213194483049629` | text | SS Dev |
| Tasks Category | `1209980251972651` | enum | D&S Daily Tasks |
| Transcript Link | `1209994721938666` | text | D&S Daily Tasks |

---

## Usage Notes

- Always use project-specific OPTIONS files when available — they include option GIDs scoped to the project context.
- This file is the fallback when no OPTIONS file exists for a project.
- Run `maintenance/update-fields-index` to refresh after any workspace field changes.
- Core funnel fields (Stage, Priority, DoD, Update Status, Driver, Owner) are workspace-level — available on all projects.
