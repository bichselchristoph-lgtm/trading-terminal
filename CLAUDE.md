# CLAUDE.md — momentum

Guidance for Claude Code working in `D:\Dev\momentum`.

## What this is

The active tree, born 2026-08-10 at commit one. It is **deliberately near-empty.**

`D:\Dev\momentum-harness` is the predecessor and is now archived reference. It holds a
mixture of authored work and folders imported wholesale from `tradesignals`, and that
mixture is why this tree exists: an import carried across a `README.md` describing another
repo, a condition-code vocabulary invented by an unidentified codebase, and a spec directory
where nothing declared whether it was current.

**A near-empty tree is the expected state, not a problem to solve by adopting more.**
Files arrive one at a time, each with a reason and a test.

## Nothing enters this tree by copying

Two routes in, and only two.

### 1. The adoption gate — for anything that does work

A candidate is copied into the drop folder `D:\Dev\_adopt\` (unversioned, outside both
repos) with a provenance companion, and enters this tree **only after passing every check**.
A failed adoption leaves no trace here.

```powershell
C:\venvs\trading\Scripts\python.exe tools\adopt.py --check <name>    # dry run
C:\venvs\trading\Scripts\python.exe tools\adopt.py --adopt <name> --into <dest> --by <who>
```

Four refusals, none of which has a default or an inferred value:

| # | Refusal |
|---|---|
| 1 | **No provenance companion.** `<name>.provenance.md` naming source path, origin, reason for adoption, and what depends on it. |
| 2 | **No behavioural test.** Nothing enters a code tree — core, live, harness or tools — without a test that fails if the file's behaviour changes. **Import-smoke does not count** — `regime_pull.py` passed import coverage while raising `NameError` on its first call. |
| 3 | **Same name, different content.** Never silently overwrite, never auto-rename. |
| 4 | **Origin `imported` or `unknown` without an explicit decision.** An `authored` file can be adopted on its merits. A predecessor's artifact needs a person to say why this project is adopting it. |

Every adoption appends a row to `ADOPTION-LOG.md`.

### 2. The evidence carry — for records of what happened

Evidence is **not** adopted and does not pass through the gate, because the gate's question
— *is this worth keeping* — does not apply to a record of what happened. It is carried
byte-identical, verified by hash, and logged in `EVIDENCE-CARRY.md`.

**Never clean, dedupe, reformat, prune or regenerate evidence.** If a file looks wrong, say
so and carry it anyway. A regenerated ledger is a well-formed value answering a different
question, and it will later be read as a record of what happened.

### The test that makes it stick

`tests/test_adoption_log_complete.py` asserts that **every tracked file outside the
bootstrap allowlist appears in `ADOPTION-LOG.md` or `EVIDENCE-CARRY.md`.** A file that
arrives by any other route goes red. Without it the gate is prose, and a convention that
lives in prose depends on someone remembering.

## Running things

**There is no `python` on PATH.** Use `C:\venvs\trading\Scripts\python.exe` (3.12.7) or
`py -3.12`.

```powershell
C:\venvs\trading\Scripts\python.exe -m pytest
```

`pytest.ini` lists **every** test directory, not just `tests/`. The old repo set
`testpaths = tests` and seven behavioural tests in `momentum-harness/live/tests/` were never
collected. `tests/test_pytest_collection.py` keeps that list honest.

**IBKR access is `ib_async`, always. Never `ib_insync`.**

## docs/specs/ — the location of record

`SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` and `DRIVE-ARCHIVE-LIST.md` belong in
`docs/specs/`. **Drive is archive, not the record.** A spec that lives only in Drive is
invisible to the side that builds — Layer 0 was fully specified and never built for exactly
that reason.

**A spec quoted into a task file is a copy, and the copy is authoritative for that slice
only. The tree is authoritative for everything else.** Drive is archive: the sync was removed
2026-08-09, so nothing on disk points at it and its copies cannot drift back in.

**All four are now in the tree**, adopted 2026-08-10 under H9. `tests/test_spec_pointers.py`
asserts the three canonical ones are present and non-empty, and pins `REGIME-PROMPT.md` at
v1.1 so a later re-supply cannot silently downgrade it to v1.0.

If any of these ever needs replacing, it comes from Christoph. **Do not reconstruct,
paraphrase or regenerate one** — from memory, or from quotations in handoff files. A
plausible reconstruction of a spec is worse than an absent one, because it will be read as
the record.

`docs/specs/` also holds `REPO_CONSOLIDATION_PLAN.md` (the definition of "step 7"),
`USE_GUIDE.md`, `layer0-amendment-2-frozen-vs-live.md`, and `docs/specs/mockups/` — the five
screen mockups and their index.

## Handoff convention

**Chat and this session cannot see the same things.** Chat does design and review; Claude
Code builds. Chat has **no direct access to this repo and no file sync of any kind** — the
Drive sync was removed 2026-08-09, so nothing on disk reaches chat automatically. It cannot
read the code, the test output, or anything said in a session transcript.

**Christoph is the only channel between the two halves.** That makes writing things down more
important, not less: a file is what he can carry. A finding that exists only in session output
cannot be carried at all.

The consequence is the whole convention: **anything chat needs must be written to a file.**
A finding explained in session output and nowhere else did not happen, because the half of
the loop that acts on it will never see it. Write these without being asked.

| Path | What goes there |
|---|---|
| `handoff/inbox/NNN-*.md` | Build tasks. Written by chat, addressed to this session. |
| `handoff/done/NNN-*.md` | One per completed task: what changed, what the tests said, what you found. |
| `handoff/questions/*.md` | Anything needing a **decision rather than a choice**. Frontmatter carries `status: OPEN`. |
| `docs/observations/*.md` | Durable findings about the system, outliving the task that found them. |
| `handoff/*.md` (root) | A **standing instruction that is always live**. Not a task; never moves to `handoff/done/`. |

`handoff/` is **tracked**. In the old repo these files were untracked, so they existed on one
machine and in nobody's history — no sync, no git, no second copy anywhere.

`handoff/done/NNN-*.md` must be **readable cold** by someone with no session context: name
the files, quote the numbers, say what surprised you. "Done as specified" is not a handoff.
The test result belongs in it verbatim — a claim that the suite passed is worth less than the
count that passed and the count that did not.

A **question** is not a task you would rather not do. It is a fork where the answer changes
what gets built and the choice is not yours to make. If you can pick a defensible option and
say why, that is a choice — make it, record it, move on.

## Spend

Databento is billed per byte. Any sanctioned client must refuse a billable call without a
shown, approved estimate, and a $100/day ceiling in `~/.claude/spend_limits.yaml` overrides
every approval.

**No Databento key is reachable from any Claude-accessible config, deliberately.** The
consequence, stated plainly rather than discovered later: Claude Code cannot run Databento
pulls, and a reserve-then-close ledger cannot be exercised end to end. Any adopted module
touching Databento therefore arrives **untested against a live credential**, and its
provenance companion must say so.
