# 016 — the verification harness, three record-keeping defects, and a ledger for findings

**Status** WRITTEN · **Date** 2026-08-12 · **Type** infrastructure · **Tree** `D:\Dev\momentum`

> **Do not run this concurrently with `S009a`.** Both touch `tests/`. `S009a` is mid-flight and
> its done-note is owed. Run 016 only after `S009a` has reported.

---

## Why this task exists

**Christoph cannot verify what he carries.** A done-note is machine-to-machine communication
passing through a human who can see that it arrived and that all of it arrived, but not
whether 179 hashes verified or a suite really passed. On 2026-08-12 the design session tried
to check two notes against each other and could not: `015` claimed `103 passed, 1 failed`,
`012` claimed `2 failed, 102 passed`, and the tree was actually at **126 tests, 2 failed, 124
passed**. Neither note described this tree. Nothing was contradicted and nothing was
confirmed.

**Part 1 is the fix for that**, and it is the reason for the task. Parts 2–4 are three defects
found while running the gate. Part 5 is the one that outlives all of them.

---

## Part 1 — `verify.ps1`

**Create `D:\Dev\momentum\verify.ps1`.** One command, four facts, output Christoph can read
without knowing what any of it means.

It prints, in this order, each under a labelled heading:

1. **The suite result** — the pytest summary line, verbatim. Not a claim that it passed.
2. **`git status --short`** — every uncommitted path.
3. **`git log -1 --format="%H %s"`** — the current HEAD.
4. **The evidence re-hash** — walk `EVIDENCE-CARRY.md`, recompute sha256 for every recorded
   path, print `N rows checked, M mismatches` and name any mismatch.

**Item 4 must not call the test suite's own code.** `014` did this correctly and the reasoning
is its: an independent path means a bug in the test cannot mask a real drift. Reimplement the
walk in the script rather than importing `test_evidence_carry_intact`.

**Constraints.**

- **It must never modify anything.** No writes, no `git add`, no fixture creation. If it
  cannot compute something, it prints why and continues to the next section.
- **It must not interpret.** No "all good", no green/red, no exit-code-as-verdict. Four
  sections of raw fact. The reading belongs to the design session; **this script's whole
  value is that it does not have an opinion.**
- **It must state its own runtime** at the end, and **warn if the suite took over 100
  seconds** — see Part 2, and because a 2-minute default cap currently fails it by 8 seconds
  and reads as a hang to anyone who has not seen it before.
- Uses `C:\venvs\trading\Scripts\python.exe`. There is no `python` on PATH.

**Then run it once and paste the whole output into the done-note**, so its first execution is
itself a record.

---

## Part 2 — `test_no_secrets.py` reads 1.8 GB on every run

**Observed:** the suite went from 1.4 s to ~128 s once `records/tape/` filled. `test_no_secrets.py`
includes `.jsonl` among its text suffixes and its `SKIP_DIRS` has no entry for `records/`, so
the credential scan reads every byte of depth data on every run.

**The predecessor's version skipped `records` and `records_truncated` explicitly.** That was
dropped when the test was rewritten for this tree under M001, and the defect was invisible
until something large landed.

**Fix:** restore the skip. `records/` is gitignored and never committed, so scanning it for
committed secrets answers a question nobody asked.

**Do not** widen the suffix list, add a size cap, or make the scan sample. A size cap would
silently stop scanning a large file that *is* tracked, which is the failure this test exists
to catch.

**Report the before and after runtime as measured numbers**, not as "much faster".

---

## Part 3 — the `christoph/` exemption, and why a prefix list is the wrong shape

**Observed:** `test_no_legacy_regime_snapshot_path` fails on
`christoph/done/006-h8-snapshot-path-fills.md:12`, which contains `claude/regime-snapshots/`
while *describing the change H8 made*. It is a historical citation, not a live path.

`EXEMPT_PREFIXES = ("docs/specs/DRIVE-ARCHIVE-LIST.md", "handoff/")` at
`tests/test_regime_snapshot_path.py:37`, and the docstring's stated reason for exempting
`handoff/` is that **task files and done-notes record what the convention was at the time they
were written, and rewriting them would falsify the record.**

**That reason describes `christoph/` word for word.** The list simply predates the tree
existing. The test's own message forbids widening the exemption — but that prohibition is
aimed at hiding *live* breakage, which this is not.

**So: exempt `christoph/`, and change the shape of the discriminator while doing it.**

**A prefix list will need widening at the next tree**, and a list that grows is the hiding
place this project keeps naming. **Derive the exemption from the property instead**, the same
way Resolution D derived the evidence exemption from `EVIDENCE-CARRY.md`. The property is:
*this file is a dated record of a past state rather than a live pointer.*

**Choose the discriminator and defend it in the done-note.** Two candidates, neither
mandated — pick the one you can test, or propose a third:

- **Structural** — the citation appears inside a document whose own header declares a handoff
  state or a date, i.e. it is a record by construction.
- **Positional** — the same discipline as `HEADER_LINES` and `UAT_ROW`: the path appears in
  prose describing a change rather than in a config value or an import.

**If neither can be made to work, say so and widen the list** — but say why the derivation
failed, because that is the finding. **Do not silently fall back.**

**A guard is required either way**, mirroring Resolution D's two: something that fails if the
exemption ever covers a live pointer.

---

## Part 4 — `CLAUDE.md` line 159, and the version it forces

**Observed:** `test_claude_md_pointers_resolve` fails on `CLAUDE.md:159  \`done/\``.

**The cause is a design-session defect, stated so it is not diagnosed as something else.** The
line reads *"Copy to `done/`, verify byte-identical"* — prose shorthand for
`christoph/done/`, which the pointer test correctly reads as an unresolvable repo-relative
token.

**Fix:** `done/` → `christoph/done/`. One word.

**Then bump `CLAUDE.md` to v1.2 and add its history row.** Rule 9 has no size threshold: a
version that skips small fixes stops being a reliable identity for the file. The row should
say what it was — a broken pointer introduced by the v1.1 re-supply, not a content change.

**Edit in place. Do not accept a replacement from outside the tree**, and do not re-author.
`CLAUDE.md` is currently modified in the working tree and the design session cannot see what
else has changed since it was pasted.

**Check the same file for other bare-folder shorthand** while you are in it — `open/`,
`done/`, `accepted/`, `inbox/` written without their parent. Report any found; fix only those
the pointer test flags.

---

## Part 5 — the observations ledger, and the trigger that makes it real

**This is the part that outlives the task.**

**Observed:** findings are captured in done-notes and never acted on. There is no mechanism.
`docs/observations/` exists as a folder and the active `CLAUDE.md` says nothing about how
anything leaves it.

**And the rule that governs it is itself a finding nobody reads.** `momentum-harness/CLAUDE.md`
carries a complete, well-reasoned convention — an observation states *what was seen*, *what
produced it*, *what would settle it*, and leaves the folder by exactly three routes: promoted
to a pre-registered hypothesis, promoted to a spec, or dropped with the reason recorded. **It
sits beneath a banner declaring that everything below it is not current guidance.** That is
the project's most-named failure applied to the machinery for handling the project's failures.

### 5a — carry the convention forward

**Read `momentum-harness/CLAUDE.md`'s observations section and re-state it in the active
tree's `CLAUDE.md`.** This is a read from the archive, not an adoption — the archive is a
source and must not be modified. If the v1.2 bump from Part 4 has already landed, this is
v1.3; **do not batch two changes under one version.**

### 5b — `docs/observations/OBSERVATIONS.md`

One ledger, one row per finding: **id · date · what was seen · what produced it · what would
settle it · status · review-by date.**

`status` is one of **`OPEN` · `PROMOTED` · `DROPPED`**, and `PROMOTED` and `DROPPED` both
require a `resolution:` naming where it went or why it did not.

**Seed it with the findings named on 2026-08-12 and nowhere else.** Carry each with its
producing source; **do not re-derive, re-measure or improve any of them**, and mark clearly
which are observations and which are readings:

| what was seen | source |
|---|---|
| 88.9 % of prints in the capture are odd lots, mean 47.5 shares | `012` done-note |
| `FINRA` is 57.88 % of prints and 42.57 % of shares | `012` done-note |
| `CHX` is 0.11 % of prints but 3.82 % of shares — 1,606 shares/print, 34× the mean | `012` done-note |
| The capture is 5.32× larger than TradingView's same-window volume. **Cause unestablished**; Cboe One + odd-lot filtering is the most probable explanation and is a reading | `012` done-note |
| `manage` has no slice anywhere in `BUILD-PLAN.md` | `S009a` session output |
| `SPEC.md` §4d's ASCII trigger names `SSH_CONNECTION`; the real property is whether the output encoding can carry the box characters | `S009` done-note |
| The adoption gate has no route for natively-authored new code; `BOOTSTRAP_ALLOWLIST` is doing two jobs and grows ~11 entries per slice | `S009` done-note |
| `H9-v3-specs-into-new-tree.md` was never carried into this tree; H9 was built from v2 | `013a` done-note |
| `condition_codes.yaml` needs rewriting, not deleting — its banner asserts ITCH provenance it does not have | `013c` done-note |
| The separation guard misclassifies `OMCL 2024-08-01` and `ITCI 2025-01-10`; latent until the identification window widens past 15 s | `013c` done-note |
| `git ls-files` reads the index and reports staged files as present; `git cat-file -e HEAD:<path>` is the check that answers "committed" | `013b` done-note |
| At 209 columns each top-row tile gets ~67, below the `BOX_WIDTH` of 71 the snapshots are taken at | design session, 2026-08-12 — **a reading, unverified** |

**Every row cites where it came from. A finding with no source does not go in.**

### 5c — the trigger

**A ledger without a trigger is a folder nobody opens, which is the thing being fixed.**

Build a test on the shape of `test_open_questions.py`: **it goes RED while any row is `OPEN`
past its `review-by` date.** Not red for being open — red for being *ignored*.

- Missing or malformed `review-by` is red. **Unknown is never read as answered.**
- **Deleting a row must not clear it.** An earlier version of `test_open_questions.py` keyed
  on a folder being non-empty, which made deletion the cheapest route to green on a mechanism
  whose purpose was holding things open. `PROMOTED` or `DROPPED` with a `resolution:` is the
  only exit.
- **Seed every row with a `review-by` far enough out that this task does not ship red.**
  Propose the interval and say why.

### 5d — where rows come from

**Rows are added at done-note review**, which is the one moment someone is already reading.
State that in `CLAUDE.md` alongside the convention: **a done-note that names a finding with no
ledger row has not finished reporting it.**

---

## Part 6 — retention, recorded

**`records/tape/` is kept indefinitely until Christoph says otherwise.** Decided 2026-08-12.

**Write it into `CLAUDE.md`** with its reason: the 2026-08-11 QQQ session is unrepeatable and
is Row 14's basis. **Never delete a session that any fitted threshold cites as its source** —
a threshold whose basis file is gone has no source string, which the threshold convention
forbids.

**No retention policy for future captures is decided.** Say so explicitly rather than leaving
the absence to be read as "keep everything forever by rule".

---

## Part 7 — the `christoph/` header cleanup

`012-uat-first-five-minutes.md` was authored with `**State** OPEN`. **Two defects: the key
name and the value.**

`HANDOFF-PROTOCOL.md` v1.1 rules both — the key is `**Status**` everywhere, and the five
states are the whole vocabulary. `OPEN` is not one.

**Fix the headers across `christoph/open/` and `christoph/done/`.** Where a file's correct
state is not knowable from the repo, **write nothing and list it in the done-note for
Christoph to answer.** A fabricated state is exactly what the header test exists to catch.

**Do not write a regex that tolerates variants.** A pattern permitting drift is not a guard.

---

## Part 8 — commit

**Everything from `015` and `S009a` is uncommitted**, and HEAD is at `cfa491d`. `verify.ps1`
prints `git status --short`; against a permanently dirty tree that section says nothing.

Commit in **separate, subject-coherent commits**, following `014`'s reasoning: split further
if the shape suggests it, and name anything that fits no group rather than forcing it.

**Nothing is pushed.** The GitHub repo named `momentum` maps to the **archived** local tree
and that decision is still open.

---

## Do not

- **Do not run this concurrently with `S009a`.**
- Do not modify any file recorded in `EVIDENCE-CARRY.md`, or re-record any hash.
- Do not touch `records/`, any tape file, or anything belonging to `012`.
- **Do not reword any done-note's UAT exit row**, including the five `015` left red. Editing a
  note already copied to `handoff/accepted/` breaks byte-identity with its acceptance copy,
  which `013d` verified by hash. **That is Christoph's decision and it is not in this task.**
- Do not open a TWS connection.
- Do not modify `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` or `HANDOFF-PROTOCOL.md`.
- Do not weaken any test to make it pass. If a test and a convention genuinely collide,
  **report it and stop** — that is what produced Resolution D.
- Do not act on any row seeded into the ledger. Recording is not acting.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full suite. **Report the count you observed, and the count before this task, as measured numbers.** Both current failures clear. Name any new failure explicitly. |
| **Refusal A** | Claude Code | Add a ledger row with `status: OPEN` and a `review-by` in the past. Confirm the suite goes red and the message names the row. Revert. |
| **Refusal B** | Claude Code | Delete that row rather than resolving it. **Confirm the suite is still red** — deletion must not be a route to green. Revert. |
| **Refusal C** | Claude Code | Point the Part 3 exemption at a genuinely live legacy path. Confirm it still fails. Revert. |
| **UAT** | Christoph | Run `.\verify.ps1` and read the output cold. **The criterion is whether you can tell, without asking anyone, whether the four facts match what a done-note claimed.** If you cannot, the script has failed its only purpose. **Write the record to `christoph/open/`.** |

## Done-note must state

- **`verify.ps1`'s full first-run output, verbatim.**
- The `test_no_secrets` runtime before and after, as measured numbers.
- **Which discriminator Part 3 used and why**, including the guard — or why derivation failed
  and the list was widened instead.
- Every `christoph/` header changed, and **every file whose state was not knowable**, listed
  for Christoph.
- The ledger's seeded rows, the `review-by` interval chosen, and the reasoning for it.
- The commit split, with a one-line subject for each.
- **Anything in this task that was wrong on contact.** Every task this week has had
  divergences and every one of them mattered.
