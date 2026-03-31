---
name: asana-creating
description: |
  Create Asana tasks, subtasks (at any depth), projects, and project status updates.
  Use when starting any new tracked work, logging a concept, breaking down a task,
  creating proactive [SOLVE]/[ANSWER]/[FIND] tasks, or setting up a new project.
  Always invoked before any create operation. Covers single and bulk creation patterns,
  field pre-flight, notification hygiene, and the assignment-last rule.
---

# Asana — Creating

**Tools:** `asana_create_task`, `update_tasks` (batch, up to 50), `asana_create_project`, `asana_create_project_status`

---

## Before Creating Any Task

**1. Is this a subtask or dependency of an existing task?**
Before creating, consider: does this work belong under an existing task? Is it a step within something already tracked? Check with the user or search if uncertain. Creating orphaned top-level tasks when a parent exists is a hygiene problem.

**2. Load the project's field map**
Consult `index/options/OPTIONS-[project].md` for the target project before building the call. Only set fields that exist on that project — Asana returns an error if you set a field not attached to the project. If the OPTIONS file isn't available, fall back to `index/FIELDS.md`.

**3. Notification hygiene**
Anyone set as `followers` or `assignee` will receive inbox notifications. Set followers deliberately — only people who have a warranted reason to track this task from creation. See `protocols/NOTIFICATION-HYGIENE.md`.

---

## Task Creation — Field Sequence

Build calls in this order to minimize notification churn and field errors:

```
1. name           — clear, actionable, prefixed if applicable (see Task Types below)
2. notes          — description: what, why, DoD if known (plain text)
3. project_id     — required context anchor
4. section_id     — from index/PROJECTS.md, avoids API call
5. start_at / due_at  — full datetime preferred over start_on/due_on when times are known
   (start_on / due_on for date-only; due_on must be present if start_on is set)
6. custom_fields  — stage (default: Unsorted or Todo), DoD Status, Priority, Component
                  — Driver field if known (early ownership without inbox spam)
7. followers      — only if warranted
8. parent         — if subtask, set at creation time
9. assignee       — LAST. Only set if task is entering Focus or Addressing.
                    Leave null for Unsorted/Todo — use Driver field for ownership instead.
```

**Driver vs Assignee:**
- `Driver` = custom field. Who owns the work. Set early. No inbox notification.
- `assignee` = Asana native field. Triggers notifications. Set at Focus/Addressing only.
- `Owner` field = same treatment as Driver — use for @mention routing and contact, not for triggering notifications prematurely.

---

## Single Task
```
asana_create_task({
  name: "[PREFIX] Clear actionable task name",
  notes: "What needs to happen and why. DoD if available.",
  project_id: "{project_gid}",
  section_id: "{section_gid}",       // from index
  start_at: "2026-03-30T09:00:00Z",  // ISO 8601 with time when known
  due_at: "2026-04-04T17:00:00Z",
  custom_fields: JSON.stringify({
    "1189628845814528": "{stage_option_gid}",    // Stage
    "1210940116708566": "{dod_status_option_gid}", // DoD Status
    "1103808807953314": "{priority_option_gid}",   // Priority
    "{driver_field_gid}": "{driver_user_gid}"       // Driver (not assignee)
  }),
  workspace: "9526911872029"
  // assignee: omit unless Focus/Addressing
})
```

---

## Subtask (any depth)

```
asana_create_task({
  name: "Subtask name",
  notes: "...",
  parent: "{parent_task_gid}",
  // No project_id needed — inherits from parent
  // Fields optional at subtask creation, but set if going straight to Addressing
  // due_at / start_at still recommended if timing is known
})
```

Subtasks can nest as deep as needed. Dependencies apply at every level. Fields are not required at subtask creation time but should be reviewed when the subtask enters Addressing, especially if it is multi-homed (appears as a root-level task on another board).

If creating many subtasks at once, use the batch `update_tasks` tool — see Bulk below.

---

## Bulk Task Creation (batch)

For creating/initializing multiple related tasks, use `update_tasks` (UI connector) to update fields in one call after creating tasks individually. For initial creation, chain `asana_create_task` calls but batch the subsequent field/follower updates:

```
// Step 1: Create tasks (individual calls — no batch create tool)
// Step 2: Batch update fields, followers, dates on the created tasks
update_tasks({
  tasks: [
    { task: "{gid1}", custom_fields: {...}, due_on: "2026-04-01" },
    { task: "{gid2}", custom_fields: {...}, due_on: "2026-04-03" },
    // up to 50
  ]
})
```

---

## Task Types (Proactive Prefixes)

When an agent identifies an open question, needed research, or missing information during any workflow, create a task immediately with the appropriate prefix:

| Prefix | Use for |
|--------|---------|
| `[SOLVE]` | Problem that needs a solution or decision |
| `[ANSWER]` | Question directed at a specific person |
| `[FIND]` | Research or lookup needed |
| `[BUILD]` | Something to create or implement |
| `[REVIEW]` | Something needing human review or approval |
| `[FIX]` | Known bug or error to correct |

**Proactive assignment pattern for [ANSWER]/[FIND]:**
1. Create the task immediately — don't wait
2. If a research agent is available → assign to them, set Stage = Focus
3. If a specific team member likely has the answer → assign to them AND begin researching proactively
4. Present preliminary findings in task description or comment, flagged for validation
5. For multiple-choice scenarios → propose options in description, leave for confirmation
6. This serves both parties: requester gets faster answer, responder gets a head start

---

## If a Premature Assignee Was Already Set

If someone already assigned a task before it was at Focus/Addressing stage — leave it. Don't unassign. You may note it: *"I see X is already assigned — task is still in Unsorted. Is that intentional?"* Then proceed. Never silently unassign.

---

## Custom Field Error Recovery

If `asana_create_task` returns an error indicating a custom field is not on the project:
1. Retry the call without that specific field
2. Create a follow-up task: `[FIX] Add field "[field name]" to project "[project name]"` — assign to Caspera or workspace admin
3. This shouldn't happen if you loaded the project's OPTIONS file first (it tells you which fields exist)

---

## Project Status Updates → See `skills/creating/project-status-team.md` and `project-status-agent-notes.md`

## Creating Projects → See `skills/creating/project.md`
