---
name: asana-combos
description: |
  Multi-step Asana workflow patterns. Use when carrying out compound operations that
  span multiple atomic skills: starting new work (task-intake), breaking down complex
  tasks (task-decompose), wrapping up completed work (task-complete), triaging backlogs
  (task-triage), checking daily Addressing progress (daily-check), running micro-update
  checks (micro-update-check), session start/end rituals, inbox management, and team
  notifications. Trigger this skill whenever a workflow involves 3+ Asana operations.
---

# Asana — Combo Patterns

Each pattern below is a named multi-step workflow. Reference the atomic skill files for tool-level details.

---

## `task-intake` — Starting New Tracked Work

Use when: starting any new piece of work that doesn't yet exist as a task, or when logging a new item from a conversation.

```
Steps:
1. Check if a related task already exists (typeahead search + context check)
2. Determine: is this a subtask or root task? Does it block/depend on anything?
3. Consult context-validate if relevant (NotebookLM / Google Docs — see skills/context-validate/)
4. Create task:
   - name with prefix if applicable [SOLVE][FIND][BUILD] etc.
   - notes: what + why + DoD if known
   - project_id + section_id (from index)
   - start_at / due_at (full datetime preferred)
   - custom_fields: Stage (Unsorted or Todo), DoD Status, Priority, Component, Driver
   - parent if subtask
   - followers: only if warranted
   - assignee: LAST — only if entering Focus or Addressing
5. Set parent / dependencies / dependents if applicable (skills/structuring/)
6. Post intake comment if additional context was gathered
7. Trigger priority-reassess if Stage = Focus or Addressing
```

---

## `task-decompose` — Break Down a Complex Existing Task

Use when: a task exists with a long or complex description but no subtasks, and the work is clearly multi-step.

```
Steps:
1. task-prep: read task + all stories (protocols/TASK-PREP.md)
2. Consult context-validate if relevant (NotebookLM / Google Docs for richer context)
3. Parse description/notes to identify discrete units of work
4. Propose subtask structure (confirm with user if confidence is not high)
5. Create subtasks at whatever depth is needed — subtask of subtask is fine
   - Fields optional at creation for subtasks
   - Set names, parents, descriptions; add fields when they enter Addressing
   - Set dependencies between subtasks if sequencing is clear
6. Post summary comment on parent: "Decomposed into [N] subtasks: [list]. Reason: [brief]."
7. Reassess parent task stage:
   - If subtasks aren't scoped yet → step parent back to Focus, comment why
   - If subtasks are ready → parent may stay in Addressing
8. For each subtask that immediately qualifies for Focus/Addressing → set stage + trigger priority-reassess
```

If further context is needed from a human:
- Post comment @mentioning Driver/Owner with specific question
- Log task GID in waiting list (CONTRIBUTIONS.md)
- Revisit at next inbox-check when response appears

---

## `task-triage` — Process Unsorted Backlog

Use when: clearing the Unsorted stage of a project, or when a batch of new tasks needs classification.

```
Steps:
1. Fetch batch of 10 Unsorted tasks (skills/searching/ — tasks-unsorted variant)
2. For each task:
   a. Does it have enough context for anyone to understand it?
      → NO: gather from KB (context-validate), conversation, or post comment requesting context
      → YES: proceed
   b. Does it already qualify for Todo? (check gate: clear name, assignee/driver, draft DoD, component tagged)
      → NO: add missing fields or leave in Unsorted with a comment on what's needed
      → YES: move to Todo
   c. Does it immediately qualify for Focus or beyond?
      → Check all intermediate gates — must pass each in sequence
      → If yes: advance directly to the qualifying stage, skip intermediate stops
3. Fields are secondary to context — don't fill fields speculatively before you understand the task
4. After batch: check if Addressing is now empty → cascade to Focus if eligible tasks exist
```

---

## `task-complete` — Wrap Up Finished Work (Addressing → Resolved)

Use when: a driver believes their work is done and wants to move a task to Resolved.

```
Pre-check (do not skip):
1. task-prep: read task + all stories
2. Verify all subtasks are completed
3. Verify DoD Status = Ready ✔
   → If not Ready: surface to driver/assignee — "Where is the DoD? What is it?"
   → If they verbally confirm DoD is met: set DoD Status = Ready on their behalf
4. Verify all required artifact links are present:
   - REF_LINK, TEST_LINK, TRANSCRIPT (as applicable)
   - Visual proof linked (screenshot/recording) if applicable
5. Verify no active FS/SS blocking dependencies

Then:
6. Post summary comment (driver or agent): what was done, links, outcome
7. Update Stage → Resolved
8. Check dependents: are any tasks now unblocked? Surface to their assignees.
9. Trigger priority-reassess on newly unblocked tasks
```

**DoD clarification:** `DoD Status = Ready ✔` is the gate to enter Addressing — it means the Definition of Done was confirmed before work started, not that the work is done. If a task is in Addressing without DoD = Ready, confront the driver/assignee: "What is your DoD? Can you confirm it?" Once confirmed, set to Ready.

---

## `daily-check` — Addressing Stage Review

Use when: starting the day, checking in mid-session, or running the daily progress check.

```
Steps:
1. Fetch all Addressing tasks for the relevant user/project (skills/searching/)
2. For each:
   a. Check last comment timestamp — is a daily update overdue?
      → Overdue: prompt user or draft comment on their behalf
   b. Review update content — any new blockers, completions, or stage changes indicated?
   c. Is the task complete? → trigger task-complete
   d. Is it blocked? → trigger move to Roadblocked + post blocker comment
3. If Addressing is empty → cascade:
   → Search Focus for eligible tasks (no blockers, DoD = Ready)
   → Propose or auto-advance eligible tasks to Addressing
   → If Focus also empty → search Todo, advance eligible to Focus
4. priority-reassess for any tasks that moved stages
```

---

## `micro-update-check` — Update Status Field Sweep

Use when: running the automated progress funnel hygiene check on Addressing tasks.

```
Steps:
1. Fetch all Addressing tasks for the project
2. For each task:
   a. Get stories — check most recent comment timestamp
   b. Is an acceptable update present within the SOP window?
      (Q1: 24h, Q2+: 48h — see protocols/DAILY-UPDATE.md)
      → YES: Update Status = "Updated"
             Schedule next check: flip field back to "Needs Update" at midday tomorrow
      → NO: Update Status = "Needs Update"
             Asana's native notification fires to assignee/followers automatically on field change
             If Slack available: also DM Driver/Owner with hyperlinked task reference (skills/commenting/)
3. Based on update content for each task:
   - Blocker surfaced in comment → trigger move to Roadblocked
   - Work complete indicated → trigger task-complete check
   - Stage change implied → verify gate + update
```

**Note:** The `Update Status` field flip to "Needs Update" triggers Asana's native inbox notification to assignee/followers. No separate comment required for the ping. The Slack message is supplemental only.

---

## `inbox-check` — Session Start Review

Use when: beginning any agent session.

```
Steps:
1. Read last project status from agent's log project (asana_get_project_statuses)
   → Recover open items, waiting tasks, session context
2. Check followed tasks:
   → Agent maintains a list of followed task GIDs in CONTRIBUTIONS.md
   → For each: asana_get_stories_for_task — look for @mentions, directives, responses
3. Search for new @mentions since last session:
   asana_search_tasks({ text: "{agent_name}", modified_since: "{last_session_timestamp}" })
4. For each item found: categorize as directive / response-to-waiting / FYI
5. Create subtasks on Agent Activity Log task for each actionable item
6. Act on directives
7. Respond to waiting tasks where context has arrived
```

**Future:** Agent mailbox (in development) will replace the polling search with a queryable inbox that mirrors human Asana inbox behavior.

---

## `refresh-active-list` — Session End

Use when: ending any agent session.

```
Steps:
1. Search Addressing + Roadblocked tasks for this agent (assignee=me or driver=me)
2. Write updated list to CONTRIBUTIONS.md Active/Blocking section:
   Format: - [{gid}] task name — Stage — Project
   Max 10 entries
3. Post project status on agent's log project:
   asana_create_project_status({
     project_gid: "{agent_log_project_gid}",
     color: "blue",
     title: "Agent session {date}",
     text: "Worked on: [...]. Pending: [...]. Open questions: [...]. Waiting for: [{gid list}]."
   })
```

---

## `notify-team` — Board Update + Team Ping

Use when: a significant milestone is reached, a sprint ends, or a major blocker is resolved.

```
Steps:
1. Create project status update (skills/creating/project-status-team.md)
   - color: green (on track) / yellow (at risk) / red (blocked)
   - title: descriptive milestone name
   - text: what happened, what's next, who owns what
2. Post comment on relevant tasks @mentioning stakeholders
   - Use Driver → Owner → Assignee routing to identify who to mention
   - Include task link in focus view format
3. If immediate response needed: Slack DM via skills/commenting/ Slack escalation pattern
```

---

## `route-task` — PM Intake / Routing

Use when: a task lands in Unsorted and needs to be classified, structured, and directed to the right owner.

```
Steps:
1. task-prep on the incoming task
2. Understand scope: standalone task, subtask of something, or triggers subtasks?
3. Check fields: all required fields present?
4. Check context: is DoD clear? (context-validate if needed)
5. Assign Driver field (not assignee yet)
6. Set/confirm Stage (Unsorted → Todo if gates pass)
7. Link subtasks or dependencies if applicable (skills/structuring/)
8. Post routing comment: what this task is, who's driving it, what's expected next
```

---

## `priority-reassess` — On Stage Move

Use when: any task moves into a new stage.

See `skills/prioritizing/SKILL.md` for full steps. Triggered at: intake, stage update, task-complete (for newly unblocked dependents).

---

## `agent-session-start` — Full Session Init

```
1. Read own PAT from agent-access/{agent-name}.env
2. inbox-check (see above)
3. refresh-active-list review (read what was written last session)
4. Read last project status from log project for session continuity
5. Set working priority for this session based on stage-order + Q-rank
```

---

## `agent-session-end` — Full Session Close

```
1. refresh-active-list (update CONTRIBUTIONS.md)
2. Post project status as session notes (blue, structured)
3. Note any waiting tasks in status body
4. Log any tests or findings to TEST-MATRIX.md if applicable
```
