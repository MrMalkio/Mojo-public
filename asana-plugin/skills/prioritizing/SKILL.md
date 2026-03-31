---
name: asana-prioritizing
description: |
  Evaluate and assign Q-rank priority to Asana tasks. Run when a task moves into a new
  stage, when priority seems misaligned, or on manual request. Compares task against
  siblings in the same stage on the primary project. Also covers stage-order decision
  logic when no specific task is given. Trigger whenever priority needs to be set,
  reassessed, or explained.
---

# Asana — Prioritizing

**Tools:** `asana_search_tasks`, `asana_update_task`, `asana_get_task`

---

## Q-Rank Matrix

Priority is evaluated on two axes: **urgency** (deadline pressure) and **strategic importance**.

| Q-Rank | Score | Urgency | Importance | Action |
|--------|-------|---------|------------|--------|
| Q1 | 07–10 | Imminent deadline | Strategically important | Must happen now — no deferral |
| Q2 | 03–06 | Deadline flexible | Strategically important | Schedule with intention |
| Q3 | 02 | Deadline pressuring | Not important | Delegate or deprioritize |
| Q4 | 01 | No urgency | Not important | Defer to Unsorted or kill |
| Unsure | 0 | Cannot assess | Cannot assess | Flag for human decision |

**Urgency signals:** due date within 48h (Q1-tier), within the week, deadline band field value, dependencies about to unblock something critical.

**Importance signals:** linked to a primary project goal, Malkio-owned or CEO-assigned, has dependents waiting on it, customer-facing, sprint focus area.

---

## When to Reassess Priority

**Triggered automatically:** when a task moves INTO a new stage.
**Triggered manually:** on request, during daily-check, when a new task enters the same stage.
**Not triggered automatically:** when a task leaves a stage.

Scope: reassess the moved task against siblings in the **same stage on the task's primary project**. For multi-homed tasks, use the project where the task was originally created or the one with the highest priority designation.

---

## Reassessment Steps

```
1. Get the moved task:
   asana_get_task(task_id, opt_fields="name,custom_fields,due_on,due_at,memberships,assignee")

2. Get siblings in the same stage on the primary project:
   asana_search_tasks({
     workspace: "9526911872029",
     projects_any: "{primary_project_gid}",
     custom_fields: { "1189628845814528": "{current_stage_option_gid}" },
     completed: false,
     opt_fields: "name,gid,custom_fields,due_on"
   })

3. Score the moved task on Q-rank matrix

4. Compare against sibling Q-ranks:
   - Is the current task's Q-rank appropriate relative to others in the stage?
   - Is any sibling obviously mis-ranked given deadline/importance context?

5. If update is warranted:
   asana_update_task({
     task_id: "{gid}",
     custom_fields: JSON.stringify({ "1103808807953314": "{new_priority_option_gid}" })
   })
   Post a comment: "Priority updated to [Q-rank] — [one-line reason]. Compared against [N] tasks in [stage]."

6. If no change needed: note it in your reasoning but don't post a comment (no-op)
```

---

## Stage-Order Decision (no specific task given)

When an agent has no specific task to work on, work in this order:

1. **Roadblocked** — review and see if any blockers have resolved
2. **Addressing** — active work, daily update check
3. **Focus** — pull eligible tasks if Addressing is empty
4. **Todo** — pull eligible tasks if Focus is empty
5. **Unsorted** — triage in batches of 10

Within a stage: Project priority → Q-rank → most recently modified.

Never skip a Roadblocked item to work on something lower-priority without documenting why.

---

## Priority Field Update

```
asana_update_task({
  task_id: "{gid}",
  custom_fields: JSON.stringify({
    "1103808807953314": "{priority_option_gid}"
  })
})
```

Option GIDs for Priority → `index/options/OPTIONS-core.md`

---

## Comments on Priority Changes

When you change a task's priority, post a comment explaining:
- What it was changed to
- Why (deadline, importance, sibling comparison)
- What stage triggered the reassessment

When you're NOT changing priority after reassessment, no comment needed. Silence = confirmed.
