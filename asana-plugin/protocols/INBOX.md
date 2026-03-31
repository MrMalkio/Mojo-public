# Inbox Protocol — Agent Session Start

The Asana inbox isn't accessible via API for agents the way it is for humans. This protocol defines how agents poll for directed activity and maintain continuity across sessions.

---

## Phase 1: Polling (current)

Run `inbox-check` combo at every session start:

```
1. Read last project status from agent's log project:
   asana_get_project_statuses({ project_gid: "{agent_log_project_gid}", limit: 1 })
   → Recover: open items, waiting tasks, last-session context

2. Check known followed tasks (from CONTRIBUTIONS.md waiting list):
   For each followed task GID:
   asana_get_stories_for_task({ task_id: "{gid}", limit: 20 })
   → Filter for: new comments since last session timestamp
   → Look for: @mentions of agent name, action verbs, responses to previous asks

3. Search for new @mentions since last session:
   asana_search_tasks({
     workspace: "9526911872029",
     text: "{agent_name}",
     modified_on_after: "{last_session_date}",
     completed: false
   })

4. Categorize each item found:
   - Directive: @mention with action verb → act
   - Response to waiting task → complete the pending action
   - FYI: no action required → note and move on

5. Create subtasks on Agent Activity Log task for each actionable item:
   Parent: "{activity_log_task_gid}"
   Format: "[action type] {task name or topic} — {date}"

6. Act on directives in priority order (Roadblocked > Addressing > Focus > Todo)
```

---

## Agent Activity Log Task

Each agent has one long-running task in their log project:
- **Name:** `[Agent Activity Log — {agent_name}]`
- **Purpose:** Central record of all directed activity. Humans can review and intervene via comment.
- **Subtasks:** One per recognized inbox item. Each subtask captures what was found and what was done.

Agents leave session notes on the log project via `asana_create_project_status` (blue, structured). Next session reads the latest status to restore context.

---

## Maintaining the Followed Tasks List

Agents track task GIDs they are following in CONTRIBUTIONS.md under `Active/Blocking Tasks`. This list powers efficient polling — known tasks get checked directly rather than searched for.

Update this list:
- When you follow a new task (add to list)
- At session end via `refresh-active-list` combo (rewrites the whole block)
- When a task reaches Resolved and is no longer active (remove)

---

## Waiting Tasks

When an agent posts a comment requesting context and is waiting for a response:
- Log the task GID in the waiting section of CONTRIBUTIONS.md
- At next inbox-check: pull stories for each waiting task, look for responses
- When a response arrives: act on it, remove from waiting list
- If no response after SOP window: escalate via Slack (skills/commenting/)

---

## Phase 2 (future): Agent Mailbox

A dedicated queryable mailbox is being built that will mirror human Asana inbox behavior — receiving webhook-pushed events, mentions, and directed messages. When available, this protocol will update to query the mailbox directly. The polling pattern above becomes a fallback.

Design note: the Agent Activity Log task structure (master + subtasks) is directly importable into the Anasa `agent_inbox` table when that system is implemented.
