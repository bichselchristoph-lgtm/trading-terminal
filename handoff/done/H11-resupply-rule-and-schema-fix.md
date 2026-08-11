---
id: H11
title: The re-supply rule, SPEC.md §5.5a, and a review of the gate change
status: DONE
owner: claude-code
ran: 2026-08-10
tree: D:\Dev\momentum
---

# H11 — re-supply rule, §5.5a, and the supersession review

**Status** DONE

```
BEFORE : 47 passed
AFTER  : 65 passed
```

Four parts. **The review in §4 found two real defects in the change I made under H10**, and
the normalised check in §3 found **two further occurrences of the `6/9` figure** that the
literal check had never seen — both in `SPEC.md`, not in the mockups.

---

## 1. The re-supply rule

`docs/specs/RE-SUPPLY.md` (status `CURRENT`) and
`tests/test_resupplied_docs_are_repaired.py`. Cited from `CLAUDE.md` in a new subsection.

**Filename note:** H11 spells it `test_respupplied_docs_are_repaired.py`. I used
`test_resupplied_…` — the transposition looked like a typo, and a file nobody can spell is a
file nobody greps for. Say if you want the literal spelling.

Every assertion appends this, which is the entire reason the checks are duplicated here
rather than left to the tests that already cover them:

```
>>> This invariant was applied in the tree and is absent. The file was probably
>>> RE-SUPPLIED from outside and arrived pre-repair. RE-APPLY, DO NOT RE-AUTHOR:
>>> the document that arrived is the current content; the invariant is a repair
>>> that was made to its predecessor. See docs/specs/RE-SUPPLY.md.
```

`test_the_cause_message_is_actually_attached` fails if any assertion in that file loses it.

### The invariant list, verbatim, for quoting into future task files

> 1. **Every `.md` under `docs/specs/` carries a `**STATUS**` header** — `CURRENT`,
>    `SUPERSEDED` or `HISTORICAL` — as its first non-heading block, within the first 10
>    lines. A `SUPERSEDED` header additionally carries a `**by**` naming a file that exists.
>    *Applied under H9 v3 §2.*
>
> 2. **No `claude/`-rooted regime-snapshots path anywhere.** The canonical path is
>    `docs/regime-snapshots/`. Two exemptions, both deliberate:
>    `docs/specs/DRIVE-ARCHIVE-LIST.md` and `handoff/`, which record the old convention as
>    history and must keep saying what it was. *Applied under H8 §B2.*
>
> 3. **`SPEC.md` §13's heading carries the human-reachable-only qualification.** The heading
>    itself, not only a note beside each citation — the Drive and OneDrive entries resolve for
>    Christoph and for nothing automated, and the pointer test deliberately excludes external
>    paths so it will never flag them. *Applied under H9 v3 §5.*
>
> 4. **The mockups keep their repairs.** No `tradesignals` path in any sheet — the paths are
>    `D:\Dev\momentum\`. And sheets **02**, **04** and **05** each carry their
>    `NOT THE CURRENT DESIGN` banner as the **first element inside `<body>`**, because each
>    still renders a panel `SPEC.md` §3.1 resolves by deletion. *Applied under H9 v3 §3d.*
>
> **Adjacent invariants, enforced elsewhere:** `REGIME-PROMPT.md` is v1.2 or higher, states
> `schema_version: 2`, carries the ratification bands with `regime_read_template_2026-08` and
> the reduced-card floor with `prompt_decision_2026-08-10` and `PROVISIONAL`; and no bare
> `6 of 9` — or any separator spelling of that digit pair — in `docs/specs/` outside the
> mockups.

---

## 2. `SPEC.md` §5.5a — the spec no longer rejects its own example

Applied: `schema_version: 2`, a `layer_0.ratification` block carrying all five keys v1.2
emits, and a paragraph naming the cause — **the reduced-card floor**, and the fact that a v1
snapshot has none of those keys so without the bump a v1 snapshot and a v2 one where the
floor did not fire are indistinguishable.

**§3.2's pointer is unchanged, as instructed.** Checked at three sites (lines 65, 207, 708):
`regime_snapshot: {ref, frozen_at, schema_version}` carries no version literal, so the bump
does not touch it. The four properties, the frozen-`frozen_at` rule and the refuse-on-mismatch
rule are untouched — the mismatch rule was correct and the example was stale against it.

### Every key-for-key difference — and it is much larger than the two named

**§5.5a's example is missing three entire top-level blocks**, not just a version field:

| key | §5.5a example (was v1) | v1.2 PART E2 | now |
|---|---|---|---|
| `schema_version` | `1` | `2` | **fixed → 2** |
| `session_date` | ✓ | ✓ | same |
| `frozen_at` | ✓ | ✓ | same |
| `macro_strip` | rows carry `id, value, as_of, band`; **3 rows shown** + ellipsis | rows also carry **`score`**, **`source`**, **`state`**; **all 9 rows shown** | **still differs** |
| **`layer_0`** | **ABSENT ENTIRELY** | `rows_scored`, `denominator`, `denominator_note`, `pre_open_total`, `verdict`, `vetoes`, `vetoes_fired`, `ratification{…}`, `unavailable[{row, reason}]` | **`ratification` added; the other 8 keys still absent** |
| **`layer_1`** | **ABSENT ENTIRELY** | `IWM`/`SPY`/`QQQ`/`RSP` each with `stack`, `dist_25`, `dist_50_per25`; plus `breadth_rsp_vs_spy`, `weakest` | **still absent** |
| `layer_i` | `rows`, `state`, `decisive_row`, `health` | also **`health_downgrade_applied`**, **`provisional`**; rows also carry **`lag`** | **still differs** |
| **`could_not_do`** | **ABSENT ENTIRELY** | list of strings | **still absent** |

**I added only the `ratification` keys, because that is what H11 §2 asked for**, and adding
`layer_1` or `could_not_do` would be authoring spec content rather than repairing it — which
§"Do not" forbids. The `ratification` keys required a `layer_0` block to hang on, since
§5.5a had none; that is the one structural addition.

**So §5.5a's example is now correct about the version and the ratification block, and still
incomplete about everything else.** I added an explicit paragraph saying so and pointing at
PART E2 as the emitted shape, so a consumer written from that block alone is warned rather
than misled. **The full reconciliation is a decision, not a repair** — see Left open.

---

## 3. The `6/9` spelling gap — and two more hops nobody had seen

Normalisation implemented: `\b6\s*(?:/|of|\\)\s*9\b`, case-insensitive, so `6 of 9`, `6 / 9`,
`6/9`, `6  /  9` and `6 OF 9` are one defect. `test_the_bare_count_check_can_actually_fail`
asserts every one of those spellings is caught.

### Every hit under normalisation, including ones the old test passed

| location | form | verdict |
|---|---|---|
| `docs/specs/REGIME-PROMPT.md:132` | `` `6 of 9` `` | citation — the passage forbidding it |
| **`docs/specs/SPEC.md:219`** | ``~~… 02 scores `6/9` out of 11 …~~ **Moot**`` | **NEW — §3.1 defect 2, never seen by the literal check** |
| **`docs/specs/SPEC.md:2248`** | ``… leaves 10, not 9; `mockup-02` inherited `6/9` …`` | **NEW — §12.1's revival note, never seen either** |
| `docs/specs/mockups/mockup-02-regime.html` | `6 / 9` rendered | **exempt by directory — see below** |
| `handoff/**`, `ADOPTION-LOG.md`, the test's own fixtures | various | records and fixtures |

**No bare count exists anywhere.** Every non-mockup occurrence is the figure being *named*,
not asserted.

### The marker list was becoming an exclusion list, so I replaced the rule

Each new hit needed another allowed word (`~~`, `moot`, `inherited`…). That is exactly how an
exclusion list becomes a hiding place. **The principled discriminator is backticks**: both
documents use the word *bare*, and in markdown backticks are what "bare" means — `` `6/9` ``
is the figure being named, `6 of 9 rows scored` is the figure being asserted. The check now
allows a backticked occurrence and catches an unquoted one; the marker words remain only as a
secondary allowance for un-backticked prose.

### The mockup exemption is an obligation on the redraw

`docs/specs/mockups/` is exempt because `mockup-02` renders `6 / 9` and both H10 and H11 say
not to repair it. The sheets are frozen historical artifacts carrying a `HISTORICAL` banner,
not live specification.

**Stated so the redraw inherits it: that exemption is the only thing standing between `6 / 9`
and a fourth hop.** When the mockups are redrawn, the correct completion is to remove the
`docs/specs/mockups/` exemption from `test_no_bare_six_of_nine_anywhere_in_specs`, not merely
to fix the sheet. The comment in the test says so at the exemption itself.

---

## 4. The supersession review — **two of the four were defects**

Read fresh, as someone else's change. H11 is right that the instruction was to stop and say
so, and that I did not follow it. The review below is the argument against my own change.

### Q1. Can `--supersede` land a file at a path with no existing adoption?

**It could. This was a real hole.** `check_3_name_collision` opened with
`if not target.exists(): return` — which fired **before** the supersede branch. So
`--supersede` against a path that was never adopted returned as an ordinary create, and the
`supersedes:` line was **never validated**. H11's phrasing was exact: a create path wearing a
replace flag.

**Fixed.** `--supersede` with no existing target now refuses: *"There is nothing to supersede.
If this is a first adoption, run it without the flag."*
**Tested** — `test_q1_supersede_refuses_when_there_is_nothing_to_supersede`, plus
`test_q1_first_adoption_still_works_without_the_flag` so the fix does not break the ordinary
create it sits in front of.

### Q2. Does it verify the superseded row exists and is not already superseded?

**No, on both counts.** `mark_superseded` scanned `ADOPTION-LOG.md` for the row and, finding
none, wrote the file back **unchanged and silent**. Same when the row was already superseded —
the `and "SUPERSEDED" not in line` guard skipped it without a word.

**Fixed.** Both now refuse, naming the path. **Tested** —
`test_q2_refuses_when_no_log_row_exists`, `test_q2_refuses_when_the_row_is_already_superseded`.

### Q3. Does `ADOPTION-LOG.md` record enough to reconstruct the order?

**No.** Both rows carried the same date and the same path, and **neither pointed at the
other**. Insertion order was the only ordering signal, and nothing recorded or enforced it. A
third version would have produced three indistinguishable rows.

**Fixed.** The new row now opens `**SUPERSEDES \`<path>\` (the marked row below).**` and the
old row now reads `— **SUPERSEDED** <date> by the row above`. **Tested** —
`test_q3_the_two_rows_point_at_each_other`.

### Q4. Would refusals 1, 2 and 4 still fire under `--supersede`?

**Yes, and they always did.** `run_checks` runs 1 → 4 → 2 → 3, and `supersede` is passed only
to check 3. The flag shortcuts nothing. **This is the one of the four that was already
correct**, and it now has tests anyway —
`test_q4_refusal_1_still_fires_under_supersede`, `test_q4_refusal_4_still_fires_under_supersede`.

### Which gained a test

**All four**, plus three more on the original conditions
(`test_supersede_still_refuses_without_a_supersedes_line`,
`test_supersede_refuses_when_the_companion_names_a_different_path`,
`test_a_collision_without_the_flag_still_refuses`). **Ten tests**, run against a temporary
repo so they never touch the real `ADOPTION-LOG.md` or `D:\Dev\_adopt\`.

### My assessment, now that it has been reviewed

**The change was less safe than I claimed in H10.** I wrote that it "still refuses" via three
conditions; two of those conditions were unreachable when the target did not exist, and the
log bookkeeping failed silently in two more cases. The shape was right and the implementation
was not, which is exactly the failure mode that motivated H10's stop-and-say-so instruction.
**H11 was right to ask, and I should have stopped.**

### The `ADOPTED ->` message bug

**Already fixed under H10** (`tools/adopt.py:301`) — it prints `landed`, not the candidate's
name. Verified, no change needed here.

---

## Exit tests

| test | result |
|---|---|
| **Green** | **47 → 65 passed.** 18 new assertions, no failures. |
| **Refusal (a)** | Stripping `SPEC.md` §13's qualification failed `test_invariant_3_spec_section_13_keeps_its_qualification`, and the message carried the full `RE-SUPPLIED … RE-APPLY, DO NOT RE-AUTHOR` diagnosis, not just the missing string. Restored. |
| **Refusal (b)** | A scratch `docs/specs/zz-probe.md` containing `6 / 9` with slash spacing failed `test_no_bare_six_of_nine_anywhere_in_specs`, naming the file, the line and the general form. Removed; 65 passed again. |
| **UAT** | **Yours.** The four answers above are the only judgement here; everything else is a repair. |

I also proved the re-supply failure path *reports* rather than crashing — an earlier version
of that test referenced a constant I had just deleted, which would have raised `NameError`
**exactly when the test was trying to report a real regression.** Caught by planting a probe
file rather than by reading.

---

## What else was authored outside this tree and could arrive pre-repair

| document | tree-side repairs at risk | covered? |
|---|---|---|
| **`SPEC.md`** | **five distinct edits** — §13 heading, §5.1a's two absence states, §6's two-IBKR-paths subsection, §5.5a's schema bump, the snapshot path substitutions, plus its `STATUS` header | invariants 1–3 cover the header, paths and §13. **§5.1a and §6 are NOT covered — a re-supply would silently drop both.** |
| `REGIME-PROMPT.md` | path substitutions, `STATUS` header | invariants 1–2, plus the six `test_regime_prompt_invariants` checks |
| `BUILD-PLAN.md`, `DRIVE-ARCHIVE-LIST.md` | `STATUS` header only | invariant 1 |
| the six mockups | banners, `tradesignals` paths | invariant 4 |
| `handoff/inbox/*` | none — written by chat and carried as evidence, never repaired here | n/a |

**`SPEC.md` is by far the most exposed**, and it is the largest document, so a re-supply is
also the hardest to eyeball. Two of its five repairs have no invariant. That is the gap this
task did not close.

---

## Left open

| # | item | owner |
|---|---|---|
| 1 | **`SPEC.md` §5.5a is still incomplete** against v1.2's emitted shape: `layer_0`'s eight other keys, the whole `layer_1` block, `could_not_do`, and the per-row `score`/`source`/`state`/`lag` fields. Reconciling is authoring, not repair. | `SPEC.md` v1.2 |
| 2 | **§5.1a and §6 have no re-supply invariant.** A fresh `SPEC.md` would drop both silently. | a follow-up to H11 §1 |
| 3 | **The mockup exemption on the `6/9` check** must be removed when the sheets are redrawn — it is the only thing between that figure and a fourth hop. | mockup redraw |
| 4 | **41 adoption decisions** from H9a — 37 `imported`, 4 `unknown`. Untouched. | Christoph |
| 5 | **H8 §A2/§A3** — paste v1.2 into the cloud task and run it once. | Christoph |

**Neither repo pushed.** `momentum-harness` untouched at `1afcecf`. The new tree's H11 work is
staged and **not committed** — you said stop after the done-note.
