# REPO CONSOLIDATION PLAN — D:\dev (six repos to one)

> **STATUS** HISTORICAL · **date** 2026-08-10
> The plan was executed. Step 7 folded in `trading-scripts` and `orb_tools` at commit
> `1e6c893`, and `20f1d6d` deleted the staged pair. It records what was done and is
> never instruction — the tree it describes is now archived reference.

> **STATUS BLOCK — added on ingestion 2026-08-07, not part of the original plan.**
>
> **Phase 0 is already satisfied and its premise was wrong.** `momentum-harness`
> has had a `.git` directory since 2026-08-05 with a full commit history — 50
> commits at the time of reading — and a configured remote. `git init` is a
> no-op here and must not be run.
>
> The tamper-evidence concern Phase 0 raises is therefore in **better** shape
> than the plan assumes, not worse. `config/preregistration.yaml` has a
> complete per-version commit history with timestamps, and as of 2026-08-07 all
> of it is **pushed to GitHub**, so the ordering carries a third-party
> timestamp rather than only a local one. The relevant ordering is provable:
>
> ```
> c996ac6  2026-08-06 15:15  v19 registered (paired-quantity rule + tolerance band)
> 51daed8  2026-08-06 18:52  that rule's validation RUN — 3h37m later
> ```
>
> The plan's other Phase-0 statement — "the section-6 calibration has already
> run" — is also worth qualifying. §6 ran on the **phase-1 QQQ** population and
> returned a null. No phase-3 calibration has run; the tick pull is halted at
> the user's instruction with nothing spent on it.
>
> Also corrected on ingestion: **six repos, not one, were checked.** Four of the
> five non-harness repos (`ibkr_tape_tools`, `orb_tools`, `trading-scripts`,
> `tws_order`) were already fully pushed. Only the harness (22 commits) and
> `tradesignals` (1) were behind, and both are now pushed.
>
>
> **COMPLETION, 2026-08-07.** Steps 1-9 are done. Step 1 was a no-op (the repo
> already existed). Steps 4-8 landed `core/harness/live` with the boundary test,
> and folded in `tradesignals`, `trading-scripts`, `orb_tools` and
> `ibkr_tape_tools`. Step 9 leaves `tws_order` separate, recorded as a gate with
> preconditions in `harness/config/preregistration.yaml`.
>
> Overlaps: 1 resolved before the move (volume_curve collapsed into an injected
> config plus `core/indicators/rvol.py`). 2 dissolved -- `setup_grader` and the
> orb_validator tests were never a pair. 3 settled by version header, README and
> `rolling_flow`'s stated target, NOT by mtime, which pointed the other way. 4
> dissolved -- Layer 1 was never built. 5 settled -- tape detectors and a
> bar-pattern monitor are different subjects. 6 is a POLICY decision left open in
> `docs/observations/`.
>
> Deliberately NOT done: step 2 (pin a .venv, consolidate requirements) -- the
> existing venv satisfies every project and creating a new one mid-consolidation
> risks a failure ambiguous between structure and interpreter, which is the exact
> thing that step existed to prevent. The loose-end deletions
> (`winget.msixbundle`, `tree.txt`, `notes/` to Drive) are the user's files and
> are flagged rather than removed.
>
> Everything below is the plan as written, verbatim.

---

Purpose: collapse six overlapping repos into one so the indicator registry can
actually be a single definition (Amdt 5a). Ordered so nothing is moved before
it is recoverable.

## PHASE 0 — STOP. Do this before touching anything.

momentum-harness has NO .git directory. Verify:

```
cd D:\dev\momentum-harness
git status
```

If it says "not a git repository":

```
git init
git add -A          # set .gitignore first, see data policy below
git commit -m "chore: import existing harness state (retroactive initial commit)"
```

Two reasons this is Phase 0 and not a cleanup item:

1. It is the restore point. Every move below is safe only because you can get
   back.
2. PRE-REGISTRATION TAMPER-EVIDENCE. config/preregistration.yaml is at v19 and
   the section-6 calibration has already run. With no commit history there is
   nothing establishing that the predictions were written BEFORE the results
   were seen. Tenet 4 only works if that ordering is provable. A retroactive
   initial commit does not recover the lost history, but it stops the bleeding
   from today forward — and everything AFTER the phase-3 tick pull will be
   properly ordered, which is the part that still matters.

Note in the commit message that history before this point was untracked. Being
honest about the gap beats a clean-looking log that implies provenance it
doesn't have.

## TARGET STRUCTURE

```
momentum/                   # umbrella repo — NOT named "tradesignals" (see naming note)
  core/                     # shared; depended on by both sides, depends on neither
    indicators/             # THE registry — pure OHLCV functions, timeframe-agnostic
    types.py
    session.py
    us_equity_calendar.py
    config/                 # instruments, condition_codes, venue_capabilities
  harness/                  # research: calibration, holdout, eras, pre-registration
    config/                 # preregistration.yaml, holdout*.yaml, eras.yaml, spend_*
  live/                     # operational: feeds, levels, detectors, engine, render
  orders/                   # staged-order safeguard, sizing, stops (later — see tws_order)
  tools/
  tests/
  handoff/                  # inbox / done / questions
  watchlists/               # CSVs + provenance screenshots (COMMITTED, per ingestion spec)
```

DEPENDENCY RULE, enforced by a test: harness -> core. live -> core. NEVER
harness -> live or live -> harness. Add tests/test_import_boundaries.py that
walks the import graph and fails loudly on a violation. Without that test this
is a convention, and conventions decay.

NAMING: do not call the umbrella tradesignals. "Signal" is reserved for the
composition kind (Amdt 7); naming the whole system after it re-muddles
vocabulary you deliberately cleaned up. momentum is neutral and already matches
momentum-harness.

## MOVE LIST

### momentum-harness -> becomes the SPINE of the new repo

Most code, most tests, all phase-3 state. Make it the base and move others INTO
it.

| From | To | Note |
|---|---|---|
| signals/magnitude.py, structural.py | core/indicators/ | These are INDICATORS not signals (Amdt 7). Rename the package on the way. |
| signals/types.py | core/types.py | |
| data/session.py, us_equity_calendar.py | core/ | shared by both sides |
| data/bars.py, identify.py, validate.py | core/ | shared ingest primitives |
| data/selection.py, spend.py | harness/ | research-only |
| harness/*.py (eras, holdout, provenance, record, sample, dependence, venues) | harness/ | unchanged |
| config/instruments.yaml, condition_codes.yaml, venue_capabilities.yaml | core/config/ | shared |
| config/preregistration.yaml, holdout*.yaml, eras.yaml, spend_*.yaml | harness/config/ | research-only |
| tools/* | tools/ | unchanged |
| cache/, records/, records_truncated/, selection/ | stay in place, gitignored | see data policy |

### tradesignals -> live/

| From | To | Note |
|---|---|---|
| tradesignals/feeds.py, engine.py, render.py, cli.py, cache.py | live/ | |
| tradesignals/detectors.py | live/ | RESOLVE overlap with orb_tools/flag_monitor.py first |
| tradesignals/levels.py, levels/*.json | live/levels/ | this is the structured-signal LEVELS RAIL (Amdt 9) |
| tradesignals/core.py, config.py | merge into core/ | inspect for real overlap; do not blind-copy |
| tools/build_levels_ibkr.py, make_replay_slice.py | tools/ | |
| Trade Signals Spec v2.docx | Drive, not the repo | see loose ends |
| docs/sample_console_output.txt | docs/ | |

### trading-scripts -> split

| From | To | Note |
|---|---|---|
| regime_pull.py | live/regime/ | RESOLVE against harness Layer-1 work first |
| setup_grader.py | harness/ | must be REUNITED with its tests — overlap 2 |
| adr_move.py, adr_used.py | core/indicators/ | ADR is a pure OHLCV measurement = an indicator |
| ep_premarket.py | live/ | |

### orb_tools -> split

| From | To | Note |
|---|---|---|
| volume_curve.py | core/indicators/ | RESOLVE against task 001 FIRST — overlap 1 |
| flag_monitor.py | live/ | RESOLVE against tradesignals/detectors.py |
| watchlist_builder.py | tools/ | check against ingestion spec — system must NOT re-scan |

### ibkr_tape_tools -> split

| From | To | Note |
|---|---|---|
| tape_reader*.py (three versions) | live/tape/ | PICK ONE — overlap 3 |
| rolling_flow.py | live/tape/ | |
| tape_backtest.py | harness/ | it's research, not live |
| tests/test_rvol_scaling.py, test_grader_invariants.py, test_score_granularity.py | tests/ | these test the GRADER, which lives in another repo — overlap 2 |
| tests/reference.py, run_mutations.py | tests/ | |
| test_conn.py | tools/ | connection smoke check, not a unit test |

### tws_order -> KEEP SEPARATE for now

Do NOT merge in the first pass. It is the only code that can touch live orders.
Keeping the blast radius small is worth some duplication, and the no-transmit
walls are easier to audit in a repo whose entire contents are order-related.

Merge later as orders/ once the umbrella is stable AND the import-boundary test
exists. When you do: sizing.py / stops.py / ibkr.py / state.py -> orders/, tests
come with them.

## OVERLAPS TO RESOLVE BEFORE MERGING

Each must be settled by reading both files, not by picking the newer one.

1. **orb_tools/volume_curve.py vs task 001 RVOL.** BLOCKS TASK 001. A "volume
   curve" is very likely the same intraday-volume-vs-typical measurement,
   possibly with different window or baseline semantics. Read it before
   building 001. If it already does this, 001 becomes "lift and conform to the
   registry contract", not "write from scratch".

2. **setup_grader.py (trading-scripts) vs its tests (ibkr_tape_tools/tests).**
   Code and test_grader_invariants.py / test_score_granularity.py /
   test_rvol_scaling.py are in DIFFERENT repos. Whatever those tests currently
   import, it is not that grader. Reunite and run them — expect breakage and
   treat it as information. test_rvol_scaling.py may already encode RVOL
   assumptions relevant to 001.

3. **tape_reader.py vs tape_reader_v1.py vs tape_reader_v2.py.** Three files
   versioned by filename inside a git repo. Find which is live (check imports),
   keep it, delete the rest — git holds the history now.

4. **trading-scripts/regime_pull.py vs harness Layer 1.** Layer 1 (daily index
   regime, IWM/SPY/QQQ/RSP) was specified as harness work but the script lives
   elsewhere. Confirm there is one implementation, not two.

5. **orb_tools/flag_monitor.py vs tradesignals/detectors.py.** Both plausibly
   detect intraday flags. One playbook, one detector.

6. **orb_tools/watchlist_builder.py vs the ingestion spec.** The spec says the
   system does NOT re-scan; it ingests your Deepvue CSV export. If
   watchlist_builder.py builds a watchlist by scanning, it contradicts a
   decision you made deliberately (Tenet 11, source drift). Retire it or
   re-scope it to CSV ingestion.

## DATA / GITIGNORE POLICY

The "commit everything, nothing gitignored" rule was scoped to WATCHLISTS —
small files where provenance is the whole point. It should not generalise to
derived data.

GITIGNORE (regenerable, large): cache/, records/, records_truncated/,
selection/**/*.parquet, **/__pycache__/, .pytest_cache/, *.pyc, .venv/

COMMIT (small, and IS the provenance): cache/1min/manifest.jsonl,
spend_ledger.jsonl, membership_evidence.json, everything in config/,
watchlists/ (CSVs + screenshots), selection/**/*.log, monthly_yield.csv

The manifests are the provenance record; the parquet is the payload. If the
manifest is committed and the parquet is reproducible from it, nothing is lost
and you gain a repo you can actually clone.

## ENVIRONMENT

tradesignals/__pycache__ contains cpython-310, -312 AND -314 artifacts; the
harness is cleanly 312. Three interpreters have run that code. No .venv
anywhere, so this is likely global installs.

Pin one interpreter (312, matching the harness and its 704 passing tests),
create a .venv, consolidate the three requirements.txt files into one. Do this
BEFORE the merge, or the first cross-repo import failure will be ambiguous
between "wrong structure" and "wrong interpreter".

## CLAUDE CODE ROOT

CLAUDE.md and .claude/settings.local.json sit at D:\dev root — the PARENT of
six repos. That is why "commit this" is ambiguous and why push_all.ps1 exists.
After the merge, move CLAUDE.md into the umbrella repo and delete push_all.ps1;
one repo needs no fan-out script.

## LOOSE ENDS

- D:\dev\winget.msixbundle — installer, unrelated. Delete.
- D:\dev\replay\AMZN-2026-08-03-open.json — output of
  tradesignals/tools/make_replay_slice.py living outside any repo. Move to
  live/replay/, gitignore the contents, keep the folder.
- D:\dev\tree.txt — the listing that produced this plan. Delete after.
- notes/ (pptx, xlsx) — reference material, not code. Move to Drive.
- Trade Signals Spec v2.docx — filename-versioned inside a git repo. Specs live
  in Drive; let git version the code.

## ORDER OF OPERATIONS

1. git init + commit momentum-harness. **Nothing else until this is done.**
2. Pin Python 312, create .venv, consolidate requirements. Confirm 704 tests
   still pass.
3. Resolve overlap 2 (reunite grader + tests) and overlap 1 (volume_curve.py) —
   both feed directly into task 001.
4. Create the umbrella repo from the harness; add core/, harness/, live/.
5. Add tests/test_import_boundaries.py BEFORE moving live/ in, so the boundary
   is enforced from the first commit that could violate it.
6. Move tradesignals -> live/. Run tests.
7. Fold in trading-scripts and orb_tools, resolving overlaps 3-6 as you go.
8. Fold in ibkr_tape_tools.
9. Leave tws_order separate. Revisit once the umbrella is stable.

## CORRECTION TO TASK 001

The earlier Claude Code prompt pointed at D:\dev\tradesignals. WRONG REPO. The
indicator registry is momentum-harness/signals/ with tests/test_registry.py.
Task 001 belongs next to magnitude.py and structural.py.

Do not run the old prompt. Either wait for the merge and target
core/indicators/, or build it now in momentum-harness/signals/ — but only AFTER
reading volume_curve.py and test_rvol_scaling.py (overlaps 1 and 2), which may
already contain the answer.
