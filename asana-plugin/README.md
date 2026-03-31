# Asana Plugin v1.0.1-CC

A fully decomposed, modular Asana management skill suite for Claude-based agents operating in the Duck & Shark / GNGE workspace. Part of the **Mojo Dojo** agent skill ecosystem.

---

## What This Is

A Claude Code plugin that gives agents full Asana operational capability: task creation, stage transitions, search, commenting, priority evaluation, dependency management, inbox processing, and workspace hygiene — all enforced against the D&S Progress Funnel SOP.

Built for both **persistent agents** (dedicated sessions with continuous identity) and **ephemeral agents** (spun up per-task, full context from cold).

**Platform:** Claude (CC) | Codex (CX) and Gemini (GM) ports planned
**Version:** 1.0.1-CC
**Workspace:** gnge.co (`9526911872029`)

---

## File Structure

```
asana-plugin/
├── SKILL.md                        # Master entry point — always loaded
├── README.md                       # This file
├── TEST-MATRIX.md                  # 12 behavioral tests + results
│
├── skills/
│   ├── README.md                   # Skill router table
│   ├── searching/SKILL.md          # All search patterns + stage filters
│   ├── creating/SKILL.md           # Task creation, field sequence, types
│   ├── updating/SKILL.md           # Field updates, description safety, batch ops
│   ├── commenting/SKILL.md         # Comments, @mentions, followers, Slack escalation
│   ├── structuring/SKILL.md        # Subtasks, dependencies, multihoming, hierarchy
│   ├── prioritizing/SKILL.md       # Q-rank evaluation and reassessment
│   ├── work-tracking/SKILL.md      # Session logs, task linkage, merge to Asana
│   ├── context-validate/SKILL.md   # NotebookLM + Google Drive context lookup
│   ├── maintenance/SKILL.md        # Index refresh, workspace hygiene
│   └── combos/
│       ├── SKILL.md                # All multi-step workflow patterns
│       └── project-audit.md        # Full project redundancy/dependency audit
│
├── protocols/
│   ├── PROGRESS-FUNNEL.md          # Stage definitions, gate rules, field dependencies
│   ├── TASK-PREP.md                # Read-before-write protocol
│   ├── NOTIFICATION-HYGIENE.md     # What triggers pings, assignee-last rule
│   ├── DAILY-UPDATE.md             # Update cadence by Q-rank, staleness handling
│   └── INBOX.md                    # Agent inbox polling and triage
│
├── index/                          # Workspace knowledge base (Anasa P0 layer)
│   ├── PLAYERS.md                  # All humans + agents with GIDs
│   ├── PROJECTS.md                 # All workspace projects with GIDs
│   ├── FIELDS.md                   # All custom field GIDs and option tables
│   └── options/
│       ├── OPTIONS-core.md         # Stage, Priority, DoD, Update Status (all projects)
│       ├── OPTIONS-work.md         # D&S Daily Tasks project fields
│       └── OPTIONS-feature.md      # SteadyStars Development project fields
│
├── agent/
│   ├── INSTALL.md                  # Setup guide, hooks spec, slash commands
│   └── CONTRIBUTIONS.md            # Agent session log (per-agent, accumulates over time)
│
├── evals/
│   └── evals.json                  # 5 behavioral evals (all passed)
│
├── scripts/
│   └── package_skill.py            # Builds distributable archive + manifest
│
└── dist/
    ├── asana-plugin-1.0.1-CC.tar.gz
    └── asana-plugin-1.0.1-CC-manifest.json
```

---

## Quick Start

### 1. Install

**Project-level (recommended):**
```bash
cp -r asana-plugin/ /path/to/your/project/.claude/skills/asana-plugin/
```

**Global (available in all Claude Code sessions):**
```bash
cp -r asana-plugin/ ~/.claude/skills/asana-plugin/
```

Register in `.claude/settings.json`:
```json
{
  "skills": ["asana-plugin"]
}
```

### 2. Configure Agent Identity

Create `asana-plugin/agent/{your-handle}.env`:
```
AGENT_GID=your_agent_gid
AGENT_HANDLE=@YourHandle
AGENT_EMAIL=your-agent@duckandshark.com
ASANA_PAT=your_agent_pat
USER_PAT=your_user_pat
WORKSPACE_GID=9526911872029
PRIMARY_PROJECT_GID=your_primary_project_gid
DEFAULT_AGENT=true
LEASHED_TO=user_gid
```

Add env files to `.gitignore` — **never commit PATs**.

### 3. Add to CLAUDE.md

```markdown
## Asana Plugin
Load `asana-plugin/SKILL.md` for any Asana operation.
Agent identity: read from `asana-plugin/agent/{handle}.env`.
```

### 4. Set Up Hooks (Optional but Recommended)

See `agent/INSTALL.md` section 4 for full hook specs. The two highest-value hooks:
- **PostToolUse** — auto-appends every Asana write to session work log
- **Stop** — merges work log to Asana Activity Log on session end (critical for ephemeral agents)

### 5. Register Slash Commands

Create files in `.claude/commands/`:
- `asana-start.md` → maps to `combos/agent-session-start`
- `asana-daily.md` → maps to `combos/daily-check`
- `asana-triage.md` → maps to `combos/task-triage`
- `asana-complete.md` → maps to `combos/task-complete`
- `asana-inbox.md` → maps to `combos/inbox-check`
- `asana-end.md` → maps to `combos/agent-session-end`

---

## Agent Identity Model

### Leashed Agents
Each agent is assigned to a primary human. Malkio's default agent is Caspera. When Malkio opens any Claude/Codex/Gemini thread, Caspera loads automatically — no command needed.

To use a different agent:
```
Hey Cirra, go check the SS Dev board...
/as:cirra review the Daily Tasks board
```

### Dual-PAT Operations
Each agent env carries both `AGENT_PAT` (agent acts as itself) and `USER_PAT` (agent acts as the leashed human). Default: all Asana operations use `AGENT_PAT`. Switch to `USER_PAT` only when the user explicitly requests actions on their behalf:
- "Respond to that comment for me"
- "Mark my task complete"
- "Create this as me, not as you"

---

## Progress Funnel

All task management follows the D&S Progress Funnel:

```
Unsorted → Todo → Focus → Addressing → Resolved
                              ↕
                          Roadblocked
```

Each stage has entry gates. Key rules:
- **DoD Status = Ready** required to enter Addressing
- **Driver field** set before Assignee (no inbox ping until Focus/Addressing)
- **Assignee** set last — triggers notification
- **Roadblocked** tasks still require daily micro-updates

See `protocols/PROGRESS-FUNNEL.md` for full gate rules.

---

## Known MCP Limitations

| Limitation | Workaround |
|---|---|
| `html_notes` rejects HTML via both connectors | Use `notes` (plain text) only. Direct REST for rich HTML. |
| No file attachment upload | URL links only via Reference link field. |
| `add_projects` + `custom_fields` non-atomic | Two sequential calls always. |
| `sections_any` + `projects_any` = UNION | Omit `projects_any` for section-scoped search. |
| Subtasks via `parent=` have empty `memberships` | Explicitly `add_projects` if board visibility needed. |

---

## MCP Connectors Required

| Connector ID | Purpose |
|---|---|
| `e785d4fd` | Primary — all Asana operations |
| `d7bbb126` | Batch `update_tasks` (up to 50), visual previews |

---

## Index Layer (Anasa P0)

The `index/` directory is a file-based workspace knowledge cache. It eliminates cold-start API calls. Refresh with:
```bash
# Manual refresh (uses maintenance skill)
# Run maintenance/update-projects-index, update-fields-index, update-players-index
```

This layer will be replaced by the Anasa API in P1. See `ANASA-PRD.md` for the full spec.

---

## Running Evals

```bash
# Evals are in evals/evals.json
# Run via Claude Code eval runner or manually against the skill
cat evals/evals.json
```

All 5 behavioral evals passed on 2026-03-30.

---

## Packaging

```bash
cd asana-plugin/
python scripts/package_skill.py
# Output: dist/asana-plugin-{version}.tar.gz + manifest.json
```

Platform variants use version suffix: `-CC` (Claude), `-CX` (Codex), `-GM` (Gemini).

---

## Roadmap

- **v1.1-CC** — index files auto-generated via `anasa refresh-all` CLI
- **v1.2-CC** — Anasa P1 API integration (replace file reads with `GET /agent-context`)
- **v1.x-CX** — Codex port
- **v1.x-GM** — Gemini port
- **v2.0** — Full Anasa integration, real-time inbox, cross-agent coordination surface

---

## Test Matrix Summary

| Test | Status | Finding |
|---|---|---|
| T1 — html_notes wrapping | ✅ | Plain text always wrapped in `<body>` |
| T2 — multihome + fields atomic | ⚠️ | Non-atomic — use two calls |
| T3 — batch field coverage | ✅ | name, custom_fields, followers, dates all work |
| T4 — file attachment create | ✅ | Not possible via MCP — UI only |
| T5 — wrong field error format | ✅ | Exact error strings documented |
| T6 — search filter union/intersect | ✅ | projects_any + sections_any = UNION |
| T7 — subtask project inheritance | ✅ | Subtasks do NOT inherit project membership |
| T8 — datetime UI render | ✅ | start_at/due_at renders with time in UI |
| T9 — start_on without due_on | ✅ | Fails with explicit error message |
| T10 — project field map via API | ✅ | Full field map via opt_fields |
| T11 — REST add field to project | ✅ | Endpoint exists, not in MCP |
| T12 — html_notes MCP transport | 🚫 | XML transport bug — HTML rejected |

See `TEST-MATRIX.md` for full details.
