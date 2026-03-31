---
name: anasa-context
version: "1.0.0"
description: |
  Workspace knowledge base for the D&S / GNGE Asana workspace. Provides player GIDs,
  project GIDs, field GIDs, and option GIDs without live API calls. Load at session
  start to eliminate cold-start overhead. Used by asana-plugin and any other skill
  that needs to reference workspace entities by GID.

  Trigger: whenever a GID lookup is needed for a player, project, field, or field option.
  Load automatically when asana-plugin is active.

  Future: this skill will be replaced by GET /agent-context from the Anasa API (see ANASA-PRD.md).
  File format is frozen — API response will be a superset, zero breaking changes.
---

# Anasa Context — Workspace Knowledge Base

**Workspace:** gnge.co (`9526911872029`)
**Last refreshed:** 2026-03-31
**Refresh method:** maintenance skill `full-refresh` or `anasa refresh-all` CLI (P1)

---

## Loading Guide

Load files on demand — not all at once. Loading order:

1. **Always available (memorized in asana-plugin/SKILL.md):** Stage, Priority, DoD, Update Status GIDs
2. **Load if player lookup needed:** `index/PLAYERS.md`
3. **Load if project routing needed:** `index/PROJECTS.md`
4. **Load for field operations (fallback):** `index/FIELDS.md`
5. **Load for specific project field ops:** `index/options/OPTIONS-{project}.md`

For most operations, options 1 + 5 are sufficient.

---

## Index Files

| File | Contents | Load when |
|------|----------|-----------|
| `index/PLAYERS.md` | All humans + agents, GIDs, emails, platforms | @mention, assign, route |
| `index/PROJECTS.md` | All projects, GIDs, ownership, purpose | Route task, search by project |
| `index/FIELDS.md` | All workspace field GIDs + option tables | Fallback when no OPTIONS file |
| `index/options/OPTIONS-core.md` | Stage, Priority, DoD, Update Status, Deadline Band, Weight | All projects |
| `index/options/OPTIONS-work.md` | D&S Daily Tasks project fields | Daily Tasks operations |
| `index/options/OPTIONS-feature.md` | SteadyStars Dev project fields | SS Dev operations |

---

## Refreshing This Data

Run via maintenance skill in asana-plugin:
```
Load asana-plugin/skills/maintenance/SKILL.md → run full-refresh
```

Or individually:
- `update-projects-index` → refreshes PROJECTS.md
- `update-fields-index` → refreshes FIELDS.md + OPTIONS files
- `update-players-index` → refreshes PLAYERS.md

Target refresh frequency: weekly or after any workspace structural change (new project, new field, new player).

---

## Anasa P1 Note

When Anasa API is live, replace this skill's file reads with:
```
GET https://anasa.duckandshark.com/agent-context?agent_gid={gid}
```
Response is a superset of all index file contents. File-based fallback remains available via `GET /snapshot?format=markdown`.
