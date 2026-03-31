---
name: asana-maintenance
description: |
  Maintain and update the Asana plugin reference files — projects index, fields index,
  options files, players index, and skill files. Run full-refresh at install time and
  whenever workspace changes are detected. Run targeted updates when specific indexes
  go stale. Also covers workspace hygiene (stale tasks, violations, orphans) and
  keeping agent CONTRIBUTIONS.md current. Trigger when reference data seems outdated,
  when encountering unknown field or project GIDs, or when doing periodic workspace audits.
---

# Asana — Maintenance

**Tools:** `asana_get_projects_for_workspace`, `asana_get_project_sections`, `asana_get_workspace_users`, `asana_get_project`, `asana_search_tasks`

---

## Full Refresh (`full-refresh`)

Run at install time and on periodic audit. Pulls everything needed to fully populate the reference files.

```
Steps:
1. update-projects-index (see below)
2. update-fields-index
3. update-players-index
4. update-sections-index (per project)
5. Verify OPTIONS files are current for each primary project
6. Post completion status to agent log project
```

---

## `update-projects-index`

Trigger: new project detected, project archived, section structure changed.

```
asana_get_projects_for_workspace({
  workspace_gid: "9526911872029",
  archived: false,
  opt_fields: "name,gid,owner,team"
})
// For each project, get sections:
asana_get_project_sections({ project_id: "{gid}" })
```

Write results to `index/PROJECTS.md`. Format:
```
| Project Name | GID | Purpose | Sections |
```

---

## `update-fields-index`

Trigger: unknown field GID encountered in an error, new custom field detected on a project, periodic refresh.

```
// Get project with its custom field settings
asana_get_project({
  project_id: "{gid}",
  opt_fields: "custom_field_settings,custom_field_settings.custom_field,custom_field_settings.custom_field.name,custom_field_settings.custom_field.gid,custom_field_settings.custom_field.type,custom_field_settings.custom_field.enum_options"
})
```

Write field GIDs, types, and option GIDs to `index/FIELDS.md` and the appropriate `index/options/OPTIONS-[project].md`.

**Note:** Cannot add custom fields to projects via MCP. If a field is missing from a project, create a `[FIX]` task for Caspera or workspace admin to add it via the Asana UI.

---

## `update-players-index`

Trigger: unknown user GID, new team member, agent added to workspace.

```
asana_get_workspace_users({
  workspace: "9526911872029",
  opt_fields: "name,gid,email"
})
```

Write to `index/PLAYERS.md`. Players includes humans (internal/external) and agents. Format:
```
| Name | GID | Type (human/agent) | Role | Escalation | Notes |
```

Note: `index/PLAYERS.md` is the renamed evolution of `PEOPLE.md` — aligns with the Anasa "Players" concept which covers all participants regardless of type.

---

## `workspace-hygiene`

Run on demand or periodically. Finds and flags violations.

**What to look for:**

1. **Tasks in Focus without DoD = Ready** → move back to Todo, comment why
2. **Tasks in Addressing without a recent update** → flag for `micro-update-check`
3. **Tasks in Resolved with incomplete subtasks** → revert to Addressing, comment
4. **Orphaned tasks (no project membership)** → surface to task owner
5. **Unsorted tasks older than 7 days** → escalate for triage
6. **Tasks with no assignee or driver in Addressing** → flag for assignment

For each violation: fix it, post a comment explaining what was corrected and why. Don't silently change things.

```
// Example: find Focus tasks without DoD Ready
asana_search_tasks({
  workspace: "9526911872029",
  projects_any: "{project_gid}",
  custom_fields: {
    "1189628845814528": "{Focus_option_gid}",
    "1210940116708566": "{DoD_not_ready_option_gid}"
  },
  completed: false
})
```

---

## `update-skill`

When a new MCP tool is discovered, an API change is detected, or a known error pattern is found:
1. Identify which skill file(s) are affected
2. Update the relevant SKILL.md file(s)
3. Post a note in `MAINTENANCE.md` with what changed and why
4. If the change affects the test matrix, update `TEST-MATRIX.md`

---

## `update-contributions`

Run at session end as part of `agent-session-end` combo. Updates:
- Active/Blocking Tasks list in CONTRIBUTIONS.md (Addressing + Roadblocked for this agent)
- Waiting tasks list
- Sprint context block if sprint changed

---

## Maintenance Catalog

| Artifact | Update trigger | Maintainer |
|----------|---------------|------------|
| `index/PROJECTS.md` | New project, archive, section added | Caspera on detection |
| `index/FIELDS.md` | New field, field deprecated, unknown GID error | Caspera after API check |
| `index/options/OPTIONS-*.md` | Option added/renamed/deprecated | Caspera after API check |
| `index/PLAYERS.md` | New user, new agent, role change | Caspera on detection |
| `protocols/PROGRESS-FUNNEL.md` | Stage gate rules change | Malkio approval required |
| `skills/*.md` | New MCP tool, API change, known error pattern | Caspera |
| `agent/CONTRIBUTIONS.md` | Session end, sprint change, PAT rotation | Agent auto-refresh |
| `TEST-MATRIX.md` | New unknown discovered, test completed | Agent during/after testing |
