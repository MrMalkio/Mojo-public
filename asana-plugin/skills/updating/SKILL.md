---
name: asana-updating
description: |
  Update existing Asana tasks — fields, stage transitions, assignee, dates, descriptions,
  completion, bulk updates. Use for any mutation of an existing task. Always run task-prep
  first. Covers single and batch updates (up to 50 tasks), stage gate enforcement,
  description safety rules, multi-homing field handling, and the assignment-last rule.
  Also handles the custom field error recovery pattern.
---

# Asana — Updating

**Single task:** `asana_update_task` (primary connector)
**Batch (up to 50):** `update_tasks` (UI connector `d7bbb126`) — preferred for any multi-task operation
**Always run first:** `protocols/TASK-PREP.md`

---

## Before Updating Anything

Read the task. Without exception. See `protocols/TASK-PREP.md`.

The sequence:
```
1. asana_get_task(task_id, include_comments=true, include_subtasks=true)
2. asana_get_stories_for_task(task_id)
3. Understand current state → then act
```

Batch updates to a single task (one `update_tasks` call with multiple fields) reduce notification events compared to multiple sequential `asana_update_task` calls. Prefer batching when changing more than one field on a task.

---

## Updating Fields (Custom + Native)

```
asana_update_task({
  task_id: "{gid}",
  custom_fields: JSON.stringify({
    "1189628845814528": "{stage_option_gid}",
    "1210940116708566": "{dod_option_gid}",
    "1103808807953314": "{priority_option_gid}"
  }),
  due_at: "2026-04-04T17:00:00Z",   // full datetime preferred
  start_at: "2026-03-31T09:00:00Z",
  // due_on / start_on for date-only (due_on must be present when setting start_on)
  assignee: "{user_gid}"             // only if task is at Focus or Addressing
})
```

**Owner / Driver fields:** When you need to know who to contact about a task, check Driver first, then Owner, then Assignee. All three can be updated and used for @mention routing — they're not just display fields.

**Custom field error:** If Asana returns an error that a field isn't on the project — retry without that field, then create a `[FIX]` task to get it added. Load `index/options/OPTIONS-[project].md` before building update calls to prevent this.

---

## Stage Transitions

Stage is a custom field (GID `1189628845814528`). Every stage move must pass the gate defined in `protocols/PROGRESS-FUNNEL.md`. Check the gate before updating, not after.

```
asana_update_task({
  task_id: "{gid}",
  custom_fields: JSON.stringify({
    "1189628845814528": "{new_stage_option_gid}"
  })
})
```

After any stage move: trigger `combos/priority-reassess.md` on the tasks in the destination stage.

**Field dependency rules (enforce, never violate):**

| Condition | Rule |
|-----------|------|
| Moving to Roadblocked | DoD Status must NOT be Ready |
| Moving to Resolved | DoD Status MUST be Ready ✔ |
| Moving to Focus | DoD Status MUST be Ready ✔ (gate check) |
| Moving to Addressing | Assignee must be set (or set it now — last step) |

---

## Updating Description (Critical — Read This Carefully)

The description field in Asana is `notes` (plain text) or `html_notes` (HTML). **Updates always overwrite — there is no append.** A careless write nukes everything already there.

### Safe Update Protocol:
```
1. Read: asana_get_task(task_id, opt_fields="notes,html_notes")
2. Inspect: check both fields — which one has content?
   → html_notes will likely contain HTML wrappers even for "plain text" tasks
     (Asana wraps all content in HTML internally — see TEST-MATRIX.md T1)
3. Decide how to update:
```

**Decision tree:**
- Description is short and plain → rewrite `notes` with updated content
- Description has rich formatting (tables, images, embeds, complex HTML) → **do not overwrite** — post a comment instead
- Description is long but plain → either: (a) rewrite with your addition included, or (b) create a subtask with its own description for the new content
- You're not sure if the HTML is complex → post a comment. Safe > destructive.

**Never set both `notes` and `html_notes` in the same call.** Pick one format and stick to it.

```
// Safe plain text append
asana_update_task({
  task_id: "{gid}",
  notes: "{existing_content}\n\n---\nUpdate {date}:\n{new_content}"
})

// If original was html_notes, preserve the format
asana_update_task({
  task_id: "{gid}",
  html_notes: "<body>{existing_html}<hr/><p>Update {date}: {new_content}</p></body>"
})
```

---

## Completing a Task

Do not use `completed: true` directly. Always go through `combos/task-complete.md` which verifies all gates (subtasks, DoD, artifacts, summary comment) before marking complete.

If forced to update directly:
```
asana_update_task({
  task_id: "{gid}",
  completed: true
})
```
But don't — the combo protects against incomplete Resolved tasks.

---

## Assignee

**Only set when the task is entering Focus or Addressing.** If someone was already assigned prematurely, leave it — don't unassign. You may inquire but do not silently remove.

```
asana_update_task({
  task_id: "{gid}",
  assignee: "{user_gid}"  // or "me"
})
```

---

## Bulk Updates (up to 50 tasks)

Route through the UI connector's `update_tasks` for any multi-task operation:

```
update_tasks({
  tasks: [
    {
      task: "{gid1}",
      custom_fields: { "1189628845814528": "{stage_gid}" },
      due_on: "2026-04-01"
    },
    {
      task: "{gid2}",
      assignee: "{user_gid}",
      add_followers: ["{gid_a}", "{gid_b}"]
    }
    // up to 50
  ]
})
```

Supported in batch: name, assignee, due_on, start_on, notes, html_notes, completed, parent, add/remove_dependencies, add/remove_dependents, add/remove_projects (with section), add/remove_followers, custom_fields, approval_status.

**Note:** Batch `update_tasks` uses date-only fields (`start_on`/`due_on`). For datetime precision, use single `asana_update_task` with `start_at`/`due_at`. Both datetime variants render correctly in the Asana UI (confirmed T8).

**Confirmation required for bulk destructive operations** (stage changes on 3+ tasks, mass reassign, bulk complete). Show the user the task list and intended changes before executing.

---

## Moving Tasks Between Projects / Multi-Homing

See `skills/structuring/multihome-task.md` and `skills/structuring/move-task.md`.

**Key rule for multi-homing:** Add the task to the new project first, then set that project's custom fields in a second call. **Do not combine `add_projects` and `custom_fields` in one batch call** — confirmed non-atomic (T2): `add_projects` succeeds even if `custom_fields` fails, leaving the task in a partial state with no rollback. Always two sequential calls: (1) add to project, (2) set fields.
