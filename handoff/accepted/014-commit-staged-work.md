---
id: 014
title: Commit the staged work before the capture
status: DONE
owner: claude-code
ran: 2026-08-11, 08:07–08:13 ET
tree: D:\Dev\momentum
---

# 014 — 58 staged paths committed in five

**Status** DONE

```
Full suite  : 99 passed, 0 failed   (unchanged)
git status  : clean — 0 uncommitted paths
HEAD        : aa8bb43 → f6167d7
```

Finished at **08:13 ET**, 47 minutes before the capture window. Nothing pushed.

---

## The five commits

**Split five ways, not three.** The task named three groups; the staged work genuinely
contained five, and forcing two of them into the nearest neighbour would have produced
exactly the unreadable diff 014 exists to prevent.

### 1. `77743ff` — H11: the re-supply rule, SPEC §5.5a, and the supersession review

`docs/specs/RE-SUPPLY.md`, `SPEC.md`, `CLAUDE.md`, `tests/test_resupplied_docs_are_repaired.py`,
`tests/test_regime_prompt_invariants.py`, `tests/test_adopt_supersession.py`, `tools/adopt.py`,
and H11's own notes.

The re-supply invariants, §5.5a's schema bump, the separator-normalised `6/9` check, and the
**two real defects the supersession review found in H10's `--supersede` flag** — the
create-path-wearing-a-replace-flag, and the silent no-op when marking a row that did not
exist. Both fixed, both tested.

### 2. `b48b2f0` — 012/012a: the capture tool, and two misdiagnoses corrected

`tools/capture_tape.py` and the 012/012a task files and done-note.

**This is the group 014 did not name.** It is neither gate work, nor protocol, nor S009 — it
is the live-capture tooling, and it has its own subject. Forcing it into the S009 commit would
have put a TWS client in a diff about a TUI.

### 3. `d2d6af9` — the 013 series: protocol, resolution D, two trees

`HANDOFF-PROTOCOL.md`, `CHRISTOPH-TASKS.md`, `tests/test_handoff_state_declared.py`,
`christoph/`, `handoff/accepted/`, all five 013-series notes and task files, `ADOPTION-LOG.md`.

### 4. `8a3879c` — S009: the first panel this project has ever rendered

`live/tui/`, `live/tests/`, `config/layout.yaml`, `BUILD-PLAN.md`,
`tests/test_adoption_log_complete.py`, and S009's notes.

**The only commit containing running code**, which is why the split mattered most here.

### 5. `f6167d7` — the 013 backfill on seven already-committed done-notes

`handoff/done/{005, H8-and-corrections, H9-commit-the-specs, H9a, H10, M001}` and
`handoff/inbox/H10`, plus 014's own task file.

**The second group 014 did not name**, and it is separated deliberately: these files were
already in history and this commit adds one header line to each. Grouped with new work, the
diff would read as though the notes themselves had changed.

---

## Staged paths that fitted none of the three named groups

**Two groups' worth, ten files.** Named rather than forced:

| path | why it fits none of the three |
|---|---|
| `tools/capture_tape.py` | live-capture tooling — not the gate, not the protocol, not the TUI |
| `handoff/inbox/012-*.md`, `012a-*.md`, `handoff/done/012a-*.md` | same subject |
| 7 × `handoff/done/*` + `handoff/inbox/H10-*` | already-committed notes gaining only a header line |

Both became their own commits.

**One genuine oddity, and it is a finding.** `handoff/inbox/014-commit-staged-work.md` — the
task file for *this* task — was untracked and had to be committed by the task it describes.
It went into commit 5 rather than a sixth of its own. It is the one path that could not
belong to any group written before it existed.

---

## The Refusal test — evidence hashes verified, not asserted

Two independent checks after all five commits:

```
tests/test_evidence_carry_intact.py    5 passed
independent re-hash of the manifest    179 rows checked, 0 mismatches
```

The second walks `EVIDENCE-CARRY.md`, re-computes sha256 for every recorded path and compares
— deliberately not the suite's own code path, so a bug in the test could not mask a real
mismatch. **All 179 verify.**

## Part 2 — the two stale headers

| file | was | now |
|---|---|---|
| `handoff/inbox/013-adopt-handoff-protocol.md` | RUNNING | **DONE** |
| `handoff/inbox/013c-resolution-d-protocol-and-trees.md` | RUNNING | **DONE** |

Christoph confirmed both; these are not inferences. Both are also in `handoff/accepted/`, so
both are closed on both sides.

**`H8`, `H9` and `M001` left alone**, still declaring `OPEN`. They are carried evidence under
resolution D — editing them breaks `EVIDENCE-CARRY.md`, and asserting a state for a file that
predates the convention is the fabrication the test exists to prevent. The exemption is
working and was not tidied.

---

## Divergences from what was on disk

1. **Three groups was too few.** The staged work contained five distinct efforts. 014 says to
   split further if the shape suggests it, and to name anything that fits none of the three
   rather than forcing it — both done.
2. **014's own task file was untracked** and had to be committed by itself. Unavoidable; noted
   because a reader of commit 5 will find a task file in a commit about header backfills.
3. **`handoff/inbox/H11-*.md` and `handoff/done/H11-*.md` were untracked**, not modified —
   H11 ran after H10's four commits and its own notes were never committed. They went into
   commit 1 with the rest of H11's work, which is where they belong.

## Part 3 — the capture

**Not started yet.** It is **08:13 ET**; the window opens at **09:00 ET**. Nothing in this
task changed any part of 012's configuration: `clientId 11`, depth on ARCA, `quote_basis` and
per-line exchange attribution, three raw append-only streams, gap records, 60 s heartbeat, and
the four live-verification assertions. TWS is up on 7496.

**Nothing pushed**, and the reason stands: the GitHub repo named `momentum` maps to the
**archived** local tree, so pushing this one would put it in the wrong place. That decision is
still open.

`momentum-harness` untouched at `1afcecf`.
