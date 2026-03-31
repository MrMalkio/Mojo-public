---
name: asana-project-audit
description: |
  Full project audit combo: scans all tasks in a project for redundancy, duplicates,
  missing dependencies, structural gaps, and description quality issues. Produces a
  shared artifact (HTML report) as a live progress tracker that any agent or human
  can work from. Generates an action plan with proposed new tasks, restructures,
  subtask decompositions, and dependency wiring. Designed for multi-agent collaboration
  — the artifact is the coordination surface, not a one-time report.
  Trigger: "audit [project]", "clean up [project]", "find duplicates in [project]",
  "review task structure", "project hygiene".
---

# Combo: project-audit

**Purpose:** Deep structural analysis of a project — surface redundancy, gaps, and dependency debt, then execute improvements with human sign-off.

**Artifact:** Live HTML progress tracker (shared across agents and humans)
**Duration:** Multi-session capable — artifact persists between sessions
**Multi-agent:** Yes — any agent can pick up from the artifact and continue

---

## Phase 1 — Intake & Full Scan

### 1.1 Load project context
```
asana_get_project(project_id="{project_gid}", opt_fields="name,sections,custom_field_settings")
asana_get_project_sections(project_id="{project_gid}")
```

### 1.2 Pull all tasks (not just active)
```
asana_search_tasks({
  workspace: "9526911872029",
  projects_any: "{project_gid}",
  completed: false,
  opt_fields: "name,notes,html_notes,assignee,custom_fields,parent,dependencies,dependents,memberships,subtasks,created_at,modified_at",
  limit: 100
})
```
Paginate until exhausted. Include completed tasks if audit scope includes resolved work.

### 1.3 Pull subtask details
For every task with subtasks, call `asana_get_task` to get subtask names and fields. Build a flat list of all tasks + subtask relationships.

---

## Phase 2 — Analysis

Run all analysis passes on the collected task set. Flag issues by category.

### 2.1 Duplicate detection
- **Name similarity:** Tasks with names > 80% similar (case-insensitive, strip prefixes like [SOLVE][BUILD])
- **Description overlap:** Tasks whose notes share significant content (same problem statement, same artifact link)
- **Same assignee + same stage + similar name:** High confidence duplicate
- Flag as: `DUP-CANDIDATE` with confidence level (high/medium/low)

### 2.2 Redundancy
- Multiple tasks describing the same goal at different granularities (should be parent/subtask relationship instead)
- Tasks that are clearly subtasks of another task but exist as top-level tasks
- Flag as: `SHOULD-BE-SUBTASK` or `SHOULD-BE-PARENT`

### 2.3 Missing dependencies
- Tasks in Addressing with no dependencies that reference other tasks in their description (e.g. "after X is done") — dependency not wired
- Tasks in Roadblocked with no active dependency set — inconsistent state
- Sequences implied by names (e.g. "Phase 1 / Phase 2 / Phase 3") with no dependency chain
- Flag as: `MISSING-DEPENDENCY`

### 2.4 Structural gaps
- Tasks in Addressing with no Driver set
- Tasks in Focus/Addressing with no due date
- Tasks with empty descriptions (notes = null or < 20 chars)
- Tasks in Unsorted for > 48h with no Priority or Stage advancement
- Tasks with subtasks that have no parent stage consistency
- Flag as: `STRUCTURAL-GAP` with specific violation

### 2.5 Description quality
- Tasks with descriptions that are too long to be actionable (> 800 chars) and have no subtasks — candidate for decomposition
- Tasks with descriptions that are a copy-paste of another task — possible duplicate
- Tasks missing a clear Definition of Done statement
- Flag as: `DESC-QUALITY`

---

## Phase 3 — Build the Artifact

Generate a single-file HTML artifact as the audit workspace. This is the coordination surface — not a static report.

### Artifact structure:

```html
<!-- asana-audit-{project-slug}-{date}.html -->
```

**Sections:**
1. **Summary** — project name, task count, issue count by category, last updated timestamp, which agent last touched it
2. **Issues Table** — sortable by category / confidence / task GID. Each row: task name (linked with ?focus=true), issue type, proposed action, status (pending / approved / done / skipped)
3. **Action Plan** — ordered list of proposed changes grouped by type:
   - Merges (DUP candidates)
   - Restructures (parent/subtask promotions)
   - Dependency wiring
   - Field fixes (Driver, due date, Priority)
   - New tasks to create (decompositions, missing gaps)
4. **Progress tracker** — each action item has a checkbox. Checked = done. Any agent reads this to know what's been executed and what's left.
5. **Agent log** — append-only list of which agent took which action, with timestamp and task GID

### Artifact rules:
- **Never delete this file between sessions.** It is the shared state.
- Any agent picking up the audit reads the artifact first, continues from where the last agent stopped.
- Human can open the artifact in browser, check/uncheck items, add notes. Agent reads their changes on next session.
- Store at: `audits/asana-audit-{project-slug}-{date}.html` relative to the agent's current workspace folder. Create `audits/` if it doesn't exist. Ask the user for their workspace path if unknown.

---

## Phase 4 — Present Options (Human Sign-off)

Before executing any changes, present the action plan to the user:

```
AUDIT COMPLETE — {project_name}

Found {n} issues:
  {x} duplicate candidates (high confidence: {h}, medium: {m})
  {x} redundancy / structural issues
  {x} missing dependencies
  {x} field/stage violations
  {x} description quality issues

Proposed actions:
  Merge {n} task pairs
  Rewire {n} dependencies
  Fix {n} field violations
  Decompose {n} tasks into subtasks
  Create {n} new linking/gap tasks

[Artifact: asana-audit-{project-slug}-{date}.html]

Approve all / approve by category / review each / skip to [category]?
```

**Do not execute any changes until the user approves.** This is a safety gate — this combo touches potentially many tasks.

---

## Phase 5 — Execute (with artifact as progress tracker)

Work through the approved action plan in order. For each item:

1. Mark item as `in_progress` in artifact
2. Execute the Asana operation (update, create, set dependency, etc.)
3. Mark item as `done` in artifact with task GID and timestamp
4. Append to agent log

**Execution order (minimize notification noise):**
1. Field fixes first (no notifications for custom field changes)
2. Dependency wiring (structural, low notification impact)
3. Subtask creation and parent assignments
4. Task merges (create merged task → move subtasks → mark originals Resolved)
5. New task creation last (triggers notifications)

**Batching:** Use `update_tasks` (UI connector) for field fixes — batch up to 50. Single operations for structural changes.

---

## Phase 6 — Handoff

When session ends before audit is complete:

1. Update artifact: mark current item as `paused`, add agent name and timestamp
2. Post comment on project (via `asana_create_project_status`) summarizing progress:
   ```
   Audit in progress — {n}/{total} items completed.
   Artifact: [link to HTML file]
   Next: {next action item description}
   Any agent can continue from the artifact.
   ```
3. Log in agent CONTRIBUTIONS.md: audit started, artifact path, items completed/remaining

**Resuming (any agent):**
1. Read artifact — check agent log and progress tracker for current state
2. Find first unchecked `approved` item
3. Continue from there

---

## Multi-Agent Coordination Notes

- The artifact is the single source of truth. Do not re-run Phase 1–3 if an artifact already exists for this project + date.
- If another agent is actively working the artifact (check agent log timestamp < 30 min ago), post a comment on the artifact task and wait rather than colliding.
- Agents from different platforms (CC/CX/GM) can all use the same artifact — it's HTML, platform-agnostic.
- For cross-agent dependency decisions (e.g. "should task A depend on task B?"), post the question as a comment on the relevant task rather than making unilateral structural changes.

---

## Tool Sequence Reference

```
# Phase 1
asana_get_project → asana_get_project_sections → asana_search_tasks (paginated) → asana_get_task (for subtasks)

# Phase 3
Write artifact to audits/ in the agent's workspace folder

# Phase 5 — field fixes
update_tasks (batch, UI connector)

# Phase 5 — dependencies
asana_set_task_dependencies / asana_set_task_dependents

# Phase 5 — subtask restructure
asana_set_parent_for_task

# Phase 5 — new tasks
asana_create_task (individually) → update_tasks (batch field set)

# Phase 5 — merges
asana_create_task (merged) → asana_set_parent_for_task (move subtasks) → update_tasks (Resolved on originals)

# Phase 6
asana_create_project_status (handoff comment)
```
