---
id: 085
title: Both open questions are answered — 063's gate was unsatisfiable and 065's count was wrong
type: task
class: admin
unblocks: 067
story: none
owner: claude-code
depends: none
touches: handoff/questions, tests/test_task_file_shape.py
answers:
  - 063-q1
  - 065-q1
---

**Status** WRITTEN

# 085 — answering two questions, and making one of them not happen again

**Both answers are short. The test in Part 3 is the part that matters.**

---

## 0. Is this task for you

**If `handoff/inbox/085-for-code-task-answer-two-questions.md` exists in your
tree and no file beginning `085-` exists in `handoff/done/`, this task is for
you. Otherwise stop reading and ignore this message.**

---

## 1. Answer to `063-q1` — the refusal was correct and the gate was wrong

**You were right to stop, and the finding is not the dirty tree.** The paths you
named were Christoph performing `christoph/`'s own copy-verify-retire — the
sanctioned route — plus two run-record files that every `verify.ps1` and
`export-handoff.ps1` run rewrites by design.

**The gate was unsatisfiable.** *No tracked file modified that this session did
not write* can essentially never hold in this tree: `christoph/**` is edited by
Christoph whenever he likes, `sync-run-record.md` and `export-run-record.md` are
rewritten on every run, and `docs/observations/OBSERVATIONS.md` is appended by
other sessions. **Project instructions rule 17 already says a condition must be
one that can actually hold — that task's own precondition broke it.**

**Also worth recording: your observation that the set changed three times while
you were writing the refusal is the stronger half of the finding.** A
whole-tree quiet check is not merely hard to satisfy, it is **not a property of
the tree at all** — it is a property of a moment, and it has already stopped
being true by the time it is acted on.

**Set `063-q1` to `ANSWERED`.** 063 itself is superseded by 064 and both are
done; nothing else is owed on it.

---

## 2. Answer to `065-q1` — reading 2, and the wrong count was the design session's

**Your reading of the tree is correct and the task file's premise was not.**
Ten levels exist; thirteen do not. The three that Part A asked for already
rendered before it started.

**The error is named: the design session read "23 levels" off LEVELS-SPEC and
treated it as a count of the tree.** A count read from an artifact is a count as
of that artifact's world — the spec ruled twenty-three, the tree had ten, and
nobody had reconciled them.

**Part A closes as already delivered.** Its caption exit tests (`23 of 23`,
`17 of 23`) are **withdrawn**, not deferred — they described a rail that does
not exist. **Do not build the thirteen here.** Part A's own text forecloses it
and h067 exists for exactly that work.

**Your finding that all thirteen derive from data already fetched is carried
forward into h067** — no new IBKR request either way — and it is what makes
that task affordable.

**Set `065-q1` to `ANSWERED`.**

---

## 3. Part 3 — the gate cannot be written that way again

**A test that goes red when a task file's precondition depends on paths outside
its own `touches:` declaration.**

**This is the positional fix.** 063's gate failed because it asserted something
about the whole tree; a task can only reasonably assert something about the
paths it is going to change. **Rule 17's "a condition that can actually hold"
becomes checkable rather than remembered.**

Add it to `tests/test_task_file_shape.py`, beside the guards already there.

**Two things to be careful of, both of which this project has been bitten by:**

- **Existing task files must not be swept.** The test applies to files in
  `handoff/inbox/`; if historical ones fail it, **report the list in the
  done-note and do not edit them** — `handoff/` is copy-and-keep.
- **Do not read a state the shared fixture guarantees** — B-136.

**See it red first.** Construct a task file with a whole-tree precondition,
watch the test fail, then remove it.

---

## 4. What you may NOT do

**Do not build any of the thirteen levels.** h067.

**Do not edit any question file's body** — only its `status` field.

**Do not edit historical task files** to satisfy the new test.

**Do not touch `verify.ps1`.**

---

## 5. Exit tests

**Green.** Both question files read `ANSWERED`.

**Guard.** The new test in `test_task_file_shape.py`, seen red against a task
file carrying a whole-tree precondition.

**No UAT.** Nothing here renders. **Stated deliberately rather than omitted** —
this is an admin task with no product surface.

---

## 6. What the done-note must state

Any existing task file that fails the new guard, listed and not edited. Whether
the guard was seen red and against what.

`verify.ps1` runs as the last action. Do not paste or summarise it.

---

## 7. The prompt

```
Do inbox 085
```
