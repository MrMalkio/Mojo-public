# Notification Hygiene

Every Asana action that touches `assignee` or `followers` generates inbox notifications for real humans. Agents must treat this as a cost, not a side effect. Unnecessary pings erode trust and create noise that drowns out the signals that matter.

---

## What Triggers Notifications

| Action | Who gets notified |
|--------|------------------|
| Task assigned to user | That user |
| User added as follower | That user |
| Comment posted on task | All followers + assignee |
| Subtask created on task | All followers + assignee |
| Dependency added | Assignee of each task in the relationship |
| Task stage or field changed | All followers + assignee |
| Update Status field → "Needs Update" | Assignee + followers (native Asana behavior) |
| Blocking task completed | Assignee of the waiting task (native Asana) |

---

## Core Rules

**Assignee is late.** Do not set `assignee` until the task reaches Focus or Addressing. Use the `Driver` custom field for early ownership — it records who owns the work without triggering a notification.

**Followers are intentional.** Only add followers when the person has a specific, warranted reason to track the task at this point in time. "They might want to know" is not enough. For FYI-only updates, use Slack.

**Batch field updates.** When changing multiple fields on a task, do it in one `update_tasks` call rather than sequential single-field updates. Multiple changes in one call = one notification event. Sequential calls = multiple pings.

**Comments count.** Every comment notifies everyone on the task. No filler, no acknowledgements, no redundant summaries. See `skills/commenting/SKILL.md`.

**Don't unassign prematurely set assignees.** If someone was already assigned before it was the right time, leave it. You may note it, but removing them creates another notification event and may confuse the assignee. Inquire if needed.

---

## Driver vs Owner vs Assignee

All three fields identify someone connected to the task. Use them deliberately:

| Field | Purpose | Sets off notification? | Set when |
|-------|---------|----------------------|----------|
| Driver | Custom field — who does the work | ❌ No | As early as needed |
| Owner | Custom field — who is accountable | ❌ No | As early as needed |
| Assignee | Native Asana — formal task holder | ✅ Yes | Focus or Addressing only |

**Contact routing order:** When you need to @mention or reach out about a task, check Driver first → Owner second → Assignee third. Any of these can be the right point of contact depending on context.

---

## Followers — Lifecycle

| Stage | Follower additions warranted |
|-------|------------------------------|
| Unsorted | None (task not committed) |
| Todo | Driver if not already following |
| Focus | Driver + Owner if not following |
| Addressing | Relevant reviewers only when review is imminent |
| Reviewing | Reviewer(s) — add at the moment review is requested |
| Resolved | None needed |
| Roadblocked | Escalation owner if they don't already follow |

---

## The Update Status Field

When Update Status flips to "Needs Update", Asana's native notification system automatically pings the assignee and followers. The agent does NOT need to post a comment for this ping — the field change itself is the notification. A separate Slack message is supplemental only, triggered after the SOP response window has passed without a reply.
