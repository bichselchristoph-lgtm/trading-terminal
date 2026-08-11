---
id: 013c
title: Resolution D, protocol amendments, and two new trees
status: DONE
owner: claude-code
ran: 2026-08-11
tree: D:\Dev\momentum
---

# 013c — resolution D, five amendments, two trees

**Status** DONE

```
BEFORE : 67 passed, 2 failed   (013's collision)
AFTER  : 71 passed, 0 failed
```

Resolution D clears both of `013`'s red tests without weakening anything and without editing
a single carried file.

---

## Part 1 — Resolution D

### The exemption, quoted from `tests/test_handoff_state_declared.py`

```python
def carried() -> dict[str, str]:
    """path-in-tree -> source path, from EVIDENCE-CARRY.md."""
    if not MANIFEST.exists():
        return {}
    return {m.group("rel"): m.group("src")
            for m in _ROW.finditer(MANIFEST.read_text(encoding="utf-8"))}


def exempt_paths() -> set[str]:
    c = carried()
    return {p.relative_to(REPO).as_posix() for p in all_task_files()
            if p.relative_to(REPO).as_posix() in c}


def task_files() -> list[Path]:
    """Live handoffs only — carried evidence is exempt under resolution D."""
    ex = exempt_paths()
    return [p for p in all_task_files() if p.relative_to(REPO).as_posix() not in ex]
```

**Derived from the manifest at test time. No list anywhere.**

### Guard 1 — every exempted path must be in the manifest

```python
def test_guard_1_every_exempted_path_is_in_the_manifest() -> None:
    c = carried()
    ungrounded = sorted(p for p in exempt_paths() if p not in c)
    assert not ungrounded, (
        "these task files are exempt from the state-header rule but are NOT in "
        f"{MANIFEST.name}:\n  " + "\n  ".join(ungrounded)
        + "\n\nThe exemption is derived from the manifest and from nothing else. A file "
          "skipped\nwithout a manifest row means the rule has become a hardcoded list."
    )
```

### Guard 2 — no natively-authored file may be exempt

```python
def test_guard_2_no_natively_authored_file_is_exempt() -> None:
    c = carried()
    native = sorted(
        f"{p}  (source recorded as `{c[p]}`)"
        for p in exempt_paths()
        if not c[p].replace("\\", "/").startswith(CARRIED_SOURCE_ROOT)
    )
    assert not native, (...)
```

**The discriminator is the manifest's own `source path` column.** A genuinely carried file was
copied from `D:/Dev/momentum-harness/`; a task file authored here cannot have come from a repo
that is frozen and read-only. That is a property already recorded and hash-enforced, not a
judgment about authorship.

**Result: 38 task files → 21 exempt, 17 live, all 17 declaring a valid state.**

---

## Part 2 — five amendments, as edits to the file on disk

`HANDOFF-PROTOCOL.md` was **edited in place. Not re-authored, and no replacement was accepted
from outside the tree** — that would have been the textbook `RE-SUPPLY.md` instance the task
warned about.

### 2a — rule 4's mechanical facts

> - The mechanical facts are Christoph's: **inbox placement, whether it ran, whether a
>   done-note exists on disk, and whether what reached the design session was all of it.**
>
> **The contents of the note are NOT uniquely his.** … once he pastes it, the design session
> reads the same text, and can read it as well or as badly as anyone.
>
> **Proved on 2026-08-11.** `012a` and `013` both wrote done-notes into `handoff/done/`.
> **Neither reached the design session**, which went on holding a stale `RUNNING` for both. …
> Only Christoph stood where both sides are visible.

### 2b — what `RUNNING` means

> **The five states describe the handoff, not the work's internal progress.**
>
> `RUNNING` means **Claude Code has picked the task up and has not yet reported.** … A
> scheduled window inside a task … does **not** create a sixth state.
>
> **A known limit** … `HANDED OFF` and `RUNNING` are **indistinguishable on disk**. … No test
> can separate them, which is why the state is Christoph's to report and not the repo's to
> infer.

### 2c — copy-and-keep, and where a done-note lives

> **Nothing is ever moved.** A done-note is **created** at `handoff/done/NNN-*.md` as a new
> file; the task file stays in `handoff/inbox/`. …
>
> **no file has ever been moved from `inbox/` to `done/`** — `git log --diff-filter=R -M --
> handoff/` returns nothing across the repository's whole history. … **A done-note is a file
> at `handoff/done/NNN-*.md`**, and this document — the adopted authority on handoffs — now
> says so.

### 2d — my ruling: frontmatter is outside the five-state vocabulary

> The five states describe **the handoff**. A done-note's own frontmatter describes **the
> work**, and the two are different questions.
>
> `013`'s done-note carries `status: BLOCKED ON ONE DECISION`, which is not one of the five and
> **is correct** — the handoff was `RUNNING` (picked up, not yet reported) while the work was
> blocked awaiting a decision. Collapsing those would lose the more useful fact.
>
> **frontmatter may say what it likes; the `**Status**` header line may not.**

**What a future test would need if this is ever reversed:** it would have to parse YAML
frontmatter specifically, distinguish a `status:` key there from the `**Status**` header line,
and apply a different vocabulary to each. **The test's reach was not extended in this task** —
it still reads only the first 20 lines and only the `**Status**` line, which is why `BLOCKED`
was not flagged. That is correct behaviour under this ruling, not a gap.

### 2e — `handoff/accepted/`

> `handoff/done/` … means **Claude Code has finished and reported.** Whether anything is still
> owed is a separate judgment … **`handoff/accepted/NNN-*.md`** — an acceptance record,
> written only when both parties agree nothing further is owed …
> **Claude Code never writes to `handoff/accepted/`**, and never infers acceptance from a note
> it wrote itself.

Created with `.gitkeep`. **Nothing backfilled.**

---

## Part 3 — `CHRISTOPH-TASKS.md` adopted

```
| 2026-08-11 | `docs/specs/CHRISTOPH-TASKS.md` | `design session (Claude chat), 2026-08-11,
in conversation with Christoph` | authored | Items requiring Christoph's own action — UATs and
external enquiries — have had no home. They have been raised in chat and lost at the end of the
session. Placing them in handoff/inbox/ is unsafe because Claude Code executes that folder on
"Do inbox NNN", so a task addressed to a human would be executed by a machine that was not
asked to judge it. | `n/a (not a code tree)` | Christoph |
```

**No `**STATUS**` repair was needed.** It arrived carrying
`> **STATUS** CURRENT · **date** 2026-08-11` in the correct `docs/specs/` form — checked
rather than assumed, as instructed.

**Both of `013`'s design-session defects are confirmed fixed at source:** the companion is
named `CHRISTOPH-TASKS.md.provenance.md` (the gate's convention), and carries `origin`,
`source`, `reason`, `depends` as parsed fields with the prose preserved beneath. The dry run
reported `PASSES all four refusals` with every field populated.

`christoph/open/` and `christoph/done/` created with `.gitkeep`. **`christoph/` was added to
`NATIVE_PREFIXES`** — it holds task files authored here for a human audience, so it takes the
same carve-out as `handoff/`. `test_no_code_tree_is_native` still guards `core/`, `live/`,
`harness/`, `tools/`.

---

## Part 4 — four files created

| path | what |
|---|---|
| `handoff/done/013a-handoff-tree-inventory.md` | reconstructed from the 013a report, plus the H9a finding |
| `handoff/done/013b-state-reconciliation.md` | reconstructed from the 013b report |
| `christoph/open/001-ibkr-totalview-api-entitlement.md` | EXTERNAL |
| `christoph/done/002-handoff-protocol-rule-4-uat.md` | UAT, already answered |

**Nothing was re-derived by re-running anything** — both notes are the reports as given.

**The H9a finding, recorded because it cannot be reopened:** H9a's task file never existed and
its instructions are unrecoverable. `docs/PROVENANCE.md` and H9a's done-note survive, so the
*output* is inspectable — but **if anyone later asks whether the 183-file inventory answered
the question it was set, there is no way to check.**

---

## Part 5

**5a — the depth-budget premise, corrected.** It appears in exactly **one** place:
`handoff/inbox/012-live-qqq-tape-capture.md:102`. **Not in `013`**, which 013c attributes it
to — see divergences. Corrected **inline, with the original ask preserved**, so the record
still shows what was asked and why it was wrong:

> **[CORRECTED 2026-08-11 by 013c §5a: this premise is wrong. Christoph pays the full North
> America subscription set monthly, so depth costs nothing at the margin and does not scale
> with ticker count. The constraint is LINE COUNT, not money — 3 concurrent tick-by-tick
> subscriptions at the documented 0–399-line bracket.]**

**5b — companion naming: closed.** Verified fixed at source on `CHRISTOPH-TASKS.md`. Nothing
to change in-tree.

### 5c — the two unread files. **Both name substantial unresolved work.**

**`condition-codes-config-is-unverified.md`** — frontmatter `status: PARTIALLY_CONSUMED`,
raised 2026-08-05.

> "Checked 2026-08-08 and the banner was understating it. **There is no condition field in the
> delivery at all** … The codes are entirely derived by `identify_auctions`, so the file is not
> a mapping of venue codes to meanings; **it is a declaration of the vocabulary this codebase
> invented.**"

**Still owed, two things:**
1. The banner instructs deleting itself once verified. **It must NOT simply be deleted** — the
   file needs rewriting to say what it actually is, "because a reader today would take 'ITCH
   cross-type codes' as provenance it does not have."
2. The `statistics` schema check. "Venue-published official open/high/low is the only source
   INDEPENDENT of the trades delivery, so it is the only thing that can confirm the
   identification rather than agree with itself."

**`separation-guard-inactive-on-official-venues.md`** — found 2026-08-08, options **RESOLVED**
but the work is not done.

`core/identify.py` applies `min_separation` only when presence is `INCIDENTAL`. XNAS and XNYS
are `OFFICIAL` — **92% of the phase-3 sample** — so on all of it the largest off-book print is
accepted as the cross with no size check.

> "**The distributions overlap.** A coincidence at 1.85x sits above two real crosses at 1.64x
> and 1.65x. Any floor low enough to keep the real crosses admits the coincidence…"
>
> "This is the **third time** an identification rule has died this way… a statistic that
> separates cleanly on the instrument it was derived from, overlapping on one it was not.
> `min_separation: 5.0` came from QQQ. Tenet 6."

**Still owed:** two rows are wrong now — `OMCL 2024-08-01 open` and `ITCI 2025-01-10 open` are
classified as crosses and are not, and they are in the 18,410 records. Acting costs a
`signal_version` bump on every auction-dependent signal plus a rebuild, to be done **once,
together with the `imbalance_lag_seconds` decision — not as two rebuilds.**

**Latent, not live, and it has a trigger:** with a 15 s window those sessions fail to identify,
which is the right outcome. **It becomes live the moment the window is widened** — and the open
result (real crosses at up to 31.5 s) is a genuine reason to widen.

**I acted on nothing in either file, as instructed.**

---

## Exit tests

| test | result |
|---|---|
| **Green** | **71 passed, 0 failed.** Baseline before `013` was 65 passed / 0 failed — the figure of 8 was `momentum-harness`'s and was never this tree's. |
| **Refusal A** | Added a native live task file to `EVIDENCE-CARRY.md`; guard 2 failed: *"these exempt task files were NOT carried from the archived predecessor: `handoff/inbox/013c-…md` (source recorded as `authored-here-not-carried`)"*. Reverted. |
| **Refusal B** | Made the test skip a file with no manifest row; guard 1 failed: *"these task files are exempt … but are NOT in EVIDENCE-CARRY.md: `handoff/inbox/012-live-qqq-tape-capture.md`"*. Reverted. |
| **Refusal C** | A headerless temp file still fails `test_every_task_file_declares_a_state`. Resolution D did not widen into a general escape. Removed. |

**A fixture error worth recording:** my first Refusal B used `006-ranked-watchlist-panel.md`,
which **is** in the manifest, so exempting it created no ungrounded exemption and the guard
correctly stayed green. The guard was right and the test of it was wrong. Re-run with `012`,
which has no row, it failed as designed.

---

## Divergences from what was on disk

`013` found four and every one mattered. This task had three.

1. **The two superseded 013c drafts were never written.** `013c` says to delete
   `013c-resolution-d-and-christoph-tree.md` and `013c-resolution-d-and-two-trees.md` if
   present. **Neither exists**, on disk or anywhere in either repo. Nothing deleted.
2. **The depth-budget premise is in `012`, not `013`.** §5a attributes it to `013`; `013`'s
   task file contains no depth or budget claim at all. The text is at
   `handoff/inbox/012-live-qqq-tape-capture.md:102`, and it is in the *task file*, not a
   done-note. Corrected where it actually lives.
3. **`013`'s own state is now stale, and I did not change it.** `handoff/done/013-*.md` still
   declares `**Status** RUNNING` with frontmatter `BLOCKED ON ONE DECISION`. Resolution D has
   removed the blocker and the remaining 19 backfills are no longer owed — so `013` is
   complete. **013c did not instruct me to change it and I did not**, because a state is
   Christoph's to report. Flagged rather than assumed.

## Every file created

```
docs/specs/CHRISTOPH-TASKS.md                          adopted through the gate
handoff/accepted/.gitkeep                              new tree
christoph/open/.gitkeep                                new tree
christoph/done/.gitkeep                                new tree
handoff/done/013a-handoff-tree-inventory.md            §4a
handoff/done/013b-state-reconciliation.md              §4b
christoph/open/001-ibkr-totalview-api-entitlement.md   §4c
christoph/done/002-handoff-protocol-rule-4-uat.md      §4d
handoff/done/013c-resolution-d-protocol-and-trees.md   this note
```

Modified: `docs/specs/HANDOFF-PROTOCOL.md` (five amendments + resolution D),
`tests/test_handoff_state_declared.py`, `tests/test_adoption_log_complete.py`,
`ADOPTION-LOG.md`, `handoff/inbox/012-*.md` (§5a), and three inbox state headers
(`013a`→DONE, `013b`→DONE, `013c`→RUNNING).

**No file recorded in `EVIDENCE-CARRY.md` was modified and no hash was re-recorded.** Nothing
written into `handoff/accepted/` beyond `.gitkeep`. `records/`, the capture and
`tools/capture_tape.py` untouched; no TWS connection opened. `SPEC.md`, `REGIME-PROMPT.md` and
`BUILD-PLAN.md` untouched. No sixth state.

**Not committed.** `momentum-harness` untouched at `1afcecf`.
