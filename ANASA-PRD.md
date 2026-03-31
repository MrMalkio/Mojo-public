# Anasa — Product Requirements Document
**Version:** 0.1 (P0–P1 Scope)
**Status:** Draft — for Anasa building agents
**Owner:** Malkio / Duck & Shark
**Date:** 2026-03-31
**Source session:** `/sessions/adoring-intelligent-dirac/mnt/.claude/projects/-sessions-adoring-intelligent-dirac/cff2585b-af05-4b82-a46c-8a3064f1c9d3.jsonl`

---

## 1. What Is Anasa

Anasa is the persistent-state, agent-facing management layer that sits between the D&S agent fleet and Asana. It is NOT a replacement for Asana — it is a mirror, cache, and intelligence layer that makes Asana usable by agents at the speed and reliability that multi-agent workflows require.

The current state (P0) is a file-based approximation: static index files (`PLAYERS.md`, `PROJECTS.md`, `FIELDS.md`, `OPTIONS-*.md`) that agents load at session start. These files are manually maintained, go stale, and require API calls to refresh. Anasa replaces them with a live, queryable system.

---

## 2. The Problem Anasa Solves

### 2.1 Agent Cold-Start Cost
Every time an ephemeral agent starts a session, it must make 3–6 Asana API calls just to resolve basic facts: "What's the GID for the Stage field's 'Focus' option on SS Dev?" This data never changes. Without a cache, every session pays this cost. With many agents running, this compounds into latency and rate-limit pressure.

### 2.2 Stale Context
The file-based index layer goes stale the moment a project is created, a field is added, or a player joins the workspace. Agents operating on stale data make wrong decisions — wrong field GIDs, missing projects, unrecognized players.

### 2.3 Agent Activity Is Invisible
There is no system-level record of what agents have done across sessions. CONTRIBUTIONS.md is per-agent and manually maintained. There is no cross-agent view of "what has been touched, by whom, when."

### 2.4 No Agent-Scoped Inbox
Agents need to poll multiple Asana endpoints to simulate an inbox (followed tasks, @mentions, project status). This is expensive and incomplete. Anasa should maintain a real-time per-agent inbox derived from webhook events.

### 2.5 No Workspace Knowledge Graph
Dependencies, blockers, player load, and project health exist in Asana but cannot be queried as a graph. Agents need to make many API calls to reconstruct relationships that should be pre-computed.

---

## 3. Core Architecture

```
Asana (source of truth)
    │
    ├── Webhooks (real-time event stream)
    │
    ▼
Anasa (mirror + intelligence layer)
    ├── Postgres DB (persistent state)
    ├── REST API (agent-facing)
    ├── WebSocket (real-time push to agents)
    └── File snapshot generator (for offline/fallback)
    │
    ▼
Agent Fleet (consumers)
    ├── Caspera (Claude)
    ├── Cirra, CeeCee, Cindra (Claude)
    ├── Koda, Dex, Rook (Codex)
    └── Argus, Aegis (Gemini)
```

---

## 4. P0 — Bootstrap (File-Based, No Server)

**Goal:** Make the current static index files auto-generated and auto-refreshed. No server required.

### P0 Deliverables

**4.1 Maintenance Scripts**
CLI scripts (Python) that call Asana API and write/update index files:
- `anasa refresh-projects` → writes `index/PROJECTS.md`
- `anasa refresh-fields` → writes `index/FIELDS.md` + all `OPTIONS-*.md`
- `anasa refresh-players` → writes `index/PLAYERS.md`
- `anasa refresh-all` → all of the above in sequence

**4.2 Scheduled Refresh**
Run `anasa refresh-all` on a schedule (daily or on workspace change). Can use the existing `schedule` skill/plugin.

**4.3 Format Contract**
The file format for all index files must be frozen at P0. P1 will serve the same data via API — agents should need zero code changes to switch from file-based to API-based loading.

---

## 5. P1 — Core Server

**Goal:** Replace file reads with API calls. Single bootstrap endpoint. Real-time agent inbox via webhooks.

### 5.1 Data Model

**Projects table**
```sql
projects (
  gid TEXT PRIMARY KEY,
  name TEXT,
  slug TEXT,
  team_gid TEXT,
  owner_gid TEXT,
  archived BOOLEAN,
  sections JSONB,           -- [{gid, name}]
  custom_field_gids TEXT[], -- field GIDs on this project
  last_synced_at TIMESTAMPTZ
)
```

**Fields table**
```sql
fields (
  gid TEXT PRIMARY KEY,
  name TEXT,
  type TEXT,                -- enum, multi_enum, text, number, people
  options JSONB,            -- [{gid, name, color}] for enum types
  projects TEXT[],          -- which project GIDs this field appears on
  last_synced_at TIMESTAMPTZ
)
```

**Players table**
```sql
players (
  gid TEXT PRIMARY KEY,
  name TEXT,
  handle TEXT,
  email TEXT,
  type TEXT,                -- human | agent
  platform TEXT,            -- claude | codex | gemini | null
  default_user_gid TEXT,    -- for agents: the human they're leashed to
  managed_by TEXT[],        -- for agents: human GIDs who manage them
  active_project_gids TEXT[],
  last_active_at TIMESTAMPTZ
)
```

**Agent activity log**
```sql
agent_activity (
  id SERIAL PRIMARY KEY,
  agent_gid TEXT,
  session_id TEXT,
  action_type TEXT,         -- create_task | update_task | comment | complete | etc.
  task_gid TEXT,
  project_gid TEXT,
  payload JSONB,            -- full action details
  created_at TIMESTAMPTZ
)
```

**Agent inbox**
```sql
agent_inbox (
  id SERIAL PRIMARY KEY,
  agent_gid TEXT,
  event_type TEXT,          -- mention | assignment | follower_update | dependency_cleared | etc.
  task_gid TEXT,
  from_gid TEXT,
  payload JSONB,
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ
)
```

### 5.2 API Endpoints

**Bootstrap (most critical — replaces all 7 index files)**
```
GET /agent-context?agent_gid={gid}
```
Returns single JSON blob: identity, managed projects, all field GIDs + options for those projects, teammates, open inbox items. One call at session start.

**Projects**
```
GET /projects                          -- all active projects
GET /projects/{gid}                    -- single project with sections + fields
GET /projects/{gid}/fields             -- field map for this project
```

**Fields**
```
GET /fields                            -- all workspace fields
GET /fields/{gid}/options              -- options for a specific field
GET /fields/options?project={gid}      -- all option GIDs scoped to a project
```

**Players**
```
GET /players                           -- all humans + agents
GET /players/{gid}                     -- single player with load + recent activity
GET /players?type=agent                -- agents only
GET /players?managed_by={user_gid}     -- agents managed by a specific human
```

**Agent Inbox**
```
GET /inbox?agent_gid={gid}&unread=true
PATCH /inbox/{id}/read
```

**Agent Activity**
```
POST /activity                         -- agent logs an action
GET /activity?agent_gid={gid}&since={date}
GET /activity?task_gid={gid}           -- all agent activity on a task
```

**Workspace Snapshot (for fallback file generation)**
```
GET /snapshot?format=markdown          -- returns current index files as text
GET /snapshot?format=json              -- machine-readable
```

### 5.3 Webhook Consumer

Subscribe to Asana webhook events for the workspace. On each event:
- Update relevant Postgres tables (project changed, task created, user added, field modified)
- Evaluate which agents have inbox subscriptions affected → write to `agent_inbox`
- Invalidate any cached snapshots

**Event types to handle:**
- `task.created` / `task.deleted` / `task.changed`
- `project.created` / `project.deleted` / `project.changed`
- `story.created` (comments, @mentions)
- `task.assigned` / `task.unassigned`
- `task.dependency_added` / `task.dependency_removed`

---

## 6. What Anasa Requests of Building Agents

The following are explicit requirements that Anasa must satisfy for the Asana plugin (and its successors) to upgrade cleanly from file-based to API-based operation:

### 6.1 Frozen format contract
The `GET /agent-context` response must be a superset of what the 7 current index files contain. Agents should be able to map response fields 1:1 to current file content. No format breaks without a versioned migration path.

### 6.2 Single bootstrap call
`GET /agent-context?agent_gid={gid}` must return everything an agent needs for a full session: identity, projects, fields+options (scoped to agent's projects), players, open inbox. Target response time: < 500ms. This replaces the current 3–6 cold-start API calls and all 7 file reads.

### 6.3 Per-agent inbox
Each agent must have a queryable inbox derived from webhook events. The inbox must support filtering by `unread`, `event_type`, and `task_gid`. Agents mark items read after processing.

### 6.4 Activity logging endpoint
`POST /activity` must accept an action log entry from any agent at any time. This is how CONTRIBUTIONS.md gets replaced — agents write to Anasa instead of a local file.

### 6.5 Offline/fallback snapshot
`GET /snapshot?format=markdown` must regenerate the 7 current index files on demand. Agents that cannot reach Anasa fall back to the last-generated snapshot files.

### 6.6 Dual-PAT support in player record
Each agent player record must store both `AGENT_PAT` and `USER_PAT` (the PAT of the human they're leashed to). Anasa must expose which PAT to use for a given operation type without the agent needing to decide.

### 6.7 No breaking changes to file format at P1
When Anasa launches, the 7 index files still exist as fallback. Anasa's snapshot endpoint writes files in identical format. Agents switching from file→API see zero behavior change.

---

## 7. The 7 Index Files → Anasa Mapping

| Current File | Anasa Endpoint | Notes |
|---|---|---|
| `index/PLAYERS.md` | `GET /players` | Add load, last_active, managed_by |
| `index/PROJECTS.md` | `GET /projects` | Add section GIDs, active task count |
| `index/FIELDS.md` | `GET /fields` | Add per-project membership |
| `index/options/OPTIONS-core.md` | `GET /fields/options?project=all` | Core = workspace-level |
| `index/options/OPTIONS-work.md` | `GET /fields/options?project=1209978806020366` | D&S Daily Tasks |
| `index/options/OPTIONS-feature.md` | `GET /fields/options?project=1213243591510417` | SS Dev |
| `agent/CONTRIBUTIONS.md` | `GET /activity?agent_gid={gid}` | Append-only, all sessions |

All 7 replaced by `GET /agent-context?agent_gid={gid}` at session start in P1.

---

## 8. Out of Scope (P0–P1)

- UI / dashboard
- Natural language query interface
- Cross-workspace federation
- Billing / multi-tenant
- Asana write operations (Anasa is read/mirror only — writes still go direct to Asana via MCP)
- Replacing the Asana plugin's operational skills (search, create, update, etc.)

---

## 9. Success Criteria

**P0:** `anasa refresh-all` runs without error and produces all 7 index files with accurate, current data. Agent cold-start API call count drops to 0 (all data read from files).

**P1:** `GET /agent-context` returns in < 500ms. Agent inbox receives events within 60s of Asana webhook firing. Zero cold-start API calls. Agent activity logged to Anasa on every session.

---

## 10. Open Questions for Building Agents

1. Postgres or SQLite for P1? (SQLite is simpler for a single-node first version)
2. Webhook registration: does Anasa register its own Asana webhook, or does an existing webhook infrastructure forward events?
3. Auth: does Anasa use workspace-level service account, or does each agent authenticate independently?
4. How does Anasa handle agents from different platforms (Claude/Codex/Gemini) — single endpoint or platform-specific?
5. Rate limiting: Anasa must respect Asana API rate limits during initial sync. Backoff strategy?
