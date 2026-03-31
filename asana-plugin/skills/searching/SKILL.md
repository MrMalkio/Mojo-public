---
name: asana-searching
description: |
  All Asana task and project search operations. Use whenever you need to find tasks by stage,
  assignee, project, date, text, or any combination. Includes predefined filtered views for
  common patterns: Addressing tasks, Focus tasks, blocked tasks, triage batches, user tasks,
  project views, and orphan tasks. Always enforce filters — never run unbounded searches.
  Trigger this skill when looking up tasks, checking what someone is working on, finding
  what's blocked, triaging Unsorted, or doing any project-level task scan.
---

# Asana — Searching

**Primary tool:** `asana_search_tasks` (workspace-scoped, 40+ filters)
**Fast name lookup:** `asana_typeahead_search` (text-only, no field filters — use first when you know the name)
**Project task list:** `asana_get_tasks` (project/section/user_task_list/tag scoped)
**UI preview:** `search_tasks_preview` (Cowork UI only — renders results visually, do not use for agent logic)

---

## The Golden Rule

**Always pass at least one meaningful filter beyond workspace.** Never call `asana_search_tasks` with only `workspace` set. Unbounded searches destroy context windows and return noise. If you genuinely need everything for a person/project, see `tasks-all` below and read its gate.

Prefer `opt_fields` to limit what comes back. Default fields include names and GIDs. Add only what you need: `due_on`, `assignee`, `custom_fields`, `memberships`, `completed`.

---

## Predefined Search Variants

### 1. My Addressing Tasks (most common daily pattern)
```
asana_search_tasks({
  workspace: "9526911872029",
  assignee_any: "me",
  custom_fields: { "1189628845814528": "{Addressing_option_gid}" },
  completed: false,
  sort_by: "due_date",
  sort_ascending: true,
  opt_fields: "name,gid,due_on,custom_fields,assignee,memberships"
})
```
This is the starting point of every agent's day. If empty → cascade to Focus (see below).

### 2. My Focus Tasks
```
asana_search_tasks({
  workspace: "9526911872029",
  assignee_any: "me",
  custom_fields: { "1189628845814528": "{Focus_option_gid}" },
  completed: false,
  sort_by: "due_date",
  sort_ascending: true
})
```
Check eligibility before pulling to Addressing: DoD Status = Ready, no active blockers.

### 3. My Blocked Tasks
```
asana_search_tasks({
  workspace: "9526911872029",
  assignee_any: "me",
  custom_fields: { "1189628845814528": "{Roadblocked_option_gid}" },
  completed: false
})
```
Review these first. A newly unblocked task should move back to its prior stage immediately.

### 4. Another User's Tasks (by stage)
```
asana_search_tasks({
  workspace: "9526911872029",
  assignee_any: "{user_gid}",
  custom_fields: { "1189628845814528": "{stage_option_gid}" },
  completed: false,
  opt_fields: "name,gid,due_on,custom_fields,assignee"
})
```
Substitute "me" with the user's GID. Always specify stage unless doing a deliberate full review.
Use Owner/Driver fields as secondary signal for who to contact — not just the assignee.

### 5. Project — Tasks by Stage (maintainer/PM view)
```
asana_search_tasks({
  workspace: "9526911872029",
  projects_any: "{project_gid}",
  custom_fields: { "1189628845814528": "{stage_option_gid}" },
  completed: false,
  sort_by: "due_date",
  opt_fields: "name,gid,due_on,custom_fields,assignee,memberships"
})
```
Run once per stage you care about. Don't pull all stages in one call unless you're doing a full health check.

### 6. Triage Batch (Unsorted)
```
asana_search_tasks({
  workspace: "9526911872029",
  projects_any: "{project_gid}",
  custom_fields: { "1189628845814528": "{Unsorted_option_gid}" },
  completed: false,
  limit: 10,
  sort_by: "created_at",
  sort_ascending: true
})
```
Pull in small batches of 10. Oldest first — don't let things rot. After processing each batch, check if Addressing is now empty and cascade if needed.

### 7. Cascade Check (Addressing empty → pull from Focus)
When Addressing is empty for a project:
1. Run variant #5 for Focus on that project
2. For each task: check `is_blocked` = false AND DoD Status = Ready ✔
3. Eligible tasks → propose or auto-advance to Addressing (pass Focus→Addressing gate first)
4. If Focus is also empty → run variant #5 for Todo, advance eligible tasks to Focus

### 8. Orphan Tasks ("Find Orphans" / "Where's Timmy")
```
asana_search_tasks({
  workspace: "9526911872029",
  assignee_any: "{user_gid or 'me'}",
  completed: false
})
```
Then filter results client-side for tasks where `memberships` array is empty. These are tasks not in any project. Note: may be intentionally private — don't assume they're lost, just surface them.

### 9. All Tasks (gated)
```
asana_search_tasks({
  workspace: "9526911872029",
  assignee_any: "{target}",   // OR projects_any, not both unless intentional
  completed: false,
  // MUST include at least one of: due_on_before/after, modified_on_after, created_on_after
})
```
**Gate:** Only run this if you have a specific, articulable reason why a stage or date filter would miss something you need. State the reason before calling. Never omit all filters.

---

## Fast Lookup (Typeahead)

Use `asana_typeahead_search` when you know the name of what you're looking for:
```
asana_typeahead_search({
  workspace_gid: "9526911872029",
  resource_type: "task",   // task | project | user | team | tag | portfolio | goal
  query: "the task name",
  count: 5
})
```
Fastest option. Returns top matches by recency and usage. If multiple results look similar, ask the user to confirm before proceeding.

---

## Project Task List (by section)

When you already know the project and section GIDs, bypass search entirely:
```
asana_get_tasks({
  project: "{project_gid}",
  section: "{section_gid}",    // optional — omit for full project
  assignee: "me",               // optional
  completed_since: "now",       // only incomplete tasks
  opt_fields: "name,gid,due_on,assignee,custom_fields"
})
```
This is more efficient than `search_tasks` when you already know the project. Use section GIDs from `index/PROJECTS.md` to avoid a lookup.

---

## opt_fields Reference

Only request what you need:
- **Minimal:** `name,gid`
- **Routing:** `name,gid,assignee,custom_fields,memberships`
- **Scheduling:** `name,gid,due_on,start_on,due_at,start_at`
- **Full context:** `name,gid,due_on,start_on,assignee,custom_fields,memberships,notes,parent,num_subtasks`

Never request `notes` or `html_notes` in bulk search — read description only after targeting a specific task.
