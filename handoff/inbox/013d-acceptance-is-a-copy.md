# 013d — Correct §2e: acceptance is a copy, not an authored document

**Status** DONE · **Date** 2026-08-11 · **Type** one-line spec correction
**Runs in** `D:\Dev\momentum`. No TWS, no network, nothing under `records/`. **Safe alongside the capture and alongside `S009`** — it touches one file neither of them opens.

> Read this cold. The session that wrote it cannot answer questions.
> **This is deliberately small.** One amendment, one file. It exists to close the last open item before the first build slice, not to reopen the protocol.

---

## Why

`HANDOFF-PROTOCOL.md` §2e, written yesterday and adopted by `013c`, says the design session authors the acceptance record and Christoph saves it.

**That is wrong, and it was wrong when written.** Acceptance was exercised for the first time on `013`, `013a`, `013b` and `013c` immediately after adoption. The design session authored four acceptance records; Christoph discarded them and **copied the four done-notes from `handoff/done/` into `handoff/accepted/` instead.** That is the correct process and it is what the tree now shows.

Two things are wrong with the authored version:

1. **It makes closure depend on a party that cannot see the repo.** A task cannot be accepted unless the design session is available to write a file about it. Copying needs nobody.
2. **Nobody reads `handoff/accepted/`.** An authored record puts new information somewhere it will never be opened — the sixth instance of *a correct warning sitting in a file nobody was instructed to read*, which is the failure this project names most often. Anything genuinely new belongs in the task file for the work it implies, where someone must read it to do the job.

---

## The amendment

Edit `docs/specs/HANDOFF-PROTOCOL.md` §2e **in place. Do not re-author the file and do not accept a replacement from outside the tree.**

**Replace the authoring rule with the copy rule.** The substance:

- **Acceptance is a copy.** When both parties agree nothing further is owed, `handoff/done/NNN-*.md` is copied to `handoff/accepted/NNN-*.md`. **The presence of the copy is the acceptance.** Nothing is authored, and the copy is byte-identical to the note.
- **Christoph performs the copy.** He is the only party who can, and it requires nothing from the design session beyond agreement.
- **Copy-and-keep still applies.** The done-note stays in `handoff/done/`. Three copies coexist: task file, done-note, acceptance record.
- **Claude Code still never writes to `handoff/accepted/`** and never infers acceptance from a note it wrote itself. Unchanged.
- **New work discovered during acceptance does not live here.** It goes into the task file for the work it implies. **`handoff/accepted/` is a record that agreement happened, not a place where anything is first written down.**

**Record why**, briefly: the authored version was exercised once, failed twice on the same day it was adopted, and the copy version is what the four accepted files actually are.

---

## Do not

- Do not re-author `HANDOFF-PROTOCOL.md` or accept a replacement from outside the tree.
- Do not touch `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md`, or `CHRISTOPH-TASKS.md`.
- Do not add, remove, or redefine any of the five states.
- Do not modify anything already in `handoff/accepted/` — those four files are correct.
- Do not modify any file recorded in `EVIDENCE-CARRY.md`.
- Do not touch `records/`, the capture, or anything `S009` is building.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full `pytest`, unchanged from `013c`'s **71 passed, 0 failed**. This amendment adds no test and should break none. |
| **Refusal** | Claude Code | Confirm the four files in `handoff/accepted/` are **byte-identical** to their counterparts in `handoff/done/`. If any differs, say so and change nothing — a mismatch means the copy rule is already not what happened, and that is a finding rather than something to repair. |
| **UAT** | Christoph | None. |

## Done-note must state

- §2e as it now reads, quoted.
- The byte-identity result for all four accepted files.
- **Anything in this task that diverged from what was on disk.**
