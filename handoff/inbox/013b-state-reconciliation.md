# 013b — Do you agree with the state table?

**Status** DONE · **Date** 2026-08-11 · **Type** read-only reconciliation
**Runs in** `D:\Dev\momentum`. No writes, no network, no TWS. **Safe alongside the capture.**

> Read this cold. The session that wrote it cannot answer questions.
> **This task writes nothing** — including no done-note file. `013a` hit that contradiction; this task resolves it in advance: **report in chat, write nothing.** If a file is needed later, a separate task will ask for it.

---

## Why

The design session holds task state in conversation. Claude Code holds a repo. **Neither can see the other**, and Christoph is the only channel between them — which means the two views can diverge silently and nothing detects it.

This is a reconciliation, not an audit. **Disagreement is the useful output.** If the tree says something the design session's table does not, that gap is the finding.

---

## The design session's table, as of 2026-08-11 ~07:30 ET

| Task | State per design session |
|---|---|
| `012` live QQQ tape capture | RUNNING |
| `012a` pre-open correction | RUNNING |
| `013` adopt HANDOFF-PROTOCOL | RUNNING |
| `013a` handoff tree inventory | DONE |

Older tasks — H8, H9, H9a, M001, H10, H11 — are believed DONE.

---

## What to report

**1. Agree or disagree, per row.** For each of the four, state what the repo shows and whether it matches. **Where the repo cannot distinguish two states, say so** rather than picking the closer one — `HANDED OFF` and `RUNNING` may look identical on disk, and that limitation is itself worth reporting.

**2. What `013` actually did.** It was reported RUNNING and its changes were staged and uncommitted when `013a` read the tree. Report its current state: committed, still staged, partially applied, or complete-but-unreported. **If `013` finished and its done-note was written, say so** — the design session has not received it and would be holding a stale RUNNING.

**3. Any task the design session's table omits.** Anything in `handoff/inbox/` or `handoff/done/` not named above. The table is built from one conversation and may simply not know about work that exists.

**4. Any state header that contradicts reality.** `013` backfills headers. If a file now declares a state that the repo contradicts — a header saying `DONE` where no done-note exists, or `RUNNING` for something finished — name the file and both values. **A fabricated state is the defect `013`'s test exists to prevent**, and it would be worth knowing if the backfill introduced one.

**5. Whether the capture is unaffected.** Confirm `012`/`012a` and `records/tape/` were not touched by anything in this reconciliation.

---

## Do not

- Do not write, move, rename, or delete anything, including a done-note.
- Do not commit or stage.
- Do not correct any state you disagree with. **Report it.** The design session holds the table and will amend it.
- Do not touch the capture, `records/`, or `live/`.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | All five items reported. `git status --porcelain` hashes identically before and after — **prove it, do not assert it**, as in `013a`. |
| **Refusal** | Claude Code | Where the repo cannot distinguish two states, the report says so. **An inference is labelled as an inference**, never reported as an observation. Two misdiagnoses today came from exactly that collapse. |
| **UAT** | Christoph | None. This one is machine-checkable. |

## Report must state

- Per-row agreement, with what the repo shows.
- `013`'s true current state, and whether a done-note for it exists.
- Any task the table omits.
- Any header contradicting reality, with file and both values.
- Confirmation the capture is untouched.
- **Which of your answers are observations and which are inferences.**
