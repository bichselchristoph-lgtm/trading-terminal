# 026 — done — the inbox arrives through Drive

**Status** RUNNING · **Date** 2026-08-13 · **Type** pipeline · **Tree** `D:\Dev\momentum`

> **This note needs to be pasted to chat**, and it is also exported to Drive under 020. Neither
> closes it.

---

## The headline: the differing case fired on its first run, on 026 itself

**`026-for-code-inbox-sync-from-drive.md` is in the Drive folder and in `handoff/inbox/`, and the
two are not the same file.** The repo copy was placed by hand from Drive's document viewer and
carries the viewer's own chrome — `Page`, `1`, `/`, `1`, `100%` above the frontmatter and
`Displaying 026-for-code-inbox-sync-from-drive.md` at the end. The Drive copy is the authored
document.

```
handoff_inbox: 0 new · - · 1 differing
  !! DIFFERS, NOT OVERWRITTEN: 026-for-code-inbox-sync-from-drive.md
       source 2b4b07346453fc8b152b99e868a9b4c9adab10ece8dd0c061906e68b88ae9049
       repo   c7257a6f4600e179fb2e1953dddcd75b31c97c1635a6568b970ebe215d00fbe6
       The repo copy is untouched. A handed-off file that changes breaks a reference
       another party holds, and may already have been read. Resolve by hand.
  ok source folder byte-for-byte unchanged (1 files hashed before and after)
exit 1
```

**Nothing was overwritten and nothing was resolved.** The rule says report and stop, and *this
session is exactly the party the rule protects against*: I had already read the repo copy before
the tool ran. **Deciding which version wins is the judgment the rule exists to keep away from
the process that discovers the conflict.**

**It is trivially resolvable and it is Christoph's to resolve** — the authored bytes are in Drive,
the repo copy is a degraded transcription of the same document, and no content differs beyond the
viewer chrome (checked: the diff is whole-file because line endings differ too, but no sentence
of the task differs). **Say the word and I will replace the repo copy with the Drive bytes.**
Until then `handoff_inbox` exits 1 on every run.

---

## 1. Whether 025's copier was generalised, or a second one written

**Neither — 025 has not shipped, so the shared copier was built here.** 026 says *"if `025` has
already shipped a single-purpose script, generalise it here rather than adding a sibling"*; it
had not, so there was nothing to generalise and a single-purpose script would have been the
sibling 026 exists to prevent.

**One copier, two configured pairs**, exactly as specified:

| File | Role |
|---|---|
| `config/sync.yaml` | Both pairs. Every difference between them is a **value**, not a branch |
| `tools/sync_from_drive.py` | The copier. **No pair-specific code** |
| `tests/test_sync_from_drive.py` | 23 tests, each against real folders under `tmp_path` |

**`test_the_copier_has_no_pair_specific_branches` enforces it**: neither `handoff_inbox` nor
`regime_snapshots` may appear in the copier's code. A branch on `id == "handoff_inbox"` is how
one copier becomes two, and the divergence 026 predicts would then be invisible.

**The two 026-only checks are configured, not hardcoded** — `checks: [filename_convention,
number_collision]` on the inbox pair, `checks: []` on the regime pair. `test_the_checks_are_configured_not_hardcoded`
runs the same inputs with an empty list and asserts no flag and no collision, which is what
proves 025's pair does not silently inherit them.

### The regime pair is configured and deliberately NOT exercised

`regime_snapshots` is in `sync.yaml` because 026 specifies it there. **I did not run it.** 025
owns the gap analysis against the trading calendar, the `git check-ignore` assertion, and the
daily wiring — none of which exists, and `core/session.py` that 025 names **is not in this tree
at all**. Running the copy without them would put a file into `docs/regime-snapshots/` and let
025 look partly done. A `--dry-run` of both pairs shows it is wired:

```
regime_snapshots: 1 new · README-momentum-regime-snapshots.md · 0 differing
  ok source folder byte-for-byte unchanged (1 files hashed before and after)
```

---

## 2. The differing case, demonstrated

**Twice: live, above, and in isolation.** `test_a_differing_file_is_reported_and_never_overwritten`
writes `ORIGINAL BODY` to the destination and `NEW BODY` to the source, runs the real
`sync_pair`, and asserts the destination still reads `ORIGINAL BODY` afterwards. **The assertion
is on the file's bytes, not on the report** — a tool that reports correctly and overwrites anyway
would pass a report-only check.

`test_comparison_is_on_content_not_mtime` sets the two files' mtimes 63 years apart with identical
bytes and asserts `unchanged`. Drive rewrites mtimes on a re-sync or a client reinstall; an mtime
comparison would report a change every time Drive touched the folder and the real changes would
drown in it.

## 3. The convention-flag case, demonstrated

`test_an_off_convention_name_is_copied_AND_flagged`: `notes-about-something.md` is **copied** —
asserted by reading it back out of the destination — **and** listed in `off_convention`, and
`blocked` stays `False`. A refused task file is a task nobody sees, so the flag must not become a
refusal.

`test_a_number_collision_copies_neither`: an arriving `031-for-code-second-thing.md` against an
existing `031-for-code-first-thing.md` copies nothing, leaves the existing file byte-identical,
and sets `blocked`.

**Both were demonstrated against real folders but NOT against the live Drive folder** — see below.

---

## What I could not do, and why

**1. I could not place a test file in the Drive folder, so the end-to-end "a new file arrives"
path is unproven on the real channel.** The standing constraint is *"never write to, delete from,
or rename in the sync folder — a file appearing there because this task put it there would be
indistinguishable from one the design session authored"*, and that reasoning applies to me at
least as strongly as to the tool. **So the copy path is proven on real folders under `tmp_path`
and inferred on the Drive folder.** The live run exercised discovery, hashing, the differing
branch and the source-unchanged check against the real folder — everything except a successful
copy, because the one file there differs.

**The cheap way to close it: drop any `.md` into `D:\claude-googledrive-sync\momentum-inbox-handoff\`
and I will run the copier and quote the report.** One file settles it.

**2. Two of the Done-when criteria are therefore partly inferred**, and I would rather say so than
tick them:

| Criterion | Status |
|---|---|
| A file placed in the Drive folder appears in `handoff/inbox/` and is named in the report | **Inferred.** Proven on real folders, not on the Drive folder — I may not write there |
| A re-run copies nothing and says so | **Met live.** Two consecutive runs, identical output, exit 1 both times from the pre-existing differing file |
| A deliberately-modified inbox copy causes a report and no overwrite | **Met live**, and not deliberately — the modification was already there |
| A file whose name breaks the convention is copied and flagged | **Met in test**, not on the Drive folder |
| The sync folder is byte-for-byte unchanged after a run | **Met live.** Hashed before and after, printed every run |

**3. I did not resolve the 026 conflict**, per the rule. See the headline.

**4. I did not wire a daily run.** 025 owns the scheduling ("run it once a day") and 026 does not
restate it. Wiring a schedule for a pair whose sibling task is unstarted would mean a scheduled
job that exits 1 every day until the conflict above is resolved — noise that teaches people to
ignore it.

---

## One refinement on the task text, stated rather than slipped in

026 specifies the failure line as `0 new · source folder empty or unreachable`. **Those are two
different facts** — an empty folder is a working pipeline with nothing to send; a missing one is
a broken path or an unmounted Drive — and 026's own principle is that outcomes which mean
different things must not read alike. They are printed separately as `source folder EMPTY` and
`source folder UNREACHABLE`, and **only the second is treated as blocking**.
`test_empty_and_unreachable_do_not_read_alike` pins both.

Two further additions, neither requested:

- **`main` exits non-zero when a person must look** (differing, collision, unreachable, or the
  source mutating mid-run). A scheduled run that reports a collision and exits 0 is a report
  nobody reads. **An off-convention name alone does not block.**
- **`--pair typo` exits 2 rather than running zero pairs and exiting 0**, which would read exactly
  like a healthy up-to-date run.

---

## The suite

| When | Result |
|---|---|
| Before 026 | **199 passed, 2 failed** |
| After 026 | **222 passed, 2 failed** |

**23 new tests, all passing.** The two failures are unchanged and both are blocked on a person:
020's UAT gate, and the four task files (`021`–`024`, now `025`/`026` too) carrying
`status: READY` in frontmatter instead of a `**Status**` header.

### One run in the middle went red on a test nobody touched

`live/tests/test_tui_measured_against_its_tile.py::test_shrinking_after_launch_refuses_and_growing_back_restores`
**failed once**, passed immediately in isolation, and passed on the next two whole-suite runs.
It is a Textual pilot whose only synchronisation after `resize_terminal` is a single
`await pilot.pause()` — one scheduler turn, under whatever load the rest of the suite generates.

**Recorded as OBS-022 rather than shrugged off.** That test guards the guard that shipped broken
once, so a false green there is the expensive failure and a false red teaches people to re-run
until green. **Not fixed here — 026 does not own that file.**

## Ledger

**OBS-022**, `OPEN`, review-by 2026-11-13: the flaky TUI resize test above.

## `verify.ps1`

Run at the time recorded in the section below, after the commit.
