# 015 — A UAT that exists only in a done-note is not a UAT

**Status** DONE · **Date** 2026-08-11 · **Type** test + spec amendment
**Runs in** `D:\Dev\momentum`. No TWS, no network, nothing under `records/`. **Safe alongside the capture.**
**Run after `014`** — that one has a clock and this one does not.

> Read this cold. The session that wrote it cannot answer questions.

---

## Why

`S009`'s exit-test table says *"UAT — yours. Run it with no data and read the empty screen. Write the record to `christoph/`."*

**Nothing wrote it.** Claude Code correctly does not write to `christoph/`, and the design session had no trigger. The UAT existed as a line inside a done-note that Christoph had already read, in a folder he does not open again. He asked where his UAT was, and the answer was: nowhere.

This is the **seventh** instance of *a correct instruction sitting in a file nobody was directed to open* — the pattern that left Layer 0 fully specified and never built. `CHRISTOPH-TASKS.md` says the design session authors these files. **A convention in prose depends on someone remembering; a convention that fails a test does not.**

The same gap produced the acceptance-record confusion two hours earlier. Both were fixed by hand. This one gets a test.

---

## Part 1 — `tests/test_uat_has_a_file.py`

**The rule.** If a done-note's exit-test table names a **UAT owned by Christoph**, a corresponding file must exist in `christoph/open/` or `christoph/done/`.

### Detecting the UAT

Parse `handoff/done/*.md` for an exit-test row whose first cell is `UAT`. **Match on the table row, not on the word appearing anywhere in the file** — the same positional discipline as `test_handoff_state_declared`, and for the same reason: a lexical match turns every done-note that *discusses* UATs into a false positive, and an exclusion list to suppress those becomes the hiding place.

**A row that says `UAT | Christoph | None` is a valid declaration that no UAT is owed.** It must pass. Not every task needs one, and forcing a file for tasks that do not is how a useful rule becomes noise people learn to ignore.

### Linking the file back

Each `christoph/` file declares the task it belongs to in its header:

```
**Slice** S009
```
or
```
**Task** 012
```

The test extracts the identifier from the done-note's filename and requires a `christoph/` file declaring it. **Search both `open/` and `done/`** — an answered UAT is still a satisfied one.

### Failure message

Name the done-note, the identifier, and what is missing. Say plainly that the fix is to author the file, and that **the design session authors it and Christoph saves it** — a reader hitting this test should not have to find `CHRISTOPH-TASKS.md` to know what to do.

### Exemption

**Reuse resolution D exactly.** Done-notes recorded in `EVIDENCE-CARRY.md` are carried evidence, predate the convention, and are exempt — derived from the manifest at test time, never a list. **Do not write a second exemption mechanism**; if the existing one cannot be reused as-is, say so rather than duplicating it.

**Backfill nothing.** Older tasks whose UATs were performed verbally do not get files invented for them. **An invented record of an agreement nobody made is the fabrication these tests exist to prevent.** If that leaves the test red on historical notes outside the manifest, report which and stop — do not weaken the rule to make them pass.

---

## Part 2 — `christoph/open/003`

A file is in `D:\Dev\_adopt\`:

```
003-s009-read-the-empty-screen.md
```

**Move it to `christoph/open/003-s009-read-the-empty-screen.md`.** It is a `christoph/` item, not an adoption — `christoph/` is in `NATIVE_PREFIXES` and does not pass the gate.

It already carries `**Slice** S009`. **If the test's expected format differs from what the file declares, change the test to match the file, not the other way round** — the file is the convention's first instance and the format should follow real use.

---

## Part 3 — Amend `CHRISTOPH-TASKS.md` in place

**Edit the file on disk. Do not re-author it and do not accept a replacement from outside the tree.**

**3a — What makes a UAT exist.** The document says the design session authors the task file. Add: **a UAT named in a done-note's exit-test table is not a UAT until the file exists in `christoph/open/`**, and `tests/test_uat_has_a_file.py` enforces it. Record why: `S009`'s UAT was named in its exit table, went unwritten, and was only noticed because Christoph asked.

**3b — The header convention.** State that every `christoph/` file declares `**Slice** SNNN` or `**Task** NNN`, and that the test uses it. A convention a test depends on must be written where an author will look.

**3c — Not every task owes one.** `UAT | Christoph | None` is a valid declaration and passes. **A rule that fires on tasks with nothing to check trains people to ignore it.**

---

## Do not

- Do not weaken or backfill to make historical done-notes pass.
- Do not write a second exemption mechanism alongside resolution D's.
- Do not author any `christoph/` file other than moving `003` into place.
- Do not modify anything in `handoff/accepted/`, or any file in `EVIDENCE-CARRY.md`.
- Do not touch `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md`, or `HANDOFF-PROTOCOL.md`.
- Do not touch `records/`, the capture, or anything belonging to `012`.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full `pytest`. `S009`'s UAT resolves to `christoph/open/003-*.md` and the suite is green. State the pass/fail count against `014`'s baseline. |
| **Refusal A** | Claude Code | Temporarily rename `christoph/open/003-*.md`. Confirm the test fails naming `S009` and the missing file. Restore. |
| **Refusal B** | Claude Code | Add a temp done-note whose exit table reads `UAT \| Christoph \| None`. Confirm it **passes** — no file demanded. Delete. |
| **Refusal C** | Claude Code | Add a temp done-note that mentions the word UAT only in prose, outside any table. Confirm it **passes** — the rule is positional, not lexical. Delete. |
| **UAT** | Christoph | None. This one is machine-checkable, which is the point of it. |

## Done-note must state

- The detection rule, quoted from the test.
- The failure message, verbatim.
- How the resolution D exemption was reused, or why it could not be.
- Any historical done-note left red, and which.
- **Anything in this task that diverged from what was on disk.**
