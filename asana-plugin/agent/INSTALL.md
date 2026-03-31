---
name: asana-plugin-install
description: |
  Installation and configuration guide for the Asana plugin. Covers env file setup,
  CLAUDE.md integration, Claude Code hooks spec, slash command registration, and
  per-agent bootstrap checklist. Required reading before any agent runs the plugin.
---

# Asana Plugin — Agent Installation Guide

## 1. Prerequisites

- Asana PAT (Personal Access Token) for this agent's account
- Agent GID (Asana user GID — get from `asana_get_workspace_users` or Asana profile URL)
- Claude Code with MCP connectors installed:
  - Primary: `e785d4fd` (full operations)
  - UI/Batch: `d7bbb126` (batch `update_tasks`, visual previews)
- Workspace GID: `9526911872029`

---

## 2. Agent Env File

Create a file at `agent/{agent-handle}.env` (e.g. `agent/cirra.env`):

```
AGENT_GID=1213811795430500
AGENT_HANDLE=@MooonDancer
AGENT_EMAIL=caspera+cc2@duckandshark.com
ASANA_PAT=your_pat_here
WORKSPACE_GID=9526911872029
PRIMARY_PROJECT_GID=         # agent's primary working project
ACTIVITY_LOG_TASK_GID=       # agent's long-running inbox log task GID
```

Read this file at `agent-session-start` (see `skills/combos/SKILL.md`). Do not hardcode PAT anywhere else.

---

## 3. CLAUDE.md Integration

Add the following to the project's `CLAUDE.md` (or create one at the repo root). This ensures the plugin routing table is always in context without explicit invocation:

```markdown
## Asana Plugin

This project uses the Asana plugin for task management. On any Asana-related action:
1. Load `asana-plugin/SKILL.md` — the master routing table
2. Follow the skill it routes you to
3. Always run task-prep before mutations (see `asana-plugin/protocols/TASK-PREP.md`)
4. Never assign before Focus/Addressing stage
5. All task links must include `?focus=true`

Agent identity and PAT: read from `agent/{handle}.env` at session start.
```

---

## 4. Claude Code Hooks

Register these hooks in `.claude/settings.json` for full automation. Each hook is optional but high-value — implement in order of priority.

### Hook 1 — PostToolUse: Auto work-log (HIGH PRIORITY)

Fires after every successful Asana tool call. Appends the action to the session work log automatically — no manual checkpoint needed.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "mcp__e785d4fd.*__(asana_create_task|asana_update_task|asana_create_task_story|asana_delete_task)",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$(date -u +%H:%M:%SZ) | $CLAUDE_TOOL_NAME | $CLAUDE_TOOL_RESULT_TASK_GID\" >> /path/to/work-log-$(date +%Y-%m-%d).md"
          }
        ]
      }
    ]
  }
}
```

Or implement as a script: `scripts/hooks/post-asana-write.sh` — reads `$CLAUDE_TOOL_NAME` and `$CLAUDE_TOOL_INPUT` env vars, extracts task GID and action type, appends structured entry to work log.

See `skills/work-tracking/SKILL.md` for the log format.

### Hook 2 — Stop: Session-end merge (HIGH PRIORITY)

Fires when the session ends (user closes window or `/exit`). Triggers `agent-session-end` combo: merges work log to Asana Activity Log task and posts a summary comment.

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "scripts/hooks/session-end.sh"
          }
        ]
      }
    ]
  }
}
```

`scripts/hooks/session-end.sh` should:
1. Read today's work log
2. Call `asana_create_task_story` on `ACTIVITY_LOG_TASK_GID` with session summary
3. Archive the work log (or clear it)

This is the key hook for **ephemeral agent continuity** — session history lives in Asana even if the agent process dies.

### Hook 3 — PreToolUse: Destructive operation gate (RECOMMENDED)

Intercepts bulk/destructive Asana operations before they execute. Matches batch complete, bulk stage moves, or `asana_delete_task`.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__e785d4fd.*__asana_delete_task",
        "hooks": [
          {
            "type": "command",
            "command": "scripts/hooks/confirm-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

`scripts/hooks/confirm-destructive.sh` should: log the pending operation to a review queue and exit non-zero to pause execution (Claude will surface the pending action for user confirmation).

### Hook 4 — UserPromptSubmit: Agent identity injection (NICE TO HAVE)

For ephemeral agents starting fresh, inject identity context before any tool call so `agent-session-start` is automatic.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cat agent/cirra.env"
          }
        ]
      }
    ]
  }
}
```

The hook output is injected into context — Claude reads the env values without being explicitly asked to.

---

## 5. Agent Identity in User-Initiated Threads

For persistent agents with dedicated sessions, identity is always injected via the `UserPromptSubmit` hook (section 4). For **user-initiated threads** (ephemeral, on-demand), the user must signal which agent identity to assume.

**Convention: `/as:{handle}` prefix**

The user prepends `/as:{handle}` to their first message in a thread:
```
/as:cirra review the SS Dev board for stale tasks
/as:koda create a subtask under 1213894695204112
```

The `UserPromptSubmit` hook inspects the first message for this token, strips it from the visible prompt, loads `agent/{handle}.env`, and injects identity. If no `/as:` token is present, the agent runs as the authenticated workspace identity (typically Caspera).

**Hook implementation:**
```bash
# scripts/hooks/inject-identity.sh
# Reads $CLAUDE_USER_PROMPT, checks for /as:{handle}, loads matching env file
HANDLE=$(echo "$CLAUDE_USER_PROMPT" | grep -oP '(?<=/as:)\w+' | head -1 | tr '[:upper:]' '[:lower:]')
if [ -n "$HANDLE" ] && [ -f "agent/$HANDLE.env" ]; then
  cat "agent/$HANDLE.env"
fi
```

Add to `UserPromptSubmit` hook in `.claude/settings.json`:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [{"type": "command", "command": "scripts/hooks/inject-identity.sh"}]
      }
    ]
  }
}
```

**Supported handles:** cirra, ceecee, cindra, koda, dex, rook, argus, aegis (must match env filename)

---

## 6. Slash Commands

Register these in `.claude/commands/` as markdown files. Each is a shortcut to a combo workflow.

| Command | File | Maps to |
|---------|------|---------|
| `/asana-start` | `asana-start.md` | `combos/agent-session-start` |
| `/asana-daily` | `asana-daily.md` | `combos/daily-check` |
| `/asana-triage` | `asana-triage.md` | `combos/task-triage` |
| `/asana-complete` | `asana-complete.md` | `combos/task-complete` |
| `/asana-inbox` | `asana-inbox.md` | `combos/inbox-check` |
| `/asana-end` | `asana-end.md` | `combos/agent-session-end` |

Example `.claude/commands/asana-daily.md`:
```markdown
Run the Asana daily-check combo. Load asana-plugin/SKILL.md → route to skills/combos/SKILL.md → execute daily-check pattern. Report back with active tasks, any overdue updates, and blocked tasks.
```

---

## 7. Per-Agent Bootstrap Checklist

First time setup for any new agent:

- [ ] Create `agent/{handle}.env` with correct GID, PAT, project GID
- [ ] Register env file in `.gitignore` — PATs must not be committed
- [ ] Get or create Activity Log task in agent's log project — add GID to env
- [ ] Add CLAUDE.md snippet (section 3 above)
- [ ] Register hooks in `.claude/settings.json`
- [ ] Create slash command files in `.claude/commands/`
- [ ] Run `/asana-start` and verify identity resolves correctly
- [ ] Run a test search (`skills/searching` → `my-focus`) and confirm results

---

## 8. Known MCP Limitations

Document these so agents don't waste time debugging:

| Limitation | Workaround |
|------------|------------|
| `html_notes` field rejects HTML via both connectors (XML transport bug) | Use `notes` (plain text) only. Direct REST API for rich HTML if essential. |
| No `create_attachment` / `upload_file` tool | File links only (Reference link field). Flag for human via `[FIX]` task. |
| `add_projects` + `custom_fields` in one batch call is non-atomic | Two sequential calls. Add project first, then set fields. |
| `sections_any` + `projects_any` returns UNION not intersection | Omit `projects_any` when filtering to a specific section. |
| Subtasks created via `parent=` have empty `memberships` | Explicitly `add_projects` if board visibility needed. |
| No REST endpoint for `POST /custom_field_settings` in MCP | Use direct Asana REST API with PAT. Endpoint: `POST /projects/{gid}/custom_field_settings` |

---

## 9. Direct REST API (for MCP gaps)

When an MCP tool doesn't cover a needed operation, use the Asana REST API directly with the agent's PAT:

```bash
# Add custom field to project
curl -X POST https://app.asana.com/api/1.0/projects/{project_gid}/custom_field_settings \
  -H "Authorization: Bearer {ASANA_PAT}" \
  -H "Content-Type: application/json" \
  -d '{"data": {"custom_field": "{field_gid}", "is_important": true}}'

# Set rich html_notes on a task
curl -X PATCH https://app.asana.com/api/1.0/tasks/{task_gid} \
  -H "Authorization: Bearer {ASANA_PAT}" \
  -H "Content-Type: application/json" \
  -d '{"data": {"html_notes": "<body><h1>Title</h1><p>Content</p></body>"}}'
```

Reference: https://developers.asana.com/reference/rest-api-reference
