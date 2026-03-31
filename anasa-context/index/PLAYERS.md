---
name: asana-players-index
description: |
  All humans and agents in the D&S / GNGE workspace with GIDs, handles, roles,
  and email addresses. Load when you need to @mention, assign, or route a task
  to a specific person or agent. Agents are marked with [AGENT] prefix.
  Last refreshed: 2026-03-31 by Cirra via maintenance/update-players-index.
---

# Players Index

Workspace GID: `9526911872029`

---

## Core D&S Team (Humans)

| Handle | Name | GID | Email | Role |
|--------|------|-----|-------|------|
| @Malkio | Malkio | `366935507295725` | mr@gnge.co | Founder / Primary |
| @Reggie | Reggie | `1203982573237773` | Regina@duckandshark.com | Operations |
| @Po | Po | `1207318683503051` | adepoju@duckandshark.com | Operations |
| @Kay | Kay | `1202052377104886` | kay@duckandshark.com | — |
| @Mari | Mari | `1161555221069061` | mari@duckandshark.com | — |
| @Nora | Nora | `1211101390981051` | nora@duckandshark.com | — |
| @Michael | Michael | `1207302581221108` | michael@duckandshark.com | — |
| @Caspera | Caspera | `1129617799923819` | caspera@gnge.co | Platform / Agent Host |

---

## Active Agents (D&S)

| Handle | Name | GID | Email | Platform | Notes |
|--------|------|-----|-------|----------|-------|
| @Cirra | Cirra | `1213811795430502` | caspera+cc2@duckandshark.com | Claude (CC2) | Developer Agent |
| @CeeCee | CeeCee | `1213811795430490` | caspera+cc@duckandshark.com | Claude (CC1) | — |
| @Cindra | Cindra | `1213811795430505` | caspera+cc3@duckandshark.com | Claude (CC3) | — |
| @Koda | Koda | `1213811795430511` | caspera+cody@duckandshark.com | Codex (Cody1) | — |
| @Dex | Dex | `1213811795430496` | caspera+cody2@duckandshark.com | Codex (Cody2) | — |
| @Rook | Rook | `1213811795430508` | caspera+cody3@duckandshark.com | Codex (Cody3) | — |
| @Aegis | Aegis | `1213811795430499` | caspera+ag2@duckandshark.com | Gemini (AG2) | — |
| @Argus | Argus | `1213811795430514` | caspera+ag@duckandshark.com | Gemini (AG1) | — |

---

## Extended Workspace (Active Collaborators)

| Name | GID | Email | Context |
|------|-----|-------|---------|
| Erik | `378511826573201` | erik@gnge.co | GNGE |
| Carlos Montero | `606530190214537` | carlos@gnge.co | GNGE |
| Kai Löffler | `366936020259675` | Kai@gnge.co | GNGE |
| Monique | `1184969964433139` | monique@gnge.co | GNGE |

---

## Agent Naming Convention

- **CC** prefix = Claude (Claude Code) agents: CeeCee, Cirra, Cindra
- **Cody** prefix = Codex agents: Koda, Dex, Rook
- **AG** prefix = Gemini agents: Argus, Aegis
- All agent emails follow pattern: `caspera+{id}@duckandshark.com`
- Pond Ocean agents (`ai+*@pondocean.co`) are external workspace members — treat as read-only collaborators unless context says otherwise

---

## Routing Priority

When deciding who to contact about a task: **Driver → Owner → Assignee**. All three are valid. Never @mention all three simultaneously — pick the most appropriate for the action.

For agent-to-agent routing: use GID directly in `custom_fields` (Driver/Owner fields support people type). Do not use `assignee` for agents unless the task is actively being worked.
