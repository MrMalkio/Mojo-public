---
name: asana-commenting
description: |
  Post comments, read task story history, manage followers, and @mention people or tasks
  in Asana. Use whenever posting an update, asking for input via Asana, logging progress,
  notifying a team member, or reading the comment history of a task before acting.
  Covers comment quality rules, @mention URL format, notification hygiene, and the
  Slack escalation pattern for unresponsive users.
---

# Asana — Commenting & Stories

**Post comment:** `asana_create_task_story`
**Read history:** `asana_get_stories_for_task`
**Add followers:** `asana_add_task_followers`
**Remove followers:** `asana_remove_task_followers`

---

## Comment Quality Rules

These are non-negotiable. Every comment posted by an agent must meet this bar:

- **No filler.** No "I've updated the task", "As requested", "Hope this helps", "Let me know if you need anything". Cut it.
- **No redundancy.** Don't repeat what's already in the task description or earlier comments. Read the history first.
- **Value only.** Every comment should contain at least one of: a decision, a status update, a finding, a question requiring a specific response, an artifact link, or a blocker report.
- **Specificity.** If you're asking for context or input, state exactly what you need and why the task can't move forward without it.

Comments are notifications. Every comment pings everyone on the task. Write accordingly.

---

## Posting a Comment

**Always use plain text (`text` field), not `html_text`, unless linking Asana objects via @mention URLs.**

```
asana_create_task_story({
  task_id: "{gid}",
  text: "Your comment here. Plain text. No HTML tags."
})
```

If you need to embed @mentions, use `html_text` with a `<body>` wrapper:
```
asana_create_task_story({
  task_id: "{gid}",
  html_text: "<body>Update: context confirmed by <a data-asana-gid=\"{user_gid}\"/>. Moving to Focus. Ref: <a data-asana-gid=\"{task_gid}\"/></body>"
})
```

---

## @Mention Format

**Person:**
`https://app.asana.com/1/9526911872029/profile/{user_gid}`

Paste the full URL in plain text — Asana renders it as a chip. No surrounding name text needed. Do not wrap in brackets or quotes.

**Task:**
`https://app.asana.com/1/9526911872029/project/{project_gid}/task/{task_gid}?focus=true`

Always append `?focus=true` to task links — opens the task in the focused detail view. Confirmed as the correct UX (T8 finding). Or use `data-asana-gid` in `html_text` for cleaner @mention linking.

**Who to @mention:** Check Driver field first, then Owner, then Assignee. Use whichever is the most appropriate point of contact for the action being requested. All three fields are valid contact routing signals.

---

## Reading Story History

Always read before posting or updating. See `protocols/TASK-PREP.md` for the full pattern.

```
asana_get_stories_for_task({
  task_id: "{gid}",
  limit: 50,
  opt_fields: "created_at,created_by,text,html_text,type,resource_subtype"
})
```

What to look for:
- Directives to you: @mentions with action verbs
- Decisions already made: don't re-litigate
- Last update timestamp: is a daily update overdue?
- Blocker context: what was the blocker, is it still active?
- Open questions that were never answered

---

## Waiting-for-Context Pattern

When the agent needs human input to proceed on a task:

1. Post a comment on the task @mentioning the relevant person (Driver/Owner/Assignee)
2. State exactly what's needed and why the task is blocked on it
3. Log the task GID in your session notes / CONTRIBUTIONS.md waiting list
4. On next inbox-check or session start: check if a response was posted on waiting tasks
5. If context was gathered proactively (NotebookLM, Google Docs, web): present findings in the comment for validation — especially for externally-sourced info

Comment template:
```
Waiting on: [specific question or artifact needed]
Reason: [why this is required before proceeding]
Next step once answered: [what the agent will do with the response]
```

---

## Followers — Notification Hygiene

Adding a follower means they get a notification for every subsequent comment, subtask, and significant change. Be deliberate.

```
// Add
asana_add_task_followers({
  task_id: "{gid}",
  followers: "{user_gid},{user_gid2}"
})

// Remove
asana_remove_task_followers({
  task_id: "{gid}",
  followers: "{user_gid}"
})
```

When to add followers:
- Person has a warranted action or decision to make
- Person is Driver or Owner and wasn't already following
- Review has been requested (add reviewer at that moment, not before)

When NOT to add followers:
- FYI only — post a Slack message instead
- Speculative — "they might want to know"
- The task is in Unsorted/Todo and the person has no current action

---

## Slack Escalation (when Asana comment isn't getting a response)

Trigger: user has not responded on Asana within the SOP window after a comment @mentioning them.

Requires Slack MCP (`mcp__15ac211e...`). Check availability before attempting.

**Message format:** Always include a hyperlinked reference to the specific resource. Never send a bare URL.

```
// Priority 1: Direct link to the specific comment (if story_gid is known)
"[Task name — see this comment](https://app.asana.com/0/9526911872029/{story_gid}) needs your input: [one-line summary of what's needed]."

// Priority 2: Task in focus view (always available)
"[Task name](https://app.asana.com/0/9526911872029/{task_gid}?focus=true) needs your response — [one-line summary]. Posted [X] hours ago on Asana."
```

Send as a DM to the user. Look up their Slack user ID via `slack_search_users` if not already known. Include just enough context that the person knows what they're walking into before clicking.

This is a secondary channel. Asana comment is always primary and always posted first.
