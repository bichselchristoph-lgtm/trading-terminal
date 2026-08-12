# HANDOFF-PROTOCOL

> **STATUS** CURRENT · **version** v1.1 · **date** 2026-08-12

**Status** CURRENT
**Version** v1.1
**Origin** authored
**Date** 2026-08-12
**Supersedes** v1.0 (2026-08-11) — same document, amended in place. **One substantive change:** copy-and-keep is now scoped. It was written as a universal rule and is not one.

---

## What this governs

Every task handed from the design session (Claude chat) to Claude Code passes through five states. **Christoph holds the state. Neither Claude can observe it.**

The design session cannot see the repo, cannot see the inbox, and cannot see whether Claude Code ran. Claude Code cannot see the design session. Christoph is the only channel, and therefore the only party who can report a transition. A state advanced without his explicit answer is an assumption wearing the costume of a fact.

---

## The five states

| State | Reached when | Gate |
|---|---|---|
| **WRITTEN** | The design session delivers the `.md` with a download link. | Design session asks: *placed in the inbox?* |
| **HANDED OFF** | Christoph answers yes. | Design session asks: *is it running?* |
| **RUNNING** | Christoph answers yes. | Christoph pastes the done-note. Design session confirms receipt and nothing more. |
| **REVIEWED** | Design session has read the done-note and named every open issue. | If anything is owed to Claude Code, that is a **new task file** and this task stays open. If nothing is owed, design session asks: *done, based on this note?* |
| **DONE** | Both parties agree. | — |

---

## Rules

**1. One gate per file.** Every task file gets its own gate at every transition. Files are never batched through a gate together, because a single yes covering three files cannot say which one it meant.

**2. The design session never advances a state on its own.** Not on inference, not on elapsed time, not because a done-note reads as successful. Only Christoph's explicit answer moves a task forward.

**3. Claude Code's own report of success is not confirmation.** It is evidence, and it arrives inside a repo the design session cannot see. The paste is the channel; there is no other.

**4. Judgment is shared, and which of us holds it depends on the call.**

- The mechanical facts are Christoph's: **inbox placement, whether it ran, whether a done-note exists on disk, and whether what reached the design session was all of it.** He is the only one who can see them.
- The reading is the design session's to *propose*: whether the note shows the task did what it set out to do, what remains open, whether anything is owed.
- The proposal is not a verdict. Christoph weighs it and may call something the design session missed or misread.

**The contents of the note are NOT uniquely his.** An earlier draft of this rule listed *"what the note says"* among the mechanical facts. It does not belong there — once he pastes it, the design session reads the same text, and can read it as well or as badly as anyone. What only he can see is whether a note exists at all, and whether the whole of it arrived.

**Proved on 2026-08-11.** `012a` and `013` both wrote done-notes into `handoff/done/`. **Neither reached the design session**, which went on holding a stale `RUNNING` for both. Nothing in either repo detected it and nothing could: the file was real on one side of the channel and absent on the other. Only Christoph stood where both sides are visible. That is why *whether a note exists* is on his side of the list and *what it says* is not.

**DONE requires both** — the design session's read that nothing is owed, and Christoph's yes.

**5. A task at RUNNING blocks its dependents.** No dependent task is written, and no output of a running task is treated as fact, until that task reaches DONE.

**6. Re-opening is cheap; false DONE is not.** If a task reaches DONE and a later session finds it did not hold, it is reopened as a new task file rather than silently amended.

---

## Why the states are separate

`WRITTEN` and `HANDED OFF` are distinct because a file that exists in the design session's output directory is not a file in the inbox. `HANDED OFF` and `RUNNING` are distinct because a file sitting in the inbox unread looks identical, from the design session's side, to one being executed.

`RUNNING` and `REVIEWED` are distinct for the reason this project keeps rediscovering: **the read is the implementation.** A done-note that arrives and is not read is a correct warning sitting in a file nobody was instructed to open — the failure that produced Layer 0's full specification and total absence from code.

`REVIEWED` and `DONE` are distinct because Christoph cannot certify that a task achieved its purpose, and the design session cannot certify that anything happened on disk. Collapsing them asks one party to sign for work only the other can see.

### What `RUNNING` means

**The five states describe the handoff, not the work's internal progress.**

`RUNNING` means **Claude Code has picked the task up and has not yet reported.** Nothing more. A scheduled window inside a task — a capture that starts at 09:00 ET, a probe that must wait for the open — does **not** create a sixth state, and does not make the task something other than `RUNNING` while it waits.

`012` was correctly `RUNNING` on 2026-08-11 while its capture had not begun: the task had been picked up, phase 0 was complete, and no report had been made.

**A known limit, stated rather than left to be discovered.** `HANDED OFF` and `RUNNING` are **indistinguishable on disk**. A task file sitting in `handoff/inbox/` with no artifact beside it looks identical whether nobody has opened it or a session is mid-execution. No test can separate them, which is why the state is Christoph's to report and not the repo's to infer.

### Where the files live — copy-and-keep, and where it does not apply

**Copy-and-keep governs `handoff/` because `handoff/` is addressed.** `Do inbox 012` is a path resolved by name; a file that moves out from under that name breaks a reference that another party is holding. That — not durability in the abstract — is what the rule protects.

**Nothing in `handoff/` is ever moved.** A done-note is **created** at `handoff/done/NNN-*.md` as a new file; the task file stays in `handoff/inbox/`. Both copies coexist for every completed task, permanently, by design.

#### `christoph/` is a queue, and a queue that never empties is not one

**Ruled, 2026-08-12.** Nothing addresses a path into `christoph/open/`. Claude Code is handed the path when it needs a file; nothing resolves one by name. The folder's whole function is to answer *what do I still have to do* — and it can only answer that if completed items leave it.

So `christoph/` uses **copy-verify-retire**, in that order:

1. **Copy** `christoph/open/NNN-*.md` → `christoph/done/NNN-*.md`.
2. **Verify** the copy exists and is byte-identical.
3. **Then** remove the original from `christoph/open/`.

**This is not a move, and the distinction is not pedantry.** A move is one artifact changing location: interrupt it halfway and there is nothing. Copy-verify-retire never has fewer than one durable copy at any instant. The rule was defending the record, and the record is never at risk here.

**Christoph performs all three steps.** No Claude writes to, or removes from, either `christoph/` folder.

**What must not be inferred from this.** This is a property of `christoph/`, not a general permission. **Done-notes, task files and acceptance records are never retired**, and this ruling is not a precedent for touching them. If a future case looks similar, the test is *is anything addressing this path by name* — if yes, copy-and-keep.

**A one-off repair is also not a move.** On 2026-08-12 `012-uat-first-five-minutes.md` was relocated into `christoph/open/` because it had been written into the wrong tree. Correcting a file that was misplaced at birth is a repair of an authoring error, not a state transition, and sets no precedent either way.

#### The tests this owes

Three assertions, to be built as part of the next task file rather than as their own:

1. **For every file in `christoph/done/`, no same-named file remains in `christoph/open/`.** Catches a retire that stopped after step 1.
2. **Every UAT named in a done-note's exit table resolves in `christoph/open/` *or* `christoph/done/`.** `test_uat_has_a_file.py` globs one folder today; the first retire would break it while the convention was working correctly. **This is the assertion that fires first.**
3. **A file's state header and its folder agree.** Two independent ways to read one state must never disagree silently.

#### One field name, not two

**The header key is `**Status**` everywhere** — task files, done-notes, and `christoph/` items alike. `012-uat-first-five-minutes.md` was written with `**State**`, and two names for one field is exactly the recurring defect this project names most: a test written against one silently skips every file carrying the other. **The five-state vocabulary binds the `**Status**` line in `christoph/` files as it does in `handoff/`;** `OPEN` is outside it and is not a state.

This was established from git history on 2026-08-11: **no file has ever been moved from `inbox/` to `done/`** — `git log --diff-filter=R -M -- handoff/` returns nothing across the repository's whole history. The convention had been operating unwritten, and `CLAUDE.md:133` was the only line in the repo that said a completed task produces a file in `handoff/done/` at all. **A done-note is a file at `handoff/done/NNN-*.md`**, and this document — the adopted authority on handoffs — now says so.

### Done-note frontmatter is outside the five-state vocabulary

**Ruled, 2026-08-11.** The five states describe **the handoff**. A done-note's own frontmatter describes **the work**, and the two are different questions.

`013`'s done-note carries `status: BLOCKED ON ONE DECISION`, which is not one of the five and **is correct** — the handoff was `RUNNING` (picked up, not yet reported) while the work was blocked awaiting a decision. Collapsing those would lose the more useful fact.

So: **frontmatter may say what it likes; the `**Status**` header line may not.** The header carries the handoff state and is bound to the five. `tests/test_handoff_state_declared.py` reads only the first 20 lines and only the `**Status**` line, which is why it did not flag `BLOCKED` — that is correct behaviour, not a gap.

**What a future test would need**, if this ruling is ever reversed: it would have to read YAML frontmatter specifically, distinguish a `status:` key there from the `**Status**` header line, and apply a different vocabulary to each. Nothing in this task extends the test's reach.

---

## The testable half

This protocol governs conversation, and no test in the repo can enforce a conversation. **What a test can enforce is that every task file declares its state**, so the repo itself is never the ambiguous party.

Every `.md` in `handoff/inbox/` and `handoff/done/` declares, in its header:

```
**Status** WRITTEN | HANDED OFF | RUNNING | REVIEWED | DONE
```

`tests/test_handoff_state_declared.py` fails if any task file omits the header or names a state outside the five. This mirrors `test_every_spec_declares_status` and exists for the same reason: a convention that fails a test does not depend on anyone remembering it.

### Carried evidence is exempt, and the exemption is derived

**A file recorded in `EVIDENCE-CARRY.md` is carried evidence, not a live handoff, and does not require a state header.**

21 task files were carried from the archived predecessor on 2026-08-10. Those tasks completed **in another repository, under a convention that did not yet exist**. Backfilling a state onto them would assert something nobody ever declared — and **a fabricated state is exactly what this test exists to catch**. Absence of a header on a pre-convention file is not a defect; it is a true statement about when the file was written.

**The exemption is scoped by a property already recorded and hash-enforced, not by authorship.** Scoping by who wrote a file would be arbitrary, and would exempt precisely the files most likely to go stale.

**It is derived from the manifest at test time and is never a hardcoded list**, because a literal list is a hiding place that grows. Two guards stop it widening quietly:

1. **Every exempted path must appear in `EVIDENCE-CARRY.md`.** If the test ever skips a file with no manifest row, the rule has stopped being derived and has become a list — and the test fails.
2. **No natively-authored file may be exempt.** A carried file's recorded `source path` lies under the archived predecessor; a task file authored in this tree cannot. If one is found in the manifest and skipped, the test fails and names it.

Guard 2 is the one that fires if someone later adds a live task file to `EVIDENCE-CARRY.md` to silence the header requirement. **Adding a live task file to the manifest does not make it evidence.**

### `handoff/done/` does not mean the task is closed

It means **Claude Code has finished and reported.** Whether anything is still owed is a separate judgment, made by Christoph and the design session together, *after* the note is read.

Those two facts shared one folder until 2026-08-11. They no longer do:

**`handoff/accepted/NNN-*.md`** — the record that both parties agreed nothing further is owed: no open follow-ups, no unresolved issues.

**Acceptance is a COPY, not an authored document.**

- When both parties agree, **`handoff/done/NNN-*.md` is copied to `handoff/accepted/NNN-*.md`**, byte-identical. **The presence of the copy is the acceptance.** Nothing is authored.
- **Christoph performs the copy.** He is the only party who can, and it requires nothing from the design session beyond agreement.
- **The five states do not change.** `accepted/` is what `DONE` leaves on disk. Until this existed `DONE` lived only in conversation, which is how four done-notes went unreceived on 2026-08-11.
- **Copy-and-keep applies here too.** Nothing moves. **Three copies coexist**: the task file, the done-note, and the acceptance record.
- **Claude Code never writes to `handoff/accepted/`**, and never infers acceptance from a note it wrote itself.
- **New work discovered during acceptance does not live here.** It goes into the task file for the work it implies. **`handoff/accepted/` records that agreement happened; it is not a place where anything is first written down.**

Nothing is backfilled into it. No past task has an acceptance record, and inventing one would assert an agreement that was never made.

**Why this replaced an authored record, on the day it was adopted.** The first version of this rule said the design session authors the acceptance record and Christoph saves it. It was exercised once — on `013`, `013a`, `013b` and `013c`, immediately after adoption — and failed twice:

1. **It makes closure depend on a party that cannot see the repo.** A task could not be accepted unless the design session was available to write a file about it. A copy needs nobody.
2. **Nobody reads `handoff/accepted/`.** An authored record puts new information somewhere it will never be opened — the same failure this project names most often, *a correct warning sitting in a file nobody was instructed to read.* Anything genuinely new belongs in the task file for the work it implies, where someone must read it to do the job.

The design session authored four acceptance records; Christoph discarded them and copied the four done-notes instead. **The copy rule is what the four files in `handoff/accepted/` actually are** — verified byte-identical to their `handoff/done/` counterparts on 2026-08-11.

**The untested half remains untested, and this document says so plainly.** Whether the design session actually waits for a gate is not machine-checkable. It is checkable by Christoph, which is why the gates are asked out loud rather than assumed.

---

## Version history

**Every change to this document increments the version and adds a row. A version is never reused and never decremented.** The version line is the thing a test can pin; a date is not, because two edits land on one date and the second is then invisible.

| Version | Date | Change |
|---|---|---|
| **v1.1** | 2026-08-12 | **Copy-and-keep scoped.** `handoff/` is copy-and-keep because it is addressed by name; `christoph/` is copy-verify-retire because it is a queue. Adds the three tests this owes, the `**Status**`-not-`**State**` ruling, and the note that the `012` UAT relocation was a birth defect rather than a precedent. Everything else byte-identical to v1.0. |
| **v1.0** | 2026-08-11 | First statement of a convention that was previously implicit. Five states, one gate per file, shared judgment, copy-and-keep, the evidence exemption, and `handoff/accepted/` as a copy rather than an authored record. |

**v1.0 was not numbered when it was written.** The number is applied here retrospectively to the 2026-08-11 content, which is a declaration made now, not a fact recovered from the file. Git history is the authority on what that content actually was.

**A version pin belongs in a test**, mirroring `tests/test_regime_prompt_invariants.py`, which pins `REGIME-PROMPT.md` at v1.2 or higher. Without it the version is prose, and a convention that lives in prose depends on someone remembering. **That test does not exist yet** and is owed by the next task file.
