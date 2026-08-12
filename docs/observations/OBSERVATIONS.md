# OBSERVATIONS — the ledger

> **Seeded 2026-08-12 under `016` §5b.** One row per finding. `tests/test_observations_ledger.py`
> goes **RED while any row is `OPEN` past its `review-by` date** — red for being *ignored*,
> not for being open.

**Every row cites where it came from. A finding with no source does not go in.**

**`kind` separates an OBSERVATION from a READING.** An observation is something measured. A
reading is an inference about what produced it. Conflating the two is how a plausible
explanation becomes a recorded fact — `012` came within one sentence of recording Cboe One
odd-lot filtering as the established cause of a 5.32× discrepancy, and it is not established.

**Status is `OPEN` · `PROMOTED` · `DROPPED`.** `PROMOTED` and `DROPPED` both require a
`resolution:` line in the Resolutions section naming where it went or why it did not.
**Deleting a row does not clear it** — see the test.

**Nothing here has been acted on. Recording is not acting**, and `016` forbids acting on any
seeded row.

---

## Why `review-by` is 2026-11-12

**Three months from seeding.** The interval is a property of what these rows are, not a round
number:

- **Almost every row is blocked on a slice that has not been built.** Rows 1–4 are questions
  about tape structure that `S012`/`S016` will answer as a side effect; row 5 needs a
  `BUILD-PLAN` revision; rows 9–10 need `S008`. `BUILD-PLAN.md` §1 sizes a slice at one to two
  Claude Code sessions and core alone is four slices. **A review date that falls before the
  work that would settle these has arrived converts the ledger into a recurring interruption**,
  and a test that cries wolf is a test people learn to make green rather than read.
- **It must be shorter than the memory of why the row exists.** Three months is inside the
  span of this project's own git history, so a reviewer can still reconstruct the context.
- **It is a floor, not a schedule.** Any row can be resolved the day its slice lands; the date
  only says *by when someone must have looked*.

**All twelve share one date deliberately.** Staggering them would be a guess dressed as
precision — nothing here justifies claiming row 7 needs attention sooner than row 8.

---

## The ledger

| id | date | kind | what was seen | what produced it | what would settle it | status | review-by |
|---|---|---|---|---|---|---|---|
| **OBS-001** | 2026-08-11 | OBSERVATION | **88.9 % of all prints in the capture are odd lots**, mean 47.5 shares/print. Any per-print statistic on this tape is dominated by odd lots | `handoff/done/012-live-qqq-tape-capture.md` | An independent source for QQQ odd-lot share on 2026-08-11. Nothing in the capture cross-checks it — `012` says so explicitly | OPEN | 2026-11-12 |
| **OBS-002** | 2026-08-11 | OBSERVATION | **`FINRA` is 57.88 % of prints and 42.57 % of shares.** Off-exchange prints are IN `whatToShow="TRADES"`, and are the largest single component | `handoff/done/012-live-qqq-tape-capture.md` — discharges `008a` Test 5 | Already answered decisively for tick-by-tick. Open only for whether IBKR's *historical* endpoint filters differently, which its documentation implies and nothing here tests | OPEN | 2026-11-12 |
| **OBS-003** | 2026-08-11 | OBSERVATION | **`CHX` is 0.11 % of prints but 3.82 % of shares** — 1,606 shares/print, **34× the overall mean.** One venue carries block-sized prints and almost nothing else | `handoff/done/012-live-qqq-tape-capture.md` | Whether it holds across sessions and symbols. One session on one symbol cannot distinguish a venue's character from a day's accident | OPEN | 2026-11-12 |
| **OBS-004** | 2026-08-11 | OBSERVATION | **The capture is 5.32× larger than TradingView's same-window volume** — 873,482 shares against 164,280 | `handoff/done/012-live-qqq-tape-capture.md` | TradingView's venue list for that session. The magnitude is measured; the cause is not | OPEN | 2026-11-12 |
| **OBS-005** | 2026-08-11 | **READING** | **Cboe One (four lit venues, ~25 % of tape) plus odd-lot filtering is the most probable cause of OBS-004.** Consistent with direction and roughly with magnitude. **NOT ESTABLISHED** | `handoff/done/012-live-qqq-tape-capture.md`, which states it as a reading | Same as OBS-004. Recorded separately from it **on purpose**: the measurement stands whether or not this explanation does | OPEN | 2026-11-12 |
| **OBS-006** | 2026-08-12 | OBSERVATION | **`manage` has no slice anywhere in `BUILD-PLAN.md` §3–4.** Reconciliation appears inside `S017`'s pre-send checks and `S015`'s execution pull; nothing builds managing an open position | `S009a` session output, from declaring the twelve stages | A `BUILD-PLAN` revision that either assigns the stage or states that it is deliberately out of scope. **It renders `[ NOT BUILT ] (slice not assigned)` on screen today** | OPEN | 2026-11-12 |
| **OBS-007** | 2026-08-11 | OBSERVATION | **`SPEC.md` §4d names `SSH_CONNECTION` as the ASCII-fallback trigger. The real property is whether the output encoding can carry the box characters** — a Windows console on cp1252 dies on `┌` with no SSH involved | `handoff/done/S009-tui-frame-and-refusal-grammar.md` | A `SPEC.md` §4d amendment. The code already implements the wider trigger; the spec still names the narrow one, so the two disagree | OPEN | 2026-11-12 |
| **OBS-008** | 2026-08-11 | OBSERVATION | **The adoption gate has no route for natively-authored new code.** `BOOTSTRAP_ALLOWLIST` is doing two jobs and grows ~11 entries per slice | `handoff/done/S009-tui-frame-and-refusal-grammar.md` | A decision on whether authored-here files get their own route or keep using the allowlist. **The growth rate is the evidence** — at 11/slice the allowlist stops being a list of exceptions | OPEN | 2026-11-12 |
| **OBS-009** | 2026-08-11 | OBSERVATION | **`H9-v3-specs-into-new-tree.md` was never carried into this tree; H9 was built from v2** | `handoff/done/013a-*.md` | Reading v3 against what H9 actually built. Until then it is unknown whether v3 asked for anything v2 did not | OPEN | 2026-11-12 |
| **OBS-010** | 2026-08-11 | OBSERVATION | **`condition_codes.yaml` needs rewriting, not deleting** — its banner asserts ITCH provenance it does not have | `handoff/done/013c-*.md` | Identifying the vocabulary's actual source. **Deleting it would lose the fact that something once claimed ITCH provenance**, which is the finding | OPEN | 2026-11-12 |
| **OBS-011** | 2026-08-11 | OBSERVATION | **The separation guard misclassifies `OMCL 2024-08-01` and `ITCI 2025-01-10`.** Latent until the identification window widens past 15 s | `handoff/done/013c-*.md` | Widening the window in a test and confirming both flip. **Latent is not fixed** — it is a defect with a trigger nobody has pulled yet | OPEN | 2026-11-12 |
| **OBS-012** | 2026-08-11 | OBSERVATION | **`git ls-files` reads the index and reports staged files as present.** `git cat-file -e HEAD:<path>` is the check that answers *"committed"* | `handoff/done/013b-*.md` | Nothing — this is settled fact about git. **It stays OPEN because the tree has not been audited for the wrong check.** `tests/test_no_secrets.py::test_claude_config_is_not_tracked` uses `git ls-files` today | OPEN | 2026-11-12 |
| **OBS-013** | 2026-08-12 | ~~READING~~ → OBSERVATION | **At 209 columns each top-row tile gets ~67, below the `BOX_WIDTH` of 71 the snapshots were taken at** | Design session 2026-08-12, **as a reading**. **Measured and confirmed by `S009a` the same day** | **SETTLED.** See resolution | PROMOTED | 2026-11-12 |

---

## Resolutions

**OBS-013 · PROMOTED.**
`resolution:` Carried into the ledger as an unverified reading, and it had already been
settled by the time the row was written. `S009a` measured Christoph's terminal at
**209 × 54** with `$Host.UI.RawUI.WindowSize` — not derived from pixels — giving **67 columns
per tile against `BOX_WIDTH = 71`.** The reading was correct.

It is promoted rather than dropped because it **became a test**:
`live/tests/test_tui_measured_against_its_tile.py` pins `209 × 54` as the primary snapshot
width with that reasoning recorded beside it, and `test_no_line_ever_exceeds_the_width_it_was_given`
makes the underlying property — nothing renders at a width it was not measured against —
enforced rather than observed.

**Recorded here rather than silently corrected**, because the row's *kind* changed: it entered
as a reading and left as a measurement, and the fact that a design-session inference turned out
to be right is itself worth being able to find later.
