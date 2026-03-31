---
name: asana-structuring
description: |
  Manage Asana task relationships — subtasks at any depth, parent assignment, dependencies,
  dependents, moving tasks between projects, and multi-homing tasks across projects.
  Use when organizing task hierarchies, setting up work sequences, establishing blocking
  relationships, or adding a task to additional boards. Multi-homing is extremely common
  in this workspace — know the field-after-project rule.
---

# Asana — Structuring

**Set parent:** `asana_set_parent_for_task`
**Dependencies:** `asana_set_task_dependencies`
**Dependents:** `asana_set_task_dependents`
**Move/multi-home:** `update_tasks` with `add_projects` / `remove_projects`

---

## Subtask Hierarchy

Subtasks can nest as deep as needed — subtask of a subtask of a subtask. Dependencies apply at every level.

**At creation time:** Fields are optional for subtasks. Set the name and parent; add fields later when the subtask enters Addressing (or when it's multi-homed to another board as a root-level task).

**Set parent on an existing task:**
```
asana_set_parent_for_task({
  task_id: "{child_gid}",
  parent: "{parent_gid}",
  insert_before: null    // null = end of sibling list
})
```

To convert a subtask back to a top-level task:
```
asana_set_parent_for_task({
  task_id: "{gid}",
  parent: null
})
```

**Before creating subtasks:** Check whether the task already has subtasks (`include_subtasks=true` on `asana_get_task`). Don't create duplicate structure.

---

## Dependencies (this task is blocked by others)

```
asana_set_task_dependencies({
  task_id: "{gid}",
  dependencies: ["{blocking_task_gid_1}", "{blocking_task_gid_2}"]
})
```

Use when this task cannot start until other tasks are complete. Asana's native "blocked" notification fires to the assignee when all dependencies are marked complete — the agent does not need to manually trigger this.

When a task's dependencies all complete: verify the task is ready to move back to its prior stage from Roadblocked if it was blocked. Don't rely solely on the Asana notification — include in `combos/inbox-check.md` review.

---

## Dependents (this task blocks others)

```
asana_set_task_dependents({
  task_id: "{gid}",
  dependents: ["{waiting_task_gid_1}"]
})
```

When this task completes: check its dependents as part of `combos/task-complete.md`. Surface any newly unblocked tasks to the relevant assignees.

---

## Moving a Task to a Different Project

Task moves from Project A to Project B — removed from A entirely:

```
update_tasks({
  tasks: [{
    task: "{gid}",
    add_projects: [{ project_id: "{project_b_gid}", section_id: "{section_gid}" }],
    remove_projects: ["{project_a_gid}"]
  }]
})
```

After moving: load `index/options/OPTIONS-[project_b].md` and set any new required fields. If `add_projects` + `custom_fields` in the same call works (see TEST-MATRIX.md T2), combine them. Otherwise: move first, then update fields in a second call.

Post a comment on the task noting the move and reason.

---

## Multi-Homing a Task (adding to additional project)

Most common structural operation in this workspace. Task stays in its original project AND appears on another board.

```
update_tasks({
  tasks: [{
    task: "{gid}",
    add_projects: [{ project_id: "{new_project_gid}", section_id: "{section_gid}" }]
  }]
})
```

**Critical field rule:** A project's custom fields can only be set on a task AFTER the task is in that project. Add to project first, then set fields. Confirm whether a single combined call works (TEST-MATRIX.md T2).

After multi-homing:
1. Load `index/options/OPTIONS-[new_project].md`
2. Identify which fields are required or relevant on the new project
3. Update the task with those fields (second call if needed)
4. Post a comment noting the multi-home: which boards it's now on, what changed

**Multi-homed subtasks:** A subtask can be a root-level task on a different board than its parent. In that case it behaves as a full task on the new board — fields, stage, and assignee all apply independently. Consider fields when the subtask enters Addressing on any of its boards.

---

## Structural Pre-Check

Before creating any subtask or setting any relationship, ask:
- Does this work already exist as a task somewhere? (search first)
- Is this a step within a known parent task or an independent item?
- Are there other tasks this blocks or that block it?

Capture these relationships at intake time. Retrofitting structure is more expensive than building it correctly upfront.
