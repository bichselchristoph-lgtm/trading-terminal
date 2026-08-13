# 027 — done — rule 15 applied, and the collision the copier could not see

**Status** RUNNING · **Date** 2026-08-13 · **Type** correction · **Tree** `D:\Dev\momentum`

> **This note needs to be pasted to chat**, and it is also exported to Drive under 020. Neither
> closes it.

---

## 5. The Drive channel, proven end to end

**This file arrived through Drive and was placed by the copier, not by hand.** The report line,
verbatim:

```
handoff_inbox: 1 new · 027-for-code-observations-ledger-catchup.md · 1 differing
  !! DIFFERS, NOT OVERWRITTEN: 026-for-code-inbox-sync-from-drive.md
       source 2b4b07346453fc8b152b99e868a9b4c9adab10ece8dd0c061906e68b88ae9049
       repo   c7257a6f4600e179fb2e1953dddcd75b31c97c1635a6568b970ebe215d00fbe6
  ok source folder byte-for-byte unchanged (2 files hashed before and after)
exit 1
```

**Byte-identical on both sides**: `6e9d66aa627b70d82936b6d03e14e06e072a83025bce9a957e46b1f3fdc41812`
in the Drive folder and in `handoff/inbox/`. **This closes 026's one unproven item** — its
done-note recorded the copy path as *inferred on the Drive folder*, and it is now demonstrated on
the real channel. **Nothing was placed by hand and nothing was written to the sync folder**; the
two source hashes are identical before and after.

**Note what the same run did NOT do**: it left `026` alone. One run, one new file copied and one
conflict refused, which is the shape the whole mechanism is for.

---

## 1. The five ledger rows

**OBS-023 to OBS-027**, all `OPEN`, review-by 2026-11-13. Each names its **disabled consumer**,
not just the missing input — a ledger of missing inputs gets skimmed.

| Row | Recurrence | Disabled consumer |
|---|---|---|
| **OBS-023** HYG pre-market credit unreadable at 05:00, 0 shares through 05:15 ET vs a 25,000-share floor | 4th | **Strip row 2 AND veto 2** |
| **OBS-024** No market-wide pre-market gap-breadth source at any hour; 07:00–09:30 also shut at read time | 4th | **Strip row 10 AND veto 4** |
| **OBS-025** VIX-family failure, a different mode each session — snapshot empty, history errored, `is_close` flag | 4th | **Strip row 1's ±3% legs** |
| **OBS-026** COR1M 6-month percentile unavailable (dispersion) | **5th** | **State-machine rule 2, every session** |
| **OBS-027** NYSE up/down volume and % of S&P 500 above 20DMA both unavailable | 4th | **Layer I breadth row half-unsourced** |

**Recurrence counts are quoted from 027's table, and I could not verify a single one.**
`docs/regime-snapshots/` holds `.gitkeep` and nothing else — **zero snapshots** — so there was
nothing to count against. 027 says *"where you can cheaply verify a count against
`docs/regime-snapshots/`, do"*; here the cost is not high, it is infinite. **Every row says so in
its source cell** rather than implying a check that did not happen.

**No disagreement was found because none could be.** That is a weaker statement than "the counts
agree", and the difference is the whole point of the source cell.

Three rows carry a reading I added beyond the supply fact, because the disabled consumer is what
makes them worth holding:

- **OBS-025** — one source failing *three different ways* in four sessions is an integration that
  has never worked, not a supply problem. A fix aimed at any one mode will look successful.
- **OBS-026** — state-machine rule 2 has **never once been exercised**. That is not a degraded
  input; it is an untested rule.
- **OBS-027** — a breadth row that renders from the half of its inputs that resolve, and says
  nothing, is a well-formed value answering a narrower question.

**None of the five was fixed here.** Four are external supply and one is an entitlement. 027 is
explicit that it makes them countable and does not source them.

## 2. HY OAS — confirmed at 2 of 3, not corrected

**Recorded here and deliberately NOT given a row.** 027 states it as unreachable at FRED twice,
not three times, and the threshold is three consecutive.

**I could not verify this either**, for the same reason as above — but the direction of the error
matters and it is safe: if the true count were 3, the cost is a row opened one session late; if a
row were opened at 2, rule 15's threshold would mean nothing from its first application onward.
**A count nobody is holding is the thing rule 15 exists to prevent**, so it is written down here
with its number rather than left in the task file.

---

## 3. Rule 15 cannot be made mechanical — the reason, as a requirement on `REGIME-PROMPT.md`

**Two independent blockers, and either alone is sufficient.**

**(a) `could_not_do` is a list of free-text strings with no key.** From `docs/specs/REGIME-PROMPT.md` §1:

```yaml
could_not_do:
  - "Row 10 gap breadth — no source wired"
  - "COR1M percentile — Cboe page did not load, retried twice"
```

No `id`, no field structure at all. And 027's own table shows the 08-13 entries embed that
session's numbers — *"0 shares traded through 05:15 ET"* — so exact matching cannot group them
across sessions: `05:15` and `05:20` are the same finding and different strings.

**(b) There are zero snapshots.** Any grouping test would pass vacuously today regardless.

**No heuristic was built.** A matcher that silently mis-groups is worse than no test, because its
green would mean nothing.

### What the format must carry, stated as the requirement 027 asked for

> **Each `could_not_do` entry must be a mapping carrying a stable `id`** — unchanged across
> sessions, naming the *finding* rather than the session's measurement — with the session-specific
> numbers in a separate field:
>
> ```yaml
> could_not_do:
>   - id:   hyg_premarket_below_floor
>     text: "HYG pre-market credit — 0 shares through 05:15 ET, floor 25,000"
> ```
>
> The `id` is what rule 15 counts. The `text` is what a person reads.

### What WAS built, and why it is sound

`tests/test_regime_snapshot_could_not_do.py` — **the precondition, which does no grouping at all**:

1. **`test_every_could_not_do_entry_carries_a_stable_id`** — vacuous today, and **red on the
   first snapshot that lands without an `id`**, which is the only moment the format is still
   cheap to change.
2. **`test_the_format_still_lacks_a_key`** — **a tripwire that fires on success.** While the
   prompt documents a bare string list there is nothing to group on; **when the prompt gains the
   `id`, this test goes red**, and its message is the instruction to come back and build the
   matcher. Without it the amendment lands, the precondition starts passing meaningfully, and the
   grouping nobody built is forgotten *exactly the way rule 15 itself was for four days*.
3. **The vacuity prints on every run** via `tests/conftest.py`:
   `regime snapshots: 0 present -- rule-15 grouping cannot run (OBS-028); docs/regime-snapshots/ holds only .gitkeep`

### Both seen red before being accepted green

**The precondition**, against a synthetic snapshot dropped into `docs/regime-snapshots/` and then
removed:

```
E   AssertionError: these could_not_do entries carry no stable `id`:
E       ZZZ-synthetic-probe.yaml[0]  HYG pre-market credit -- 0 shares through 05:15 ET
E       ZZZ-synthetic-probe.yaml[1]  COR1M percentile -- Cboe page did not load
```

**The tripwire**, by temporarily adding an `id:` to the prompt's documented example:

```
E   AssertionError: REGIME-PROMPT.md now documents an `id` on could_not_do entries.
E     **This test failing is the GOOD outcome.**
```

`REGIME-PROMPT.md` was restored and **verified byte-identical by sha256**, and
`test_regime_prompt_invariants` and `test_resupplied_docs_are_repaired` both pass afterwards.

**Deviation from the task's demonstration, stated:** 027 says *"delete one of Part 1's rows, watch
it fail, restore it."* **That demonstration is not available** — it presumes the grouping test,
which is the thing that could not be built. Deleting an OBSERVATIONS row today fails nothing. The
two red demonstrations above are what exists in its place.

---

## 4. The arriving-vs-arriving collision

**Fixed.** `by_number` is now updated as each file is copied, so a second arrival with the same
`NNN` collides with the first.

```
!! NUMBER COLLISION, NOT COPIED: 031-for-code-beta.md
     clashes with 031-for-code-alpha.md (copied by this run)
     That first file IS placed and stays -- nothing this tool wrote is removed by it.
```

**The origin is carried in the report, in those words**, because *already in destination* and
*copied by this run* need different responses from a person.

**Seen red against the pre-027 behaviour.** Removing just the registration line reproduces the old
tool, and the new test fails exactly as it should:

```
E   AssertionError: the first arrival is placed
E   assert ['031-for-cod...code-beta.md'] == ['031-for-code-alpha.md']
E     Left contains one more item: '031-for-code-beta.md'
E   AssertionError: assert 0 == 1   # len(collisions) == 0
```

**Both files copied, zero collisions reported.** Restored, and green.

Two tests: `test_two_ARRIVING_files_with_the_same_number_collide` and
`test_the_arriving_collision_is_caught_in_dry_run_too` — a dry run that misses a collision would
green-light a real run that hits it.

**027's framing is adopted rather than argued with:** this was not a defect against 026, whose
text describes the check against *an existing inbox file*. It was a gap in the mechanism, and a
reachable one.

---

## 6. What I could not do

1. **Verify any of the five recurrence counts, or HY OAS's 2 of 3.** `docs/regime-snapshots/` is
   empty. Recorded in every row's source cell.
2. **Build the rule-15 grouping.** Part 3 above; it is a requirement on `REGIME-PROMPT.md`.
3. **Run the task's own red demonstration** for Part 2, since it presumes the grouping.
4. **Resolve the `026` conflict**, which keeps `handoff_inbox` at exit 1 on every run. Confirmed
   this session that the repo copy is *exactly* the Drive copy plus 8 leading viewer-chrome lines
   (`Page`, `1 / 1`, `100%`) and one trailing `Displaying …` line — **both files are CRLF, so
   line endings are not involved, and no sentence of the task differs.** Christoph said he would
   resolve it himself; I have left both copies untouched.
5. **Populate `docs/regime-snapshots/`.** 025 owns it and remains unstarted — see Part 4 below.

## Part 4 — the regime pair, recorded so it is not re-litigated

**No work, as 027 specifies.** 026 declined to run the `regime_snapshots` pair because 025 owns
the gap analysis, the `check-ignore` assertion and the daily wiring. 027 confirms that call.

**One thing found while checking:** the Drive regime folder contains **only a README** and no
snapshots, and that README states *"Publishing to this folder starts with REGIME-PROMPT v1.7."*
**So the empty folder is not a sync failure — publishing has not begun.** It also means the
tree's `REGIME-PROMPT.md` is behind the scheduled task's stored prompt, which that README names as
the source of truth. Worth knowing before 025 runs and reads an empty source as broken.

---

## The suite

| When | Result |
|---|---|
| Before 027 | **222 passed, 2 failed** |
| After 027 | **227 passed, 2 failed** |

Five new tests. The two failures are unchanged and both blocked on a person: 020's UAT gate, and
the task files carrying `status: READY` in frontmatter instead of a `**Status**` header — **now
including `026` and `027` themselves**, since both arrived in that form.

## Ledger

**OBS-023 – OBS-027** (the five, above) and **OBS-028** (rule 15 cannot be mechanised against the
current format). All `OPEN`, review-by 2026-11-13.

## 7. `verify.ps1` — run at 2026-08-13 15:04:34 +02:00, after the commit

| Section | Output |
|---|---|
| 1 SUITE | `2 failed, 227 passed in 4.69s` — the two named above |
| 2 GIT STATUS | clean, no uncommitted paths |
| 3 HEAD | `6e6cf56ccd25495360c82e9baf8ad05e373044ab` |
| 4 EVIDENCE | 179 rows checked, **0 mismatches, 0 missing** |
| 5 EXPORT | both mirrors at `6e6cf56`, exported `15:04:33+02:00`, **87 / 13 files, counts match the sources**, tree clean at export |

**As under 020 and 026, this section is one commit behind the tree by construction** — a note
recording its own verification cannot be the file that verification described.
