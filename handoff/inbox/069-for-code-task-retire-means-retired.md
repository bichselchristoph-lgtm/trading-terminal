---
id: 069
class: admin
unblocks: NOTHING
depends: none
touches: tools/sync_from_drive.py, tools/now.py, config/sync.yaml
---

# 069 — Retire means retired

**If `handoff/inbox/069-for-code-task-retire-means-retired.md` exists in your tree and `handoff/done/069-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## Why this exists

Christoph closed `c032`, `c035` and `c036` — moved each file from `christoph/open/` to `christoph/done/` — three times each. They came back every time.

**The cause is not a bug in the copier. It is the copier working exactly as specified against a destination that uses a different lifecycle than the source assumes.**

`christoph/open/` is **copy-verify-retire**: the file leaves the destination when it is done. The Drive source `momentum-christoph-open` still holds it. The copier's rule is *not in the destination → copy it*. So every run resurrects every retired item, forever.

Pairs 1, 2 and 4 do not have this problem and **must not be changed**. `handoff/inbox/` is copy-and-keep — nothing ever leaves it, so the rule holds there correctly. **This is a pair-3-only defect.**

Christoph has already removed the three files from the Drive folder by hand, so the immediate bleeding has stopped. **This task makes it not recur.** Until it lands, every future closure needs the same manual Drive-side step, and nothing tells him when he has forgotten it.

---

## Part A — pair 3 suppresses what is already done

In the inbound copier (`tools/sync_from_drive.py`), for **pair 3 only**:

Before copying a source file, read the set of leading id tokens present in `christoph/done/`. If the source file's leading id token is in that set, **do not copy it. Count it as suppressed and name it in the report.**

**The id token is the leading run of characters before the first `-` in the filename, taken whole, including any letter suffix.** `035` and `035a` are different tasks — `NOW.md`'s own `superseded` line lists them separately — so `035a` in `christoph/done/` **must not** suppress `035`.

### Fail closed, in the direction that stays loud

**If `christoph/done/` cannot be read** — missing, empty, permission error, any reason — **suppress nothing. Copy everything. Say so by name in the report.**

A suppressed live item is invisible and nobody knows to look for it. A resurrected dead one is merely annoying and Christoph can see it. **Fail toward the annoying one.**

Do not silently treat an unreadable directory as an empty one. An empty `christoph/done/` and an unreadable `christoph/done/` produce the same suppression set and must produce **different report lines**.

### The report

§4a: *silence must be meaningful*. These four must not read alike:

```
0 new · up to date
0 new · 3 suppressed (032 035 036) · up to date
0 new · christoph/done not readable — nothing suppressed
0 new · source unreachable
```

**The suppressed count self-clears**: it goes to zero on its own the day Christoph removes the retired files from Drive, and it never goes to zero while they are there. That is the property §4a asks for — a count, not a clock.

---

## Part B — `NOW.md` renders two different tasks identically

Current output, from the real file:

```
ready now    006 007 025 031 033 040 048 049 051 066 067
on christoph 033
```

**Those are two different tasks.** `h033` is a handoff task in `handoff/inbox/`; `c033` is a Christoph item in `christoph/open/`. `NOW.md` prints both as `033`, on adjacent lines, with nothing distinguishing them.

§5 already rules this: **in chat a number always carries its sequence** — `c015`, `h015`, `S011`, `B-044`. `NOW.md` is not chat, and it is the file a session reads to decide what to pick up. **A reader who takes `033` off the `ready now` line and opens the wrong file has been misled by the terminal's own state file.**

In `tools/now.py`, prefix every rendered id with its sequence: `h` for `handoff/`, `c` for `christoph/`, `S` for build slices where they appear. Apply it to every line that renders ids — `ready now`, `blocked`, `on christoph`, `superseded`, `done`.

**Do not renumber anything on disk.** The filenames are identifiers. This is a rendering change only.

---

## Part C — the four numbers rule 16 asks for

Current output:

```
admin:product this stretch   20:11
```

Rule 16 asks for four numbers, and this is two of them fused into a ratio:

```
admin this stretch           20
  naming a product task       ?
product this stretch         11
days since last product task  ?
```

**The two missing ones are the two that carry the signal.** The gap between *admin count* and *how many of those name a product task* is what makes an admin chain visible in arithmetic instead of needing a prohibition. A bare ratio does not show it.

Render all four. `naming a product task` counts admin task files whose `unblocks:` line names a **product** task — `unblocks: NOTHING`, a blank line, a missing line, and an `unblocks:` naming another admin task all count in the first number and **not** in the second.

`days since last product task` is derived from the tree: the most recent `handoff/done/` note for a task file declaring `class: product`. **If it cannot be derived, print why, not a number.**

**`064` Part A refused this change and the refusal was correct** — it was scoped to `verify.ps1` and this lives in `tools/now.py`. The refusal is why it is here. **Nothing else picked it up in the meantime, which is the thing worth noticing:** a correct refusal with no destination is a dropped requirement, and it sat dropped for one full task cycle.

---

## Exit tests

**All three are required. The refusal test is not optional.**

| | Test |
|---|---|
| **Green** | A file in the pair-3 Drive source whose id token is present in `christoph/done/` is **not** copied, and the run report names it in the suppressed list. A file whose token is **not** present still copies normally in the same run. Exercise `035` against a `christoph/done/` containing `035a` and confirm `035` **is** copied. |
| **Refusal** | With `christoph/done/` unreadable, **nothing is suppressed**, every source file copies, and the report says `christoph/done not readable — nothing suppressed`. **Demonstrate red before green** — show the test failing against the pre-change code, then passing. |
| **UAT** | Christoph runs a sync with at least one retired item still in the Drive source and confirms it does not reappear in `christoph/open/`, and that a newly added item does arrive. Written as `christoph/open/NNN-for-christoph-task-*.md` by you, not by this session. |

---

## Scratch

**Any measurement scratch lives in `$env:TEMP`, never the repo.** The one persistent file this task may write is the pair-3 report line inside the existing run record — no new state file.

**A note on `verify-failures.txt` from `068`, in passing, not a change request.** It is gitignored persistent state, so the design session cannot read it and the delta only exists for whoever reads `verify-output.txt` after that run. That is fine under the main-checkout ruling and **not** fine if runs happen in per-task worktrees, where every run would be a cold start reporting *no previous run recorded* forever. **Say which is true in your done-note. Do not change anything about it in this task.**

---

## Closing

Sync, work, verify, export, push. From the main checkout.

`verify.ps1` is the last action. **Do not paste or summarise it** — state that it ran, and when.
