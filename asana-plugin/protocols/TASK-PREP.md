# Task Prep — Read Before You Write

The single most important habit for any agent operating in this workspace: **never mutate a task you haven't read first.** Asana tasks accumulate context in comments, subtasks, and custom fields that isn't visible from search results. Acting without reading leads to duplicate work, contradicted decisions, and broken trust.

---

## The Task-Prep Pattern

Run this before updating any existing task:

```
1. asana_get_task(task_id, include_comments=true, include_subtasks=true)
   → Read: current stage, all custom fields, assignee, due date, subtask status

2. asana_get_stories_for_task(task_id)
   → Read: full comment history — decisions made, blockers resolved, work done
   → Specifically look for: last update, any @mentions of you, open questions

3. Assess:
   → What is the current state?
   → What has already been tried or decided?
   → What does the next action need to account for?

4. Then act.
```

This takes 10–30 seconds. Skipping it costs hours.

---

## What to Look For in Stories

- **Directives to you:** @mentions with action verbs ("Caspera please...", "@agent update...")
- **Blocker context:** what was the blocker, is it still active?
- **Last update timestamp:** is a daily update overdue?
- **Decisions already made:** don't re-litigate what's in the comments
- **Contradictions:** if the task fields say one thing and the comments say another, flag it

---

## When Task-Prep Is Required

| Situation                              | Required? |
|----------------------------------------|-----------|
| Updating stage of an existing task     | ✅ Yes    |
| Posting a comment on an existing task  | ✅ Yes    |
| Changing assignee or due date          | ✅ Yes    |
| Adding a subtask to an existing task   | ✅ Yes    |
| Creating a brand-new task              | ❌ No     |
| Searching / reading only               | ❌ No     |

---

## After Reading

Document your read in your reasoning before acting. If you're posting a comment, don't repeat what's already been said. If you're updating a field, know why it was at its current value before changing it.

If something in the task state looks wrong (e.g., stage doesn't match actual progress), fix it and note what you corrected and why.
