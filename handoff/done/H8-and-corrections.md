---
id: H8 (+ H9 v3 corrections, observations carry, 005 closure)
title: Five items — requirements.txt, observations carry, H9 v3 gaps, 005 closed, H8 §B
status: DONE
owner: claude-code
ran: 2026-08-10
tree: D:\Dev\momentum (except item 1, which is momentum-harness)
---

# Done-note — five items

```
D:\Dev\momentum          34 passed
D:\Dev\momentum-harness  6 failed, 2614 passed, 5 skipped
```

The old repo's six are the five phase-3-gated `test_incomplete_work` failures and the
intended-red open question. **`test_no_secrets.py` is green** — it was 8 failed before item 1.

---

## 1. `requirements.txt` — restored, secrets test green

`git checkout -- requirements.txt` in `momentum-harness`. **It was already restored in the
previous turn, so this ran as a no-op** — recorded rather than presented as new work.

- `test_no_secrets.py`: **21 passed**, from 2 failing.
- Credential shape count in the file: **0**.
- **Not committed, not pushed.** `git status` on the file is clean because it now matches
  `HEAD` (`1afcecf`), so there is nothing to commit.

A repo-wide sweep for `db-[A-Za-z0-9]{20,}` and `DATABENTO_USER` returned three hits, **all
benign and none a credential**: prose in `handoff/done/008a` describing the setx line, a
correct `os.environ.get(...)` in `tools/diagnose_402.py`, and a pip wheel hash in the
gitignored `.venv`.

---

## 2. `docs/observations/` carried — **M001 §4's carry-list omitted it entirely**

**7 files, 0 hash mismatches**, into `D:\Dev\momentum\docs\observations\`, on the evidence
terms: byte-identical, hash-verified, **not through the adoption gate**. Rows appended to
`EVIDENCE-CARRY.md`, which now totals **179** carried files.

| file | bytes | sha256 (first 12) |
|---|---:|---|
| `README.md` | 1,972 | `d4fb72f824f1` |
| `gap-off-lows.md` | 5,072 | `b659e4bf4a50` |
| `replay-slices-do-not-record-their-source-dataset.md` | 3,872 | `0d96ab1f7890` |
| `rvol-registration-is-gated-not-pending.md` | 4,444 | `3fd11d3e0fd2` |
| `session-defined-twice.md` | 3,012 | `77ef9f792731` |
| `vwap-has-no-single-definition.md` | 4,064 | `95d436a1be21` |
| `watchlist-builder-contradicts-ingestion.md` | 1,851 | `072296039234` |

An observation is evidence by §4's own definition — it records what was seen, what produced
it, and what would settle it. The gate's question, *is this worth keeping*, is the wrong
question to ask of one.

**Six were tracked. One was not.** `replay-slices-do-not-record-their-source-dataset.md`, written
today, existed **only as an uncommitted file in an archived repository** — no git history, no
second copy, nothing pointing at it. That is precisely the loss the manifest exists to make
impossible, and it was one `rm` away the whole time.

---

## 3. H9 v3 — **I built to v2 and missed most of v3**

The file I worked from was `H9 — Commit the specs into the repo.md` (v2). `H9-v3-specs-into-new-tree.md`
was not in the inbox when I looked, and I said so at the time. **Re-reading it, seven
requirements were missed.** All are now applied.

| § | requirement | status |
|---|---|---|
| §2 | Status header on every `.md` under `docs/specs/` | **applied — 8 files** |
| §3a | `layer0-amendment-2` → `SUPERSEDED`, note that the open question *moved* | **applied** |
| §3b | `REPO_CONSOLIDATION_PLAN.md` → `HISTORICAL`; record H5's resolution | **applied** |
| §3c | Read `USE_GUIDE.md`, then classify | **applied — `HISTORICAL`** |
| §3d | Banner the mockup sheets; repair defect 4's paths | **applied — 3 bannered, 4 repaired** |
| §4 | `test_every_spec_declares_status` | **applied** (+ a `by`-resolution test) |
| §5 | Mark `SPEC.md` §13's citations in the heading | **applied** |

### The two you asked about specifically

**`USE_GUIDE.md` → `HISTORICAL`.** §3c predicted this as "likely"; the evidence is stronger
than that. Its own title is *"momentum-harness — Use Guide"*. It documents `signals/` (3
mentions) and `data/` (2) — trees commit `7987376` flattened out of existence. It links
`../README.md` as "the working record", which is the README H3 finds describes a tree that
does not exist, and it points at a Google Docs "Signal Framework Spec" with no sync path since
2026-08-09. `PROVENANCE.md` gives it **0 references**. Nothing in it is true of this tree.
Kept as the record of how the harness was operated; **never as setup instructions.**

**`SPEC.md` §13 — marked in the heading, not beside the citations.** The heading now reads
**"13. Sources — the Drive and OneDrive entries are HUMAN-REACHABLE ONLY"**, with the
qualification stated *before* the list: only the `Repo:` line is reachable from this tree, the
sync was removed 2026-08-09, and `test_spec_pointers.py` deliberately excludes external and
absolute paths so **it will never flag them however stale they become**. Each of the two lines
also carries an inline `**(human-reachable only)**`. §5's reasoning is recorded in place: this
is the exact mechanism that cost Layer 0 — a source that reads as live and is reachable by one
person.

### Statuses assigned

| document | status | why, where it differed from v3's expectation |
|---|---|---|
| `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` | `CURRENT` | as expected |
| `DRIVE-ARCHIVE-LIST.md` | `CURRENT` | **v3 did not specify one.** The 32 recommended moves are unmade and H7 owns executing them, so it is still read as instruction, not record. |
| `REPO_CONSOLIDATION_PLAN.md` | `HISTORICAL` | as expected |
| `USE_GUIDE.md` | `HISTORICAL` | as expected, with stronger evidence |
| `layer0-amendment-2-frozen-vs-live.md` | `SUPERSEDED` by `docs/specs/SPEC.md` §5.1 | as expected. Note records that the open question **moved** to `REGIME-PROMPT.md` rather than closing, and that §12.1 preserves the model, so **do not delete**. |
| `mockups/mockup-README.md` | `HISTORICAL` | as expected |

### H5 resolves as: **delete, nothing owed**

`live/_to_merge/` holds only `README.md`. `7987376` added the staged pair; **`20f1d6d` deleted
both** — *"Resolve the staged pair; live/ was broken and nothing noticed."* The gate closed;
the document describing it did not. Nothing to adopt. The originals remain at
`D:\Dev\tradesignals\tradesignals\{core.py,config.py}`. **Nothing was deleted in
`momentum-harness`** — it is frozen under M001 §1.

### Mockups — which got a banner, and which did not

| sheet | banner | why |
|---|---|---|
| `mockup-02-regime.html` | **yes** | renders the Layer 0 AMBER composite with `vetoes 0/4`, the exposure grid, **and** `HALF SIZE` |
| `mockup-04-size-stage.html` | **yes** | renders `HALF SIZE` and the exposure grid |
| `mockup-05-live-context.html` | **yes** | renders the Layer 0 row set and gap-breadth figures; §5.1 removed Layer 0 from the terminal |
| `mockup-01-ingest.html` | **no** | renders no deleted panel — path repair only |
| `mockup-03-watchlist.html` | **no** | same |

Determined by grepping each sheet for `vetoes`, `exposure`, `HALF SIZE`, `Layer 0` and
`NOT BUILT` rather than inferring from filenames. Each banner is the **first element inside
`<body>`**, `position:sticky`, so it is on screen without scrolling — not an HTML comment, not
a line in the README.

**Defect 4 repaired at the cause.** `tradesignals` occurrences: sheet 01 ×2, sheets 02/03/04
×1 each — exactly §3.1's "sheets 01–04". All now `D:\Dev\momentum\`. The `mockup-README.md`
note records v3's uncomfortable correction: `PROVENANCE.md` shows these are **`authored`**, so
this is **not carried-in wrongness — this project wrote a spec naming another project's path.**

### `test_claude_md_pointers_resolve` — was red, now **passes**

v3 says it should pass in the new tree and that red is "a real defect in a five-day-old file,
not inherited debt". **It was right on both counts.** It was red on 4 pointers and found two
genuine errors in the `CLAUDE.md` written at M001:

1. **It claimed chat "sees only the Drive sync of `docs/`, `notes/` and `handoff/`"** — sync
   removed 2026-08-09. Stale the day it was written. Rewritten: no file sync of any kind, and
   Christoph is the only channel, which makes writing things down more important, not less.
2. **`done/` written as a bare fragment** where it meant `handoff/done/`.

The remaining two were fixed as inaccuracies, not exclusions: the refusal-2 row named
`core/`, `live/`, `harness/` as paths when those directories do not exist yet (now plain
names), and `live/tests/` was the **old repo's** path (now `momentum-harness/live/tests/`).
**No exclusion was widened.** Six wildcard tokens remain in the reported "could not classify"
bucket, which is non-empty as v3 requires.

### Adoption rows

All **13** rows in `ADOPTION-LOG.md` have a provenance companion. The four canonical specs cite
**no `PROVENANCE.md` row, because none exists** — they have never been in `momentum-harness`,
so H9a has no row for them; the companions say that in those words. The nine carried files cite
their row verbatim and were verified byte-identical before adoption.

---

## 4. 005 — closed `SUPERSEDED`

Full note at **`handoff/done/005-regime-context.md`**. Nothing built: no code, no tests, no
config. Superseded by `SPEC.md` §3.2 (regime surface deleted), §5.1 (Layer 0 not in the
terminal), §7b.1 (risk from the account — the exposure dial gone).

**Two defects recorded as TRANSFERRED, not closed.** They were never defects *of* 005 — 005 was
the reader that caught them in documents that are still `CURRENT`.

### What `REGIME-PROMPT.md` PART B does about them — checked, and it is a split result

**Defect 1, the reduced-denominator arithmetic.**

- **Fixed:** row 13 is now unambiguously an *opening* row — PART B places it at `09:35–10:00`
  inside rows 12–14 and states rows 1–11 are the pre-open bias, max +11. 005's first point is
  resolved.
- **Decided, and not as 005 guessed:** 005 proposed proportional rescaling as "the obvious
  candidate". PART B decides the opposite — *"the GREEN/AMBER/RED bands were set for a
  denominator of 11 and **do not rescale** … Do not invent a rescaled band."* Anyone reading 005
  alone would build the wrong thing.
- **Not fixed:** PART B gives **no ratification bands at all.** The source doc's "+2 or +3
  ratifies, 0 or +1 downgrades one step, ≤ −1 forces RED" is absent, so 005's sharpest finding
  — that a 2-row opening card makes "ratifies" require a perfect score and turns the card into
  a **downgrade machine** — is neither solved nor contradicted. It is deferred to whoever
  consumes the `pending` rows.
- **The number survived.** PART B's worked example reads **`6 of 9 scored rows`** — the figure
  005 identified as inherited from `mockup-02` and said not to implement. Stated precisely:
  `6 of 9` is *arithmetically legal* if **two** of rows 1–11 are unavailable, and PART B does
  not say which its example assumes. So it is **indistinguishable from the error**, and a reader
  cannot tell them apart.

**Defect 2, the row-14 contradiction — resolved in the spec.** PART B lists row 14 at
`10:00–10:30 | First pullback` in rows 12–14, which "cannot be known at 05:00 — leave them
`null` with `pending: true`." A row that must be null at 05:00 cannot sit in an 08:00 frozen
composite. **Resolved against `mockup-05`**, in favour of the source doc. Transferred rather than
closed because `mockup-05` still renders the wrong arrangement; it now carries a banner, but the
banner says "historical mockup", not "row 14 is in the wrong card".

**Severity dropped, which is the reason to write it down.** §5.1 states the composite's only
consumer was the exposure dial, now gone — so this arithmetic no longer scales position size,
which was 005's stated reason for blocking. But the read still renders GREEN/AMBER/RED prose a
person acts on. **A defect that stops being urgent is the kind that gets closed by accident.**

**Design note 2 shipped, as `REGIME-PROMPT.md` §2.** 005 argued for archiving each read so
Amendment 1 §A1.6's ~1,250-session validation sample accumulates from day one. §2 ships that
argument — *"None of these can be run retroactively over prose, which is why the YAML ships from
day one even though nothing reads it yet"* — via a different mechanism (locked YAML joined on
`session_date`, not 004's two-folder archive), and adds a guard 005 did not: capture is
unconditional, mining requires pre-registration (§12.7). **It is the one part of 005 that
shipped, and it shipped somewhere else.**

---

## 5. H8 — §A skipped, §B shipped

**§A is a no-op, per your decision, not re-opened.** §A1 answers **NO**; the task stays in the
cloud; no local Desktop task; no folder repoint. §A2 and §A3 are yours and were not attempted.

### §B1 — directory

`docs/regime-snapshots/.gitkeep`, tracked. The `.md` and `.yaml` snapshots are **not**
gitignored — `test_snapshots_are_not_gitignored` asserts it with `git check-ignore`, because an
untracked record is not a record and §5.5a's join depends on them being in history.

### §B2 — path substitutions

| file | substitutions |
|---|---|
| `docs/specs/SPEC.md` | **4** (§5.1 ×2, §5.5a block ×2) |
| `docs/specs/REGIME-PROMPT.md` | **5** (header line, the three-outputs block ×2, E1, E2) |
| `docs/specs/BUILD-PLAN.md` | **0** — named in B2, contains none |
| `CLAUDE.md` | **0** — named in B2, contains none |

**Path substitution only.** No prose reworded, no sections renumbered, no threshold, row count,
denominator or YAML field touched.

**Nothing in the specs referenced the old path in a way a plain substitution would have broken.**
All nine were the bare path in running text, a code block, or a heading fragment. The one place
that needed judgement was outside the specs — see below.

### §B3 — the grep test

`tests/test_regime_snapshot_path.py`: `test_no_legacy_regime_snapshot_path`,
`test_snapshot_directory_exists`, plus the gitignore assertion above. Exemptions are exactly
v3's two — `docs/specs/DRIVE-ARCHIVE-LIST.md` (it records the five competing conventions as
history) and `handoff/`.

**One addition, and it is not a widened exemption.** The test skips **its own file**, because
the file that defines `FORBIDDEN = "claude/regime-snapshots/"` necessarily contains the string.
This is the precedent `tests/test_no_secrets.py` already sets for holding credential patterns.
Separately, `test_spec_pointers.py`'s docstring quoted the legacy path while describing the
defect; **I reworded the docstring rather than exempting `tests/`** — the honest fix, since the
description works without the literal.

### §B4 — prohibitions honoured

No snapshot parser. No backfill. No `claude/` symlink or alias.

### Exit tests

| test | result |
|---|---|
| **Green** | **34 passed.** `test_spec_pointers.py`: **8 passed before, 8 passed after** — no worse. |
| **Refusal** | A scratch `docs/scratch-h8-proof.md` containing the legacy path failed `test_no_legacy_regime_snapshot_path` naming **`docs/scratch-h8-proof.md:3`** — file *and* line. Removed; 34 passed again. |
| **UAT** | **Yours, and expected to find an empty directory.** §A1 answered NO, so the cloud task writes to a cloud filesystem and nothing arrives on `D:`. **Recorded as the result, not as an incomplete slice.** |

### The two SPEC.md additions

**§5.1a — absence has two states.** `[ NOT BUILT ]` alone is ambiguous, and the ambiguous half
is the dangerous one: before the open, no file is expected; after the scheduled time, no file
means the pipeline failed, and **the state needing action looked identical to the one that did
not**.

| state | when | renders |
|---|---|---|
| `[ NOT BUILT ]` | no file, scheduled time **not** passed | dim-inverse — refusing, not failing |
| `[ NOT BUILT — OVERDUE Nh ]` | no file, scheduled time passed **N hours** ago | **amber**-inverse — read this and decide |

Amber, not dim, because §4 reserves dim-inverse for refusal and an overdue snapshot is a
failure. Not red — red-inverse is reserved for `[ STOPPED — DAILY LIMIT ]`. The threshold comes
from config (§4.4), keyed to the cron. And it must **never infer the task ran from a file
existing** — yesterday's file left in place is a third failure that reads as success, so the
check is on today's date.

This is not hypothetical: it is currently the every-day state, and an expired claude.ai login
produces exactly the same screen as a normal pre-open morning.

**§6 — two IBKR access paths, named apart.** A table separating the **cloud connector** (own
auth tied to the claude.ai login, no TWS, used by the scheduled pre-market read, **fails by
going quiet**) from **local TWS via `ib_async`** (no cloud dependency, requires TWS, used by the
terminal in a live session, **fails loudly**). The asymmetry is the point — the connector's
silent failure is why §5.1a exists; TWS's loud failure needs no display state, and the terminal
must refuse rather than substitute. Backed by the 008a/008b measurements, including the
`useRTH=0` ADR% error of **+1.1662 points (+44.6 %)**. Closes with the rule that matters: **do
not collapse them into one config key or one client.**

---

## Left open

| # | item | owner |
|---|---|---|
| 1 | **`REGIME-PROMPT.md` PART B has no ratification bands.** Rows 12–14 captured as `pending` with no scoring rule; the 2-row downgrade-machine case unaddressed. | `REGIME-PROMPT.md` v1.2 |
| 2 | **PART B's `6 of 9` example** should name which two rows it assumes absent, or use a different figure. | `REGIME-PROMPT.md` v1.2 |
| 3 | **`mockup-05` still renders row 14 in the frozen composite.** Bannered, but the specific error is unnamed. | mockup redraw |
| 4 | **§3.1 defects 5 and 6 still owed** — box widths 69–71 against a 71-char border; six states specified in prose with no rendered form. | mockup redraw |
| 5 | **41 adoption decisions** from H9a — 37 `imported`, 4 `unknown`. Untouched by any of this. | Christoph |
| 6 | **H8 §A2/§A3** — paste the v1.1 prompt into the cloud task with the updated paths, and run it once. | Christoph |

**Nothing was committed in `momentum-harness`.** The new tree's work is staged but **not
committed** — you said stop after the done-note, and this is it.
