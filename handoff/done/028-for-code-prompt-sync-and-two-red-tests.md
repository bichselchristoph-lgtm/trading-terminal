# 028 — done — a correction applied late, a sync that could not happen, and two attributed reds

**Status** RUNNING · **Date** 2026-08-13 · **Type** correction · **Tree** `D:\Dev\momentum`

---

## 1. `027` had already run. Part 1 is a fix, not a precondition

**`028` says "Run this before `027`." It arrived after.** `handoff/done/027-for-code-observations-ledger-catchup.md`
exists and was committed at **`6e6cf56`**, before `028` was authored into Drive at 15:17.

**So the two corrected rows were already in the ledger as live `OPEN` blindnesses**, and Part 1
became a repair of committed state rather than a precondition that prevented it. Both are now
corrected:

| Row | Was | Now |
|---|---|---|
| **OBS-023** HYG pre-market credit | `OPEN`, *"disabled consumer: Strip row 2 AND veto 2"* | **`DROPPED`** — *resolved by cutting the row, v1.7*. The four sessions of evidence are kept; what changed is that they describe **history**, not a blindness |
| **HY OAS at 2 of 3** | A watch instruction in `027`'s done-note §2 | **`OBS-029`, `DROPPED`** — Layer I row 1 was cut in v1.7 and replaced by *credit, prior session* from IBKR daily bars |

**The other four stand unchanged and are still live:** OBS-024 gap breadth, OBS-025 VIX-family,
OBS-026 COR1M dispersion, OBS-027 NYSE breadth.

**One deviation, stated.** `028` says of HY OAS: *"delete this instruction entirely."* I entered a
`DROPPED` row instead of deleting. The ledger's own rule is that a finding leaves by `PROMOTED` or
`DROPPED` **with the reason recorded**, never by disappearing — *"deleting one silently loses the
fact that someone once thought it mattered."* A `DROPPED` row satisfies the instruction's intent
(nothing is open, nothing is being watched) while keeping the count findable by whoever later
wonders what happened to it. **`tests/test_observations_ledger.py` also pins a row-count floor**,
so deletion would have gone red regardless.

**Why `027` was wrong, carried into the resolution rather than left in a task file:** it took its
counts from the 2026-08-13 snapshot, produced under prompt **v1.6**. The prompt had already moved
to v1.7 and the snapshot could not know it. **A count read from an artifact is a count as of that
artifact's world** — this project's first pattern, a well-formed value answering a different
question, in a task whose own Part 1 warns about it.

---

## 2. The version pin: seen red. **v1.8 was never delivered, so it cannot be seen green**

### The pin, red

Bumped to `1.8` and run against the tree's copy:

```
E   AssertionError: REGIME-PROMPT.md is v1.2. v1.2 added the ratification bands and the
E     reduced-card floor; anything older reintroduces the defects H10 closed.
E   assert (1, 2) >= (1, 8)
1 failed, 1 passed, 12 deselected
```

Reverted; `14 passed`.

### **The tree holds v1.2, not v1.7 — and that changes Part 2's premise**

`028` says *"do not edit the v1.7 copy into shape."* **There is no v1.7 copy.**
`docs/specs/REGIME-PROMPT.md` line 5 reads:

```
**Version** 1.2 · **Date** 2026-08-10 · **Companion to** `SPEC.md` §3.2, §5.5a
```

**The tree is six versions behind the trigger**, not one. v1.3 exists only in `D:\Dev\_adopt\`,
unadopted; v1.4–v1.8 have never been in this tree in any form.

### v1.8 has not arrived through the Drive channel

Checked at 15:20. `D:\claude-googledrive-sync\momentum-inbox-handoff\` holds exactly three files —
`026`, `027`, `028` — and the regime folder holds only its README. **No prompt document of any
version has been delivered.**

`028` says the design session *will* deliver it as a separate file, and forbids reconstruction:
*"do not reconstruct it from this task."* **So Part 2 item 1 is blocked on delivery and I did not
attempt it.** Reconstructing a spec from a task file's summary is the one thing `CLAUDE.md` names
as worse than an absent spec, because it would be read as the record.

### I did not leave the pin at 1.8, and this is a judgment call

**Bumping it now creates a third permanently-red test — in the task whose Part 3 argues that two
are already one too many.** *"A test red on every run for a week has stopped carrying
information… two permanently-red tests are how a third one arrives unnoticed."* Adding a third
knowingly, in that task, would be perverse.

**The pin stays at `1.2` until the v1.8 text lands.** The moment it does, the bump is a one-line
change and the test goes green in the same commit — which is *"seen red, then green"* as `028`
intends it, rather than red for days.

**If Christoph would rather the tree carry a standing red saying "the prompt is stale", say so and
I will bump it.** It is one line and I have no strong view; what I object to is doing half of a
two-step and calling it done.

---

## 3. The two `OBSERVATIONS.md` rows, quoted

**OBS-030 — the unwatched prompt sync**

> **Nothing watches whether an authored document reached the thing that runs it.**
> `REGIME-PROMPT.md` **v1.7 was authored on 2026-08-13 and never pushed to the scheduled task's
> trigger — it was live nowhere**, while asserting in its own §0 that it *was* the stored prompt.
> It passed every check available to it. The version pin compares the TREE copy to the AUTHORED
> document; **no check compares the authored document to the DEPLOYED one.**
>
> *What would settle it:* **A gap with no owner, and that is the finding.** Neither side can close
> it: this session cannot read the trigger and neither can the tree. It needs either a trigger that
> publishes its prompt version somewhere both can see, or a person who checks. **`028` explicitly
> forbids building it here** — a check that cannot reach the thing it checks would be theatre.

**OBS-031 — the state header versus the immutable channel**

> **A mutable state cannot live in an immutable file, and the handoff convention now requires
> both.** The five states describe a handoff that PROGRESSES; the Drive channel makes a task file
> IMMUTABLE — `026`'s copier refuses to overwrite one that differs. **`**Status** WRITTEN` is true
> when written and wrong within the hour**, and correcting it in the inbox copy makes that file
> differ from its Drive original forever. Task files `021`–`027` carry `status: READY` frontmatter
> instead of the header, and `test_every_task_file_declares_a_state` has been red on every run
> since.
>
> *What would settle it:* **Christoph's decision, and `028` records the recommendation without
> implementing it:** the header becomes a **provenance stamp** — the state at authorship, never
> updated — and the live state moves to a ledger the protocol document owns. **Backfilling
> `021`–`027` is explicitly the wrong fix**: it would make seven files differ from their Drive
> originals and the copier would report seven conflicts on every run, forever.

**Part 3b: no action taken**, as instructed. `test_every_declared_uat_exists_as_a_file` is red
because `020`'s note declares a UAT with no file in `christoph/open/`. **No Claude writes to
`christoph/`.** Named, attributed, not inherited.

**`028` carries its `**Status**` header correctly**, and is the first task file to do so.

---

## 4. Part 4 — answered from the folder, and the premise is off by one degree

**`022` is done.** Evidence, all from the tree rather than memory:

| Check | Result |
|---|---|
| `handoff/done/022-for-code-secrets-hygiene.md` on disk | **17,190 bytes**, 2026-08-13 11:47 |
| Committed | **`92f1695`** *"The credential scan was answering a narrower question than its name"* |
| Its own header | `**Status** RUNNING · **Date** 2026-08-13 · **Type** housekeeping` |
| Exported to Drive | present at `momentum-code-handoff/done/`, **17,190 bytes** — same size |

**But `023`'s done-note never says `022` is unstarted. It does not mention `022` at all** —
`grep -c "022"` over that file returns **0**.

**The false claim was in the session's chat reply to Christoph, not in any note.** I wrote
*"`022`, `024`, `025` are queued and unstarted"* after being handed the queue *"023 then 022 then
024 then 027 then 025"*, and I described the queue rather than checking the folder — for a task I
had personally completed ninety minutes earlier.

**That sharpens `028`'s diagnosis rather than contradicting it.** `028` guessed the error had
*"arriv[ed] in the part of the note nobody verifies."* It is worse: **it arrived in the part of
the report that is not a note at all.** `verify.ps1` and the v1.2 gate cover the done-note; the
prose I type to Christoph has no gate, no artifact, and no test — and it is the part he actually
reads.

**Not proposing a mechanism for it here.** It would be a fourth thing to keep green, and `028`'s
own Part 3 is an argument against adding those casually.

---

## 5. What I could not do

1. **Land `REGIME-PROMPT.md` v1.8.** Not delivered to any Drive folder; reconstruction is
   forbidden and would be the worse failure. **Blocked on the design session.**
2. **See the version pin green.** Follows from 1. Red was demonstrated; green needs the text.
3. **Correct `027`'s done-note in place.** Its §2 still reads *"HY OAS — confirmed at 2 of 3"*.
   **Left as written**: a done-note records what was believed at the time, and the correction
   lives here and in `OBS-029`'s resolution, which is where someone reading the ledger will find
   it. **If notes should be corrected in place, that is a convention change and not mine to make.**
4. **Fix either red test.** Both are attributed, neither is actionable from this side.
5. **Resolve the `026` conflict**, still open, still exiting 1 on every copier run.

---

## The suite

| When | Result |
|---|---|
| Before `028` | **236 passed, 2 failed** |
| After `028` | **273 passed, 2 failed, 1 warning** |

**`028` added no tests and changed no code** — it is a correction task. **The +37 is not mine.**

### Another session is working in this repository at the same time

**`0acfb84` — *"Five streams share one account, and the quiet symbol is the slow one"* — is task
`021`, committed by a concurrent session between my `faee78d` and my `1559320`.** It brought
`tools/probe_keepuptodate_scale.py`, `tools/analyse_keepuptodate_scale.py` and
`tests/test_keepuptodate_scale.py` (**37 tests**), with their `BOOTSTRAP_ALLOWLIST` entries.

**This explains `023`'s stray file.** `023`'s done-note records that `git add -A` swept in a
406-line script authored *"three minutes before I committed"* and that I un-tracked it. It was not
a stray: **it was another session's work in progress**, and my `faee78d` pulled it back out of the
index. That session committed it properly afterwards, so nothing was lost — **but the un-tracking
was the wrong call made for a reason that looked right.** `023`'s entry stands as written; this is
the fuller account.

**The finding is not the count, it is that I wrote a number I had not re-measured.** The table
above said `236 / 236` when I drafted this note. **That is Part 4's failure again, in the same
task that diagnoses it** — a figure carried from earlier in my own context instead of read off a
run. It was caught by the commit's own suite line, which is the mechanism working.

**Concurrent sessions are not accounted for anywhere in the handoff convention.** `verify.ps1`
section 2 shows uncommitted paths and section 3 shows `HEAD`, but nothing distinguishes *my*
changes from another session's, and a done-note's suite count silently becomes a claim about
someone else's work. **Not solved here.** Named because it will recur.

**The two failures are unchanged** and this note stops calling them *"the same two people-blocked
failures"*: they are **OBS-031's state-header conflict** and **`020`'s unplaced UAT file**, and
both now have owners.

**The warning is pre-existing and not from this task**: `eventkit/util.py:21 DeprecationWarning:
There is no current event loop`, raised inside the `ib_async` dependency chain, surfaced by `021`'s
new tests importing it.

## Ledger

**OBS-023** → `DROPPED`, **OBS-029** → `DROPPED` (both with resolutions), **OBS-030** and
**OBS-031** → `OPEN`, review-by 2026-11-13.

## 6. `verify.ps1`

Run at 2026-08-13 15:24 +02:00. **Output not quoted, per HANDOFF-PROTOCOL v1.2** — it is in
`verify-output.txt` at the repo root.
