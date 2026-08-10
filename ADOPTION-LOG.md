# ADOPTION-LOG

One row per file adopted into this tree through the gate (`tools/adopt.py`).

`tests/test_adoption_log_complete.py` asserts every tracked file outside the bootstrap
allowlist appears here or in `EVIDENCE-CARRY.md`. A file that arrives by any other route
turns the suite red — that is the mechanism, and it is why this table is not documentation.

Evidence does **not** appear here. It is carried, not adopted, and lives in
`EVIDENCE-CARRY.md`.

| date | path in new tree | source path | origin | reason | test that covers it | adopted by |
|---|---|---|---|---|---|---|
| 2026-08-10 | `docs/specs/mockups/mockup-README.md` | `momentum-harness/docs/specs/mockups/mockup-README.md` | authored | Index for the mockup set; explains what each screen is and is not. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/mockups/mockup-05-live-context.html` | `momentum-harness/docs/specs/mockups/mockup-05-live-context.html` | authored | Live-context mockup including the NOT BUILT state, cited by task 005. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/mockups/mockup-04-size-stage.html` | `momentum-harness/docs/specs/mockups/mockup-04-size-stage.html` | authored | Sizing and staging screen mockup. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/mockups/mockup-03-watchlist.html` | `momentum-harness/docs/specs/mockups/mockup-03-watchlist.html` | authored | Ranked watchlist mockup, the visual contract for task 006. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/mockups/mockup-02-regime.html` | `momentum-harness/docs/specs/mockups/mockup-02-regime.html` | authored | Regime screen mockup, cited directly by task 005 as a source spec. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/mockups/mockup-01-ingest.html` | `momentum-harness/docs/specs/mockups/mockup-01-ingest.html` | authored | Ingest screen mockup; the visual contract for watchlist ingestion. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/layer0-amendment-2-frozen-vs-live.md` | `momentum-harness/docs/specs/layer0-amendment-2-frozen-vs-live.md` | authored | Amendment 2 to the Layer 0 spec, the frozen-vs-live split. Task 003 in handoff/done implements it. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/USE_GUIDE.md` | `momentum-harness/docs/specs/USE_GUIDE.md` | authored | Operating guide for the harness. Adopted with its own caveat recorded: PROVENANCE.md gives it refs=0, so nothing in the old tree referenced it. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/REPO_CONSOLIDATION_PLAN.md` | `momentum-harness/docs/specs/REPO_CONSOLIDATION_PLAN.md` | authored | The plan the consolidation actually followed, and the definition of 'step 7' that M001 §6 and H9a §3b both turn on. Referenced by 3 files in the old tree. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/DRIVE-ARCHIVE-LIST.md` | `supplied by Christoph from Drive, 2026-08-10 (Drive sync removed 2026-08-09)` | authored | The record of what remains in Drive and what could not be archived. With Drive sync removed on 2026-08-09 this is the only on-disk index of those documents. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/REGIME-PROMPT.md` | `supplied by Christoph from Drive, 2026-08-10 (Drive sync removed 2026-08-09)` | authored | v1.1, the prompt behind the scheduled Layer 1 task. Verified to carry 'PART E -- the three outputs' and the E0 subsection, so it is v1.1 and not the v1.0 H9 says to reject. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/BUILD-PLAN.md` | `supplied by Christoph from Drive, 2026-08-10 (Drive sync removed 2026-08-09)` | authored | Companion to SPEC.md and the source of the slice numbering. M001 could not report the slice-008 collision properly because this document was unreadable from the repo. | `n/a (not a code tree)` | Christoph |
| 2026-08-10 | `docs/specs/SPEC.md` | `supplied by Christoph from Drive, 2026-08-10 (Drive sync removed 2026-08-09)` | authored | The location of record for the system specification. A spec that lives only in Drive is invisible to the side that builds -- Layer 0 was fully specified and never built for exactly that reason. H9 exists to end that. | `n/a (not a code tree)` | Christoph |

## The first thirteen rows — H9, 2026-08-10

All thirteen are documentation, all `authored`, all adopted into `docs/specs/`. They split
into two populations that are cited differently, and the difference is the point:

- **Four canonical specs** — `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md`,
  `DRIVE-ARCHIVE-LIST.md` — have **no `PROVENANCE.md` row**, because they have never existed
  in `momentum-harness`. H9a inventoried that repository; these came from Drive, supplied
  directly. "No row, and here is why" is the honest citation; inventing one would be worse
  than the absence.
- **Nine carried forward** — three specs and six mockups — have rows in `PROVENANCE.md`, all
  `authored`, and every one is **byte-identical** to the old repo's copy.

Before this, the table was empty for a reason worth keeping on the record: H9a had not run,
refusal 4 keys on the origin classification it produces, and adopting anything would have
meant inventing the value the refusal exists to demand. H9a ran first. That is the order the
gate is built to enforce.
