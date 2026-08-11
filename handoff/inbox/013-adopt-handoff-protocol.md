# 013 — Adopt HANDOFF-PROTOCOL and enforce task-file state headers

**Status** DONE · **Date** 2026-08-11 · **Type** adoption + test
**Runs in** `D:\Dev\momentum`. No market data. No TWS. **Safe to run while 012 is capturing** — it touches no subscription, no `records/`, and no network.

> Read this cold. The session that wrote it cannot answer questions.

---

## Why

The handoff convention between Christoph and the design session has been operating unwritten for the whole project. It has already produced one class of error — a task treated as finished on the strength of a report the design session could not see.

This is the project's recurring failure shape: **a convention that lives in prose depends on someone remembering it.** `CLAUDE.md`'s handoff line and `RE-SUPPLY.md` are the same lesson applied twice already. This is the third.

The protocol itself governs a conversation and cannot be tested. **The half that can be tested is that every task file declares its state**, so the repo is never the ambiguous party.

---

## Phase 1 — adopt

Two files are waiting in `D:\Dev\_adopt\`:

```
HANDOFF-PROTOCOL.md
HANDOFF-PROTOCOL.provenance.md
```

Adopt into `docs/specs/` via `tools/adopt.py`. Standard gate — this is a create, **not** a supersede; do not pass `--supersede`.

Confirm on the way through:

- The status header is `CURRENT` and `test_every_spec_declares_status` collects it and passes.
- `ADOPTION-LOG.md` gains its row.
- The provenance companion records `origin: authored`, so refusal 4 does not apply.

---

## Phase 2 — the test

Write `tests/test_handoff_state_declared.py`.

**What it asserts.** Every `.md` in `handoff/inbox/` and `handoff/done/` contains a header line declaring exactly one of:

```
WRITTEN · HANDED OFF · RUNNING · REVIEWED · DONE
```

**Match on the header region only** — the first 20 lines — not anywhere in the body. A task file that discusses these words in prose must not accidentally satisfy the test. This is the same trap the `6 of 9` normalization hit, where an exclusion list was replaced by a positional rule for exactly this reason.

**Fail loudly on two distinct conditions, with different messages:**

1. **No state header at all** — name the file.
2. **A header naming something outside the five** — name the file *and* the offending value. Do not silently treat an unrecognised state as absent; the two are different defects and a reader needs to know which one they have.

**Empty directories pass.** An empty `handoff/done/` is a true statement about a project where nothing has completed yet. Do not make emptiness a failure.

### Backfill

Existing task files will not have the header. **Add it — do not weaken the test to accommodate them.**

- `handoff/inbox/012-live-qqq-tape-capture.md` → state as Christoph reports it; if unknown when you run this, write `RUNNING` and **say so in the done-note** so it can be corrected.
- Every file already in `handoff/done/` → `DONE`.
- **If any file's true state is genuinely unclear, stop and list it rather than guessing.** A fabricated state is exactly the defect this test exists to prevent — a well-formed value answering a different question.

---

## Do not

- Do not touch `records/`, any tape file, or anything related to task 012.
- Do not open a TWS connection.
- Do not modify `SPEC.md`, `REGIME-PROMPT.md`, or `BUILD-PLAN.md`.
- Do not add gates, states, or rules beyond the five in the document.
- Do not weaken the test to make existing files pass.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full `pytest` run. The 8 pre-existing failures stay at 8 — **name them explicitly** so the count is not the only evidence. New test collects and passes. |
| **Refusal A** | Claude Code | Create a temp task file with no state header. Confirm the test fails and the message names the file. |
| **Refusal B** | Claude Code | Create a temp task file with `**Status** IN PROGRESS`. Confirm the test fails with the *invalid-state* message, naming the value — **not** the missing-header message. Delete both temp files. |
| **UAT** | Christoph | Open `docs/specs/HANDOFF-PROTOCOL.md` and read rule 4. Confirm it matches what you meant by shared judgment. If it does not, that is a spec defect and a new task, not an edit. |

## Done-note must state

- The `ADOPTION-LOG.md` row as written.
- The exact matching rule used for the header region, quoted from the test.
- Both refusal messages, verbatim.
- Which files were backfilled and to which state, flagging any where the state was inferred rather than known.
- The 8 pre-existing failures by name.
