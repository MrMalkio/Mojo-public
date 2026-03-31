# Daily Update Protocol — Addressing Stage

Any task in Addressing requires a progress update on a cadence defined by its Q-rank. This is not optional — it's the mechanism that keeps the team informed and prevents Malkio from having to stop what he's doing to chase context.

---

## Update Cadence

| Q-Rank | Update required within |
|--------|----------------------|
| Q1 (07–10) | 24 hours |
| Q2 (03–06) | 48 hours |
| Q3 (02) | 48 hours |
| Q4 (01) | 72 hours |

The driver is primarily responsible for posting the update. The agent is responsible for noticing when it's overdue and acting on it.

---

## What Counts as an Acceptable Update

A comment on the task that contains at least one of:
- Status of active work (what's been done, what's in progress)
- A specific next step with a clear owner
- A blocker report (what's blocking, who owns the resolution)
- A request for review or input with context
- A confirmed completion of a subtask or milestone

What does NOT count:
- "Working on it"
- "Still in progress"
- A comment that just acknowledges a previous comment
- Auto-generated activity log entries (stage changes, field updates)

---

## Agent Response to Overdue Update

1. Check if the update is overdue (read stories, check timestamps)
2. If overdue:
   - **Option A (user is present):** Surface the task and ask the driver to provide an update, or offer to draft one
   - **Option B (automated check):** Set Update Status = "Needs Update" — this triggers Asana's native notification to the assignee/followers
3. If no response within the next SOP window after the field flip:
   - Slack DM to Driver/Owner (if Slack available) with hyperlinked task reference
   - Format: `"[Task name](https://app.asana.com/0/9526911872029/{task_gid}?focus=true) — update overdue by [X] hours. What's the status?"`

---

## Drafting an Update on Behalf of the Driver

If the driver is present and approves, the agent may draft the comment:

```
Template:
Update — {date}:
Progress: {what has been done since last update}
Current focus: {what is actively being worked on}
Next step: {specific next action and who owns it}
Blockers: {any, or "none"}
ETA: {expected completion or next checkpoint}
```

Keep it short. No padding. The driver reviews and confirms before it's posted, unless the agent has been explicitly authorized to post autonomously.

---

## Update Status Field

| Value | Meaning |
|-------|---------|
| Updated | Acceptable update received within window |
| Needs Update | Window expired, update required — notifies assignee/followers automatically |

The agent sets this field. The notification is Asana-native — no separate comment needed for the ping itself.
