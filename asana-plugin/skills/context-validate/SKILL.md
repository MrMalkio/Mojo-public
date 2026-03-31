---
name: context-validate
description: |
  Query organizational knowledge sources (NotebookLM, Google Drive) to retrieve
  context before decomposing tasks, writing descriptions, or making decisions that
  depend on internal documentation. Use when a task has a thin description but a
  known brief or transcript exists, when decomposing a complex task and richer context
  may be in a notebook or doc, or when an agent is about to make assumptions that
  could be answered by internal knowledge. Reference this skill from task-intake,
  task-decompose, and task-triage whenever context might be missing.
---

# Context Validation — NotebookLM + Google Drive

This skill is a bridge to organizational knowledge. It is **not Asana-specific** but is regularly invoked during Asana workflows when task context is incomplete.

---

## When to Use

- Task description is thin but a transcript link, feature brief, PRD, or design doc is referenced or known to exist
- Decomposing a complex task and the full scope isn't obvious from what's in Asana
- Triaging a task and the agent doesn't have enough context to classify it without guessing
- Any time the agent is about to make an assumption that internal documentation could resolve

Don't query NotebookLM or Google Drive speculatively. Know what you're looking for first.

---

## NotebookLM

**Available tools:** `mcp__notebooklm__notebook_query`, `mcp__notebooklm__notebook_list`, `mcp__notebooklm__notebook_get`

```
// Find the right notebook
mcp__notebooklm__notebook_list({})  // list available notebooks
→ Identify the notebook relevant to the project or domain

// Query it
mcp__notebooklm__notebook_query({
  notebook_id: "{notebook_id}",
  query: "What is the Definition of Done for [task name/concept]?"
})
```

Match the notebook to the project or domain. Don't query a general notebook when a project-specific one exists.

**After querying:** Present findings to the relevant stakeholder for validation before writing them into the task — especially if the answer is being used to fill in a DoD, set scope, or make a structural decision. This is non-negotiable for externally-sourced information (web research).

---

## Google Drive

**Available tools:** `mcp__c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75__google_drive_search`, `mcp__c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75__google_drive_fetch`

```
// Search for the relevant doc
mcp__c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75__google_drive_search({
  query: "[project name] brief OR PRD OR spec"
})

// Fetch it
mcp__c1fc4002-5f49-5f9d-a4e5-93c4ef5d6a75__google_drive_fetch({
  document_url: "{doc_url}"
})
```

---

## Validation Before Writing to Asana

Context retrieved from internal sources (NotebookLM, Google Drive) should be presented to the relevant stakeholder before being written into a task description, subtask structure, or DoD.

Context retrieved from external sources (web research, public docs) **must always** be presented for validation before writing to any task. Mark it clearly: "I found this externally — please confirm before I add it."

The waiting-for-context pattern (see `skills/commenting/SKILL.md`) handles cases where the agent posts a comment requesting validation and then waits for a response.

---

## Notebook-to-Project Mapping

When this skill becomes established, maintain a mapping in `index/PROJECTS.md` or a separate `index/NOTEBOOKS.md`:

```
| Project GID | Relevant NotebookLM ID | Relevant Drive Folder |
|-------------|------------------------|----------------------|
| 1213243591510417 | {notebook_id} | {folder_url} |
```

This prevents agents from querying the wrong notebook for a given project.
