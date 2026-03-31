# Asana Plugin v2 — Test Matrix

Tests that must be run before finalizing skill behavior. Block on these before writing skills as confirmed.

**Status legend:** 🔲 Not run | ✅ Passed | ❌ Failed | ⚠️ Partial | 🚫 Blocked

---

## T1 — HTML format of `notes` vs `html_notes` on task read
**Status:** ✅ Passed
**Skill affected:** `skills/updating/SKILL.md` → description section
**Test:** Called `asana_get_task` on a task written in plain text in the Asana UI. Inspected `notes` and `html_notes`.
**Actual result:** Plain text `notes` returns as-is. `html_notes` wraps even plain text in a `<body>` tag (e.g., `<body>plain text here</body>`). Both fields always returned.
**Skill impact:** Confirmed: always read `html_notes` before deciding update method. If `html_notes` contains only `<body>` wrapper with plain text → safe to overwrite `notes`. If `html_notes` has richer tags → post comment instead.
**Tested:** 2026-03-30 | Cirra

---

## T2 — Multi-home + set fields in single batch call
**Status:** ⚠️ Partial
**Skill affected:** `skills/structuring/multihome-task.md`, `skills/updating/SKILL.md`
**Test:** Used `update_tasks` to add task `1213894695204112` to test board AND set Stage custom field in same call. Field GID was valid but enum value was from SS Dev (not test board context). Call failed on `custom_fields` but `add_projects` **succeeded**.
**Actual result:** Partial execution confirmed — `add_projects` processed independently. Field set failed because enum value GID was wrong for that context. The batch connector does **not** roll back atomically. Project was added even though field failed.
**Skill impact:** ⚠️ Two sequential calls required for multihome + field-set. Do NOT combine in one call — if field op fails, the project add already happened and you're left in a partial state with no clean rollback. Pattern: (1) add_projects, (2) verify membership, (3) set fields.
**Tested:** 2026-03-31 | Cirra

---

## T3 — Batch `update_tasks` — verify supported fields
**Status:** ✅ Passed
**Skill affected:** `skills/updating/SKILL.md`, `skills/combos/SKILL.md`
**Test:** Ran `update_tasks` on task `1213894695204112` with: name change, custom_fields (Stage + Priority), add_followers, due_on, start_on.
**Actual result:** All fields updated in one call. `succeeded` array confirmed. Verified via `asana_get_task` — Stage=Todo, Priority=Q4, follower added, due_on/start_on set correctly.
**Skill impact:** Batch update supports: name, custom_fields, add_followers, remove_followers, due_on, start_on, completed, assignee, add_projects, remove_projects, add_dependencies, remove_dependencies, html_notes (see T12 caveat). Use freely for bulk field updates.
**Tested:** 2026-03-31 | Cirra

---

## T4 — File attachments — confirm no create capability
**Status:** ✅ Passed (confirmed absence)
**Skill affected:** `skills/creating/SKILL.md` (attachment note)
**Test:** Searched all available tools in both MCP connectors (`e785d4fd` and `d7bbb126`) for any `create_attachment`, `upload_file`, or similar tool.
**Actual result:** No such tool exists in either connector. Only `asana_get_attachment` (by GID) and `asana_get_attachments_for_object` (list). Both read-only.
**Skill impact:** Confirmed UI-only limitation. Document clearly: agents cannot attach files. If attachment needed, create a task comment noting "attachment required" and assign to human, or use Reference link custom field for URLs.
**Tested:** 2026-03-31 | Cirra

---

## T5 — Custom field on wrong project — exact error format
**Status:** ✅ Passed
**Skill affected:** `skills/creating/SKILL.md`, `skills/updating/SKILL.md`
**Test:** Attempted to set a custom field GID from SS Dev on a task in a context where that field wasn't valid.
**Actual result:** Exact error: `"Custom field with ID {gid} is not on given object"` (via `asana_create_task`) and `"enum_value: Unknown object: {gid}"` (via `update_tasks` batch connector with wrong option GID).
**Skill impact:** Two error patterns to match on recovery:
  1. `"Custom field with ID"` + `"is not on given object"` → field not on project
  2. `"enum_value: Unknown object"` → option GID not valid for this field
Recovery: fetch task's current project memberships → get correct field GIDs for each project → retry with correct values.
**Tested:** 2026-03-30 | Cirra

---

## T6 — `asana_search_tasks` — `projects_any` + `sections_any` behavior
**Status:** ✅ Passed (confirmed from tool documentation)
**Skill affected:** `skills/searching/SKILL.md`
**Test:** Reviewed `asana_search_tasks` tool description which explicitly documents this behavior.
**Actual result:** UNION behavior confirmed. Tool docs state: "If you specify projects_any and sections_any, you will receive tasks for the project AND tasks for the section." Additionally: "If you're looking for only tasks in a section, omit the projects_any from the request."
**Skill impact:** Never use `projects_any` + `sections_any` together when trying to filter to a specific section within a project — you'll get all tasks from both, not the intersection. For section-scoped searches, use `sections_any` alone.
**Tested:** 2026-03-31 | Cirra

---

## T7 — Subtask field inheritance
**Status:** ✅ Passed (with important nuance)
**Skill affected:** `skills/creating/SKILL.md`, `skills/structuring/SKILL.md`
**Test:** Created subtask via `parent` param only (no `project_id`). Inspected `memberships` and `custom_fields` on created subtask GID `1213865829428615`.
**Actual result:**
  - `memberships: []` — subtask does **NOT** inherit parent's project membership
  - `projects: []` — not a member of any project
  - `custom_fields` array is fully populated with all workspace-level fields (Priority, Stage, DoD Status, etc.) — fields are accessible but inherited from workspace field definitions, not project membership
  - `permalink_url` correctly routes to parent's project for UI display
**Skill impact:** Subtasks created via `parent` only are orphaned from projects. If you need a subtask to appear in project board views or be searchable by project, explicitly add it to the project via `add_projects`. Fields can still be set on orphaned subtasks (workspace-level fields work), but project search filters won't find them. Document: "subtask-only creation = workspace-visible but project-invisible."
**Tested:** 2026-03-31 | Cirra

---

## T8 — `start_at` / `due_at` datetime display in Asana UI
**Status:** ✅ Passed (API + UI confirmed)
**Skill affected:** `skills/creating/SKILL.md`, `skills/updating/SKILL.md`
**Test:** Created task with `start_at: "2026-04-01T09:00:00Z"` and `due_at: "2026-04-04T17:00:00Z"`. Malkio confirmed in Asana UI.
**Actual result:** API accepted both fields. Time component renders correctly in Asana UI (shows e.g. "Mar 30, 5am – Apr 4, 1pm"). Both datetime and date-only variants work.
**Bonus finding:** Task links in descriptions/comments should always include `?focus=true` suffix (e.g. `https://app.asana.com/1/.../task/{gid}?focus=true`). Malkio flagged that the T8 subtask description was missing this — confirmed UX improvement.
**Skill impact:** `start_at`/`due_at` confirmed safe for time-specific deadlines. Use when time of day matters; use `start_on`/`due_on` for date-only. Always append `?focus=true` to all Asana task links in descriptions and comments.
**Tested:** 2026-03-30 API | 2026-03-31 UI confirmed by Malkio

---

## T9 — Batch `update_tasks` — `start_on` without `due_on`
**Status:** ✅ Passed
**Skill affected:** `skills/updating/SKILL.md`
**Test:** Sent `update_tasks` with `start_on` set but no `due_on`.
**Actual result:** Failed with exact error: `"You must provide 'due_on' or 'due_at' when setting 'start_on'."`
**Skill impact:** Enforced at API level. Rule: never set `start_on` or `start_at` without also providing `due_on` or `due_at`. Applies to both single updates and batch. Always pair start/due dates.
**Tested:** 2026-03-30 | Cirra

---

## T10 — `asana_get_project` returns `custom_field_settings`
**Status:** ✅ Passed
**Skill affected:** `skills/maintenance/SKILL.md`, `skills/updating/SKILL.md`
**Test:** Called `asana_get_project` on SS Dev (`1213243591510417`) with `opt_fields="custom_field_settings,custom_field_settings.custom_field,custom_field_settings.custom_field.name,custom_field_settings.custom_field.gid,custom_field_settings.custom_field.type,custom_field_settings.custom_field.enum_options"`.
**Actual result:** Full field map returned — 15 custom fields with all GIDs, types, and enum option GIDs. This is the authoritative way to build `OPTIONS-*.md` files without manual lookup.
**Skill impact:** `update-fields-index` and `update-options` maintenance routines should use this call as their primary data source. No need for manual GID lookup — one call per project gives you everything.
**Tested:** 2026-03-30 | Cirra

---

## T11 — Adding custom fields to projects via Asana REST API
**Status:** ✅ Confirmed (API endpoint exists; not in MCP)
**Skill affected:** `skills/maintenance/SKILL.md`
**Test:** Searched Asana developer docs for POST endpoint to add custom fields to projects.
**Actual result:** Endpoint confirmed: `POST /projects/{project_gid}/custom_field_settings`. Documented at https://developers.asana.com/reference/addcustomfieldsettingforproject. Requires PAT with appropriate permissions. Body: `{ "data": { "custom_field": "{field_gid}", "is_important": true } }`.
**Skill impact:** Not exposed in current MCP tools. Two paths: (1) flag for human via `[FIX]` task as before, OR (2) add direct REST API call capability to maintenance skill using `requests` / `fetch` with PAT from agent env file. This is a **secondary update** candidate — document the endpoint for future direct-API skill extension.
**Tested:** 2026-03-31 | Cirra

---

## T12 — Description update: does setting `notes` strip `html_notes` formatting?
**Status:** 🚫 Blocked — MCP transport bug | ✅ Assumption confirmed (treat as known)
**Skill affected:** `skills/updating/SKILL.md` → description section
**Test:** Attempted to create task with rich `html_notes` via both `asana_update_task` (e785d4fd connector) and `update_tasks` (d7bbb126 connector) to set up test state.
**Actual result:** Both connectors reject any `html_notes` containing HTML tags with error: `"XML is invalid"`. The MCP transport layer serializes tool calls as XML — embedded HTML tags break the XML parser regardless of content complexity. Even `<body><p>text</p></body>` fails.
**Root cause:** MCP XML transport layer conflict with HTML content in string fields.
**Working assumption (pending Po's manual REST confirmation):** Based on T1 (Asana always wraps notes in html_notes), updating `notes` on a task with rich human-written html_notes destroys formatting — the write replaces the entire html_notes value with a plain-text body wrapper. Treat as confirmed until Po reports otherwise via manual REST test (task `1213865829505174` prepped).
**Skill impact:** Agents must use `notes` (plain text) only for description writes via MCP. If task has existing rich html_notes, never overwrite — post a comment instead. The "read html_notes first" safety rule is critical: agents cannot recreate rich formatting via MCP, so any overwrite is irreversible.
**Tested:** 2026-03-31 | Cirra | ⚠️ Po to confirm via REST test

---

## Post-Test Updates

After running each test, update this file with:
- Status (✅/❌/⚠️/🚫)
- Actual result
- Any skill file changes required
- Date tested and who ran it

---

## Test Task GIDs (to clean up)

| GID | Name | Board |
|-----|------|-------|
| `1213866653502116` | T1 test task | Test Automation Results |
| `1213867004520738` | T5 test task | Test Automation Results |
| `1213865418600059` | T8 test task | Test Automation Results |
| `1213865418556444` | T9 test task | Test Automation Results |
| `1213894695204112` | T2/T3 multihome source (also on SS Dev) | SS Dev + Test Automation Results |
| `1213865829428615` | T7 subtask (child of T2/T3 task) | orphaned |
| `1213865829505174` | T12 test task | Test Automation Results |
| `1213866652787699` | Eval 2 task | D&S Daily Tasks |
| `1213863388525043` | Eval 5 task | SS Dev |
