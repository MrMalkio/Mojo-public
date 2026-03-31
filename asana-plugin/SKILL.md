---
name: asana-plugin
version: "1.0.1-CC"
platform: claude
description: |
  Full Asana workspace management for Duck & Shark / SteadyStars agents. Use for ANY
  Asana operation: creating tasks and subtasks, updating stages and fields, posting
  comments, searching by stage/user/project, managing dependencies, triaging backlogs,
  running daily checks, tracking work sessions, posting project status, managing
  the progress funnel, priority evaluation (Q-rank), inbox management, and workspace
  hygiene. Also use for agent identity setup, multi-agent coordination via Asana,
  and all workflows where human + agent activity intersects on tasks.

  Trigger on: any mention of tasks, projects, Asana, progress funnel, stage, what to
  work on next, what's blocked, sprint status, task creation, work tracking, or any
  question about what someone is or should be working on. If in doubt, trigger this skill.
---

# Asana Plugin — Master Entry (v2)

**Workspace:** `9526911872029`
**Primary connector:** `mcp__e785d4fd-60ad-4c55-a327-e92717407274__` — all task operations
**Batch connector:** `mcp__d7bbb126-b1b4-4b85-956d-319cc123dc1f__update_tasks` — bulk updates (up to 50)
**UI preview connector:** `mcp__d7bbb126-b1b4-4b85-956d-319cc123dc1f__` — visual previews only. Never use for agent logic or writes in production workflows.

**Skill router:** `skills/README.md`

---

## Always-Do (no file lookup needed)

1. **Before editing any existing task:** `task-prep` — read task + all stories first (`protocols/TASK-PREP.md`)
2. **All work maps to a task** — find or create one before starting work. If unclear, ask at a natural pause (not mid-thought). Users can say "off the books" to skip.
3. **Stage defaults:** `Unsorted` (backlog, incomplete fields OK) or `Todo` (requirements met, work not started)
4. **Assignment order:** Driver field first (no notification) → assignee last (Focus or Addressing only)
5. **Addressing tasks:** daily update required — prompt user or draft comment (`protocols/DAILY-UPDATE.md`)
6. **Comment quality:** no filler, no acknowledgements, no redundancy — value only
7. **@Mention format:** `https://app.asana.com/1/9526911872029/profile/{user_gid}` — paste as plain text, renders as chip
8. **Priority order when no task given:** Roadblocked → Addressing → Focus → Todo → Unsorted → Project priority → Q-rank
9. **Session end:** run `refresh-active-list` combo
10. **Notification awareness:** batch field updates, delay assignee, add followers deliberately (`protocols/NOTIFICATION-HYGIENE.md`)

---

## Agent Identity

**Two agent types:**
- **Company agents** — persistent, independent, operate in their own Asana identity at all times
- **Leashed agents** — bound to a primary human (their default user). When that human opens a thread, the leashed agent is the assumed identity unless overridden.

**Leashed agent defaults (D&S fleet):**
| Agent | Leashed to | Default for |
|-------|-----------|-------------|
| Caspera | Malkio | All Malkio threads |
| Cirra | Malkio | Backup / alternate |

**Detecting which agent to load (priority order):**
1. `UserPromptSubmit` hook — reads `CLAUDE_USER_PROMPT` for `/as:{handle}` token (explicit override)
2. Name at message start — "Hey Caspera...", "Caspera go..." → load `agent/caspera.env`
3. Default agent for authenticated user (from env file `DEFAULT_AGENT=true`)

**`/as:{handle}` override:**
```
/as:cirra review the SS Dev board
/as:koda create a subtask under 1213894695204112
```
Hook strips the token, loads `agent/{handle}.env`, injects identity. See `agent/INSTALL.md` §5.

**Dual-PAT model:**
- `AGENT_PAT` — default for all Asana operations (agent acts as itself)
- `USER_PAT` — switch ONLY when user explicitly asks the agent to act as them:
  - "Reply to that comment for me"
  - "Mark my task complete"
  - "Create this as me, not as you"

Never use `USER_PAT` autonomously. Always confirm with user if intent is ambiguous.

**Session start:** Load `agent/{handle}.env` → confirm identity → proceed.

---

## Primary Projects

| Name | GID | Default use |
|------|-----|-------------|
| SteadyStars Development | `1213243591510417` | Code/feature tasks |
| D&S Daily Tasks | `1209978806020366` | Day-to-day operations |
| Caspera / Agent Planning | `1213243591510428` | Agent directives, plugin planning |

Full index → `index/PROJECTS.md`

---

## Primary Players

| Name | GID | Role |
|------|-----|------|
| Malkio | `366935510972879` | CEO, final approver |
| Caspera | `1129617799923819` | PM/Ops agent |
| Po | `1207318683503049` | Agentic Engineer |
| Reggie | `1203982573237779` | QA + GHL Admin |
| Kay | `1213214598185193` | DevOps |

Full roster → `index/PLAYERS.md` (includes all humans + agents)

---

## Core Fields (always available on SS Dev)

| Field | GID | Type | Options |
|-------|-----|------|---------|
| Stage | `1189628845814528` | enum | `index/options/OPTIONS-core.md` |
| DoD Status | `1210940116708566` | enum | `index/options/OPTIONS-core.md` |
| Priority | `1103808807953314` | enum | `index/options/OPTIONS-core.md` |
| Working Status | `1162095947772596` | enum | `index/options/OPTIONS-work.md` |
| Component | `1213194483049635` | multi_enum | `index/options/OPTIONS-feature.md` |

For project-specific fields → `index/options/OPTIONS-[project].md`
For full field index → `index/FIELDS.md`

---

## Stage Flow

```
Unsorted → Todo → Focus → Addressing → Resolved
                                ↕            ↕
                          Roadblocked ←→ Reviewing
```

Gate rules + field dependency rules → `protocols/PROGRESS-FUNNEL.md`

**DoD Status = Ready ✔ is the gate TO enter Addressing — not the completion signal.**

---

## Safety Rules

- Single creates/updates: execute directly
- Bulk (3+ tasks), deletes, or irreversible changes: confirm with user first
- Never skip task-prep before mutating an existing task
- Never mark Resolved without verifying DoD = Ready + all subtasks complete
- Never overwrite a description without reading current content first

---

## Key Limitations (no MCP tool available)

- Cannot add custom fields to projects (UI only)
- Cannot update project metadata or overview (read via `asana_get_project`, write blocked)
- Cannot upload file attachments (read-only via `asana_get_attachments_for_object`)
- Cannot create/edit sections (UI only)
- No webhook support via MCP

Workaround for project overview writing: use `asana_create_project_status` (color=blue) as agent notes surface.
Future: browser-based skill for UI-only actions.

---

## Tests

All 12 behavioral tests completed. See `TEST-MATRIX.md` for full results and open items.
