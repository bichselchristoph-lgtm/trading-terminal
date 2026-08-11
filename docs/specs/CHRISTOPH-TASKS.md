> **STATUS** CURRENT · **date** 2026-08-11

# CHRISTOPH-TASKS

Companion to `HANDOFF-PROTOCOL.md`. That document governs work handed to Claude Code. **This one governs work that only Christoph can do.**

---

## Why a separate tree

Anything under `handoff/inbox/` is executed by Claude Code on `Do inbox NNN`. A task addressed to Christoph must never be executed by Claude Code — it would either fail, or worse, succeed at something it was not asked to judge.

**Same folder, different audience is the ambiguity this project keeps paying for.** So the separation is structural rather than conventional: `christoph/` sits outside `handoff/` entirely, and Claude Code writes nothing there and reads it only when a task explicitly says to.

The tree is named for its **audience, not its activity.** An earlier draft called it `uat/`, which was already wrong on the day it was proposed — the first item destined for it was an entitlement question for IBKR, which is not acceptance testing. A name describing the work will be wrong again the next time a new kind of item arrives.

---

## Layout

```
christoph/open/NNN-short-name.md      items outstanding
christoph/done/NNN-short-name.md      items closed, with the result
```

**Copy-and-keep, as in `handoff/`.** The open file stays where it is; a result file is created in `done/`. Nothing is ever moved. This mirrors the convention `013a` found already operating in `handoff/` and previously unwritten.

---

## The two types

Every file declares one in its header.

| Type | What it asks | Example |
|---|---|---|
| **UAT** | Verify something that was built. Needs eyes, memory, or a judgment neither Claude can supply. | *Read rule 4 and confirm it matches what you meant by shared judgment.* |
| **EXTERNAL** | Take an action outside the repo. Ask a person, check an account, phone a broker. | *Ask IBKR why an account holding TotalView receives 10089 for API access on `NASDAQ.NMS/DEEP`.* |

**Not every task generates one.** A check that `pytest` can make does not need Christoph. An item belongs here only when the answer is unavailable to both Claudes — which is precisely why it needs recording rather than asking in passing.

---

## States

The same five as `HANDOFF-PROTOCOL.md`: `WRITTEN`, `HANDED OFF`, `RUNNING`, `REVIEWED`, `DONE`. They mean the same things, with the actor changed:

- **WRITTEN** — the design session has authored the file and given Christoph the link.
- **HANDED OFF** — Christoph has saved it to `christoph/open/`.
- **RUNNING** — Christoph is acting on it. For an EXTERNAL item this may span days, since it can depend on a third party.
- **REVIEWED** — Christoph has reported the outcome in chat and the design session has read it.
- **DONE** — both agree nothing further is owed.

---

## Who writes what

Christoph can save files but does not author them. So:

1. The **design session authors** the task file. Christoph saves it to `christoph/open/`.
2. Christoph **acts**, and reports the outcome in chat.
3. The **design session authors the result file.** Christoph saves it to `christoph/done/`.

**The result must reach disk.** An outcome that lives only in conversation is lost at the end of the session — the same failure as a done-note that never leaves chat, which happened three times on 2026-08-11 alone.

---

## Storage

**Results are carried as evidence, not adopted.** They are observations, not authored code: hash-verified into `EVIDENCE-CARRY.md`, with no per-file `.provenance.md` companion.

**This document is the exception.** It is authored, and it passed the adoption gate once. Individual items under `christoph/` do not.

Under resolution D of `013`, files recorded in `EVIDENCE-CARRY.md` are exempt from the handoff state-header test. `christoph/` items therefore need no `**Status**` header for the test's sake — though writing one costs nothing and helps a cold reader.

---

## What Claude Code does with this tree

**Nothing, unless a task says so.** It does not execute items here, does not update their states, and does not close them. It may *read* one when a task instructs it to — for instance, to check whether an EXTERNAL answer has landed before proceeding on work that depends on it.

**Claude Code never writes to `christoph/`** except when a task explicitly directs it to create a file there, and no such task exists at the time of writing.
