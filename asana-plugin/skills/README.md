# Asana Plugin v2 — Skill Router

If you need to do something with Asana, start here. Find your action, open the file.

---

## Atomic Skills (single action)

| I need to... | File |
|-------------|------|
| Create a task | `skills/creating/SKILL.md` |
| Create a subtask (any depth) | `skills/creating/SKILL.md` |
| Create a project | `skills/creating/SKILL.md` |
| Post a team status update to a project | `skills/creating/project-status-team.md` |
| Post agent session notes to Asana | `skills/creating/project-status-agent-notes.md` |
| Update task fields, stage, due date | `skills/updating/SKILL.md` |
| Update a task description safely | `skills/updating/SKILL.md` → description section |
| Move task to a different project | `skills/structuring/SKILL.md` → move-task |
| Add task to an additional project (multi-home) | `skills/structuring/SKILL.md` → multihome-task |
| Set subtask parent or reorganize hierarchy | `skills/structuring/SKILL.md` |
| Set task dependencies or dependents | `skills/structuring/SKILL.md` |
| Post a comment or update | `skills/commenting/SKILL.md` |
| @Mention someone in a task | `skills/commenting/SKILL.md` |
| Add or remove followers | `skills/commenting/SKILL.md` |
| Read a task's comment history | `skills/commenting/SKILL.md` |
| Search for tasks (my tasks, someone's tasks, project) | `skills/searching/SKILL.md` |
| Find orphaned tasks ("Where's Timmy") | `skills/searching/SKILL.md` → orphan-tasks |
| Evaluate or reassign task priority (Q-rank) | `skills/prioritizing/SKILL.md` |
| Look up context in NotebookLM or Google Drive | `skills/context-validate/SKILL.md` |
| Track work session + merge to Asana | `skills/work-tracking/SKILL.md` |
| Update reference indexes (projects, fields, players) | `skills/maintenance/SKILL.md` |
| Run workspace hygiene audit | `skills/maintenance/SKILL.md` → workspace-hygiene |

---

## Combo Patterns (multi-step workflows)

| I need to... | Combo |
|-------------|-------|
| Start new tracked work | `task-intake` |
| Break down a complex existing task into subtasks | `task-decompose` |
| Mark work complete (Addressing → Resolved) | `task-complete` |
| Triage the Unsorted backlog | `task-triage` |
| Run daily progress check on Addressing tasks | `daily-check` |
| Check if tasks have been updated on schedule | `micro-update-check` |
| Check inbox and directives at session start | `inbox-check` |
| Wrap up a session and record what was done | `refresh-active-list` + `agent-session-end` |
| Post a team update + ping relevant people | `notify-team` |
| Route and classify an incoming task | `route-task` |
| Reassess priority after a stage move | `priority-reassess` |
| Initialize a session completely | `agent-session-start` |

All combos → `skills/combos/SKILL.md`

---

## Protocols (how agents must behave)

| Topic | File |
|-------|------|
| Progress Funnel — stage gates and rules | `protocols/PROGRESS-FUNNEL.md` |
| Read before write | `protocols/TASK-PREP.md` |
| Daily update requirements for Addressing | `protocols/DAILY-UPDATE.md` |
| Session start inbox management | `protocols/INBOX.md` |
| Notification hygiene — who gets pinged and when | `protocols/NOTIFICATION-HYGIENE.md` |

---

## Reference Data

| What | File |
|------|------|
| All projects + sections + GIDs | `index/PROJECTS.md` |
| All custom fields + GIDs | `index/FIELDS.md` |
| Stage + DoD + Priority option GIDs | `index/options/OPTIONS-core.md` |
| Working Status + Deadline + Update Status GIDs | `index/options/OPTIONS-work.md` |
| Feature Status + Component + Task Weight GIDs | `index/options/OPTIONS-feature.md` |
| All players (humans + agents) | `index/PLAYERS.md` |
