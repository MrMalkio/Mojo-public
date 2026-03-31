---
name: asana-options-feature
description: |
  Field option GIDs for SteadyStars Development project (1213243591510417).
  Load when creating or updating tasks on SS Dev board.
  Includes all core fields plus SS Dev-specific: Feature Status, Component, Type,
  Working Status, Reference link, Branch, Test link.
---

# OPTIONS — SteadyStars Development (`1213243591510417`)

Inherits all core fields from OPTIONS-core.md. SS Dev-specific fields below.

---

## Working Status — `1162095947772596`
| Status | GID |
|--------|-----|
| Pending | `1208534086647239` |
| To do | `1162095947772597` |
| Doing | `1162095947772598` |
| Blocked | `1208534086647240` |
| On hold | `1202555796764656` |
| Reviewing | `1162095947772600` |
| At it again | `1162095947772601` |
| Done | `1162095947772599` |

## Feature Status — `1213246488752197`
| Status | GID |
|--------|-----|
| Considering | `1213246488752198` |
| Research and Planning | `1213246488752199` |
| Waiting | `1213246488752200` |
| In Development | `1213246488752201` |
| In Review | `1213246488752202` |
| Testing | `1213246488752203` |
| Live in Console B | `1213246488752204` |
| Active MVP | `1213246488752205` |
| Data Stored in Firebase | `1213246488752206` |
| Data Stored in Sheets | `1213246488752207` |
| Data Stored in Integromake | `1213246488752208` |
| Integromake managed | `1213246488752209` |
| Display Component | `1213246488752210` |
| Abandoned | `1213246488752211` |
| Backlogged | `1213246488752212` |

## Component — `1213194483049635` (multi_enum)
| Component | GID |
|-----------|-----|
| ss-Wizard | `1213580664393261` |
| ss-LBR | `1213731361063680` |
| ss-OwMa | `1213731361063681` |
| Zeus | `1213731361063682` |
| ss-staff-app | `1213731361063683` |
| Helm | `1213731361063684` |
| Hermes-DB | `1213731361063685` |
| Order Management | `1213194483049637` |
| Marketing | `1213194483049638` |
| Onboarding | `1213580664393262` |
| Boomerang | `1213194483049639` |
| Loyalty & Rewards | `1213194483049640` |
| User Profiles | `1213246488755743` |
| Notifications | `1213246488755744` |
| API Integration | `1213246488755745` |
| Reporting | `1213246488755746` |
| Backend Workflows | `1213246488755747` |
| Settings | `1213246488755748` |
| Dashboard | `1213194483049636` |
| Page (informational) | `1213246488755749` |
| Payload | `1213246488755750` |
| Data model (type/Table) | `1213246488755751` |
| Integration | `1213246488755752` |
| Modal | `1213246488755753` |
| Funnel | `1213592770561442` |

## Type — `1213246488697421`
| Type | GID |
|------|-----|
| Multi-Use Parent | `1213246488697422` |
| Form Input | `1213246488697423` |
| Wizard | `1213580664393267` |
| UI Element | `1213246488697424` |
| Dashboard | `1213246488697425` |
| Screen | `1213246488697426` |
| Section | `1213246488697427` |
| Access own user data | `1213246488697428` |
| Access customers data | `1213246488697429` |
| Access outlet data | `1213246488697430` |
| Access order data | `1213246488697431` |
| Update own user data | `1213246488697432` |
| Update outlet data | `1213246488697433` |
| Update order data | `1213246488697434` |
| Metrics | `1213246488697435` |
| Alert | `1213246488753548` |
| File Upload | `1213246488753549` |
| File Download | `1213246488753550` |
| Console Action | `1213246488753551` |
| Messaging | `1213246488753552` |
| Alternative Display Mechanism | `1213246488753553` |
| Bug | `1213246488753554` |

## Text Fields (no options)
| Field | GID | Use |
|-------|-----|-----|
| Reference link | `1188126729754775` | Figma / design / doc URL |
| Branch | `1213731361063686` | Git branch name |
| Test link | `1213194483049629` | URL to test/preview the feature |

---

## Section GIDs
Run `asana_get_project_sections(project_id="1213243591510417")` to get current section GIDs.
