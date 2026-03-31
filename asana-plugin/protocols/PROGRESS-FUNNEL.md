# Progress Funnel — Stage Gates & Enforcement

The Progress Funnel is the core task lifecycle system at Duck & Shark. Every task lives in exactly one stage at a time. Moving a task forward requires meeting gate conditions — not just deciding it feels done. Agents enforce these gates autonomously; human review is needed only at designated points (Reviewing → Resolved).

The goal: each column should trend toward zero as work progresses. Unsorted is a staging area, not a graveyard.

---

## Stage Definitions

| Stage           | Meaning                                                             | Agent can set?                              |
|-----------------|---------------------------------------------------------------------|---------------------------------------------|
| **Unsorted**    | Backlog / notepad. Fields may be incomplete. No commitment yet.     | ✅ Free to set                              |
| **Todo**        | Intent confirmed. Requirements met. Work not started.               | ✅ When gate passes                         |
| **Focus**       | Queued for active work this sprint/period.                          | ✅ When gate passes                         |
| **Addressing**  | Work actively in progress. Daily update required.                   | ✅ When gate passes                         |
| **Resolved**    | Work done. All acceptance criteria and DoD met.                     | ✅ When gate passes                         |
| **Roadblocked** | Blocker documented. Escalation initiated.                           | ✅ Must post blocker comment simultaneously |
| **Reviewing**   | Submitted for human review.                                         | ✅ When gate passes                         |

> Agents manage stages autonomously once funnel policy is met. Human involvement diminishes as trust is established. The driver (task owner) is primarily responsible for moving to Addressing, but any agent with context may do so.

---

## Gate Rules

### Unsorted → Todo
- Task name is clear and actionable (anyone can read it and know what to do)
- Assignee set
- Definition of Done exists (at minimum a draft)
- Component or domain tagged

### Todo → Focus
- DoD is finalized (`DoD Status = Ready ✔`)
- All required custom fields are set
- Deadline Band set
- Assignee is available (not Roadblocked on another critical task)

### Focus → Addressing
- Deadline is set (specific date)
- All custom fields populated
- Driver has confirmed work has started (comment on task)

### Addressing → Resolved
All of the following must be true:
- All subtasks completed
- `DoD Status = Ready ✔`
- All tests and driver-side reviews confirmed done (comment evidence)
- All artifacts provided: `REF_LINK`, `TEST_LINK`, `TRANSCRIPT` filled where applicable
- Warranted visual proof linked (screenshot/recording) if applicable
- Summary comment posted by driver or agent
- No blocking FS or SS dependencies outstanding

### Any Active Stage → Roadblocked
- Comment posted documenting: what is blocked, why, who owns the resolution
- Owner or relevant stakeholder @mentioned in the comment

### Roadblocked → Previous Stage
- Blocker resolved (comment acknowledging resolution)
- If blocker was another task: dependency cleared or confirmed resolved

### Any Stage → Reviewing
- Same artifact requirements as Addressing → Resolved
- Reviewer explicitly @mentioned in comment

### Reviewing → Resolved
- Reviewer has confirmed in writing (comment) that review is approved

---

## Field Dependency Rules

These field combinations are enforced — never set them in conflicting states:

| Condition                        | Rule                                      |
|----------------------------------|-------------------------------------------|
| Stage = Roadblocked              | DoD Status ≠ Ready                        |
| Stage = Resolved                 | DoD Status must = Ready ✔                 |
| Stage = Focus                    | DoD Status must = Ready ✔ (gate)          |
| Stage moves to Addressing        | Trigger Q-rank reassessment               |
| Stage moves to any new stage     | Reassess priority vs. siblings in same stage |

---

## Priority Order (when no specific task is given)

Work in this sequence:

1. **Stage:** Roadblocked → Addressing → Focus → Todo → Unsorted
2. **Project:** Workspace-level priority → User-specific priority
3. **Q-rank within stage:** See `skills/prioritizing/SKILL.md`

Never skip a Roadblocked task to work on something lower-priority without documenting why.

---

## Common Violations to Watch For

- Task in Focus without DoD Ready → move back to Todo, comment why
- Task in Addressing with no recent update → prompt for daily update
- Task in Resolved with incomplete subtasks → revert stage, comment
- Comment posted on wrong task (misattributed work) → note the error, correct it
- Stage moved without meeting gate → revert and document

When you catch a violation, fix it and post a brief comment explaining what was corrected and why. Don't silently change things.
