---
name: work-tracking
description: |
  Track agent and user work in conversation threads and commit it to Asana at meaningful
  checkpoints. Use in every session where real work is being done — writing, researching,
  planning, building, reviewing. Maintains a daily work log file, maps conversation
  activity to Asana task GIDs, and merges the log into Asana comments/updates at session
  end or on request. Ensures all work is traceable. Trigger whenever an agent starts a
  working session, whenever a user asks what task work should be linked to, or whenever
  preparing to close a session.
---

# Work Tracking — Session Log + Asana Merge

Not Asana-specific, but always triggers Asana activity. Every substantive piece of work should map to a task.

---

## Session Log File

The agent maintains a rolling daily work log: `work-log-{YYYY-MM-DD}.md`

Location: agent's working directory or designated log path.
One file per day, shared across all threads that day.

### Log Entry Format
```
## {HH:MM} — Thread: {brief thread topic}
Task GID: {gid if known} | Task: {name if known} | Status: CONFIRMED / UNCONFIRMED
Summary: {what happened — what was produced, decided, or found}
Artifacts: {file paths, URLs, doc links — whatever was created or referenced}
Notes: {anything that needs to go into the task as a comment}
---
```

Multi-task threads get multiple entries — one per task referenced.

---

## Task Linkage Rules

**The agent should always know (or find out) which Asana task the current work is attached to.**

How to establish task context:
1. User leads with a task link or name → confirmed. Log it.
2. Agent infers from context (project, topic, prior conversation) → log as UNCONFIRMED, confirm at first natural pause
3. User says "off the books" or "no task" → skip tracking for this thread
4. Not clear → ask once, at a natural pause. Don't interrupt the user's flow mid-thought.

**Don't nag.** Ask once. If no answer, continue working and ask again at end of session.

---

## Multi-Task Sessions

When a conversation covers multiple topics or tasks:
- The log file is the source of truth for mapping conversation segments to task GIDs
- Each distinct topic/task gets its own log entry
- At merge time, the agent groups entries by task and composes a comment per task

---

## Merge to Asana (Checkpoint)

At session end, or when the user requests a merge, or at a significant completion point:

```
Steps:
1. Review the day's log entries
2. Group by task GID
3. For each task with CONFIRMED GID:
   a. Draft a comment from the log entries for that task
      - Include: what was done, decisions made, artifacts with links
      - Remove fluff — this is a task comment, not a journal entry
   b. Present the draft to the user: "Here's what I'd post to [task name] — approve, edit, or skip?"
   c. Post approved comments
4. For UNCONFIRMED entries: present to user, confirm GID, then post
5. For new tasks implied by the log (things that came up but aren't tracked yet):
   flag for task creation — user approves or skips
```

---

## Proactive Research Tasks

If during any session an open question, needed research, or missing context is identified:
- Create a `[FIND]` or `[ANSWER]` or `[SOLVE]` task immediately (don't wait for the merge)
- Don't interrupt the current conversation — create it quietly, log it, surface it at merge or next natural pause

---

## Agent Notes

This skill pairs with `protocols/INBOX.md` and `combos/agent-session-end.md`. The work log feeds the session notes posted to the agent's Asana log project at session end. The two together give a persistent record of what was done across all sessions.
