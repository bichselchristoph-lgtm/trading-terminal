# CLAUDE.md — momentum

> **version** v1.7 · **date** 2026-08-15 · **supersedes** v1.6 (2026-08-13)

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

## The remote, and the push habit

**Push at the end of every session. A commit is local; only a push survives the disk.**

**The active tree's remote is `origin` →
`https://github.com/bichselchristoph-lgtm/trading-terminal.git`.** It was created empty and
private on 2026-08-13 under 017, and until that day **nothing in this tree had ever been
pushed** — the adoption gate, the protocol, the TUI, every done-note, all on one disk since
2026-08-10.

**`momentum` on GitHub is the ARCHIVED tree** — it maps to `D:\Dev\momentum-harness`, renamed
there before this tree existed. **It is never pushed to.** That naming collision is the whole
reason a new repository was created rather than the old name reused. **Do not touch, rename,
remove or re-point any remote on `momentum-harness`.**

> **The repository is named `trading-terminal`, not `momentum-terminal`.** 017 proposed the
> latter and Christoph created the former. **The name in this file is the one that exists**;
> if you find `momentum-terminal` written anywhere, it is a proposal that was not taken up.

**This supersedes the position in `D:\Dev\CLAUDE.md` v1.1**, which says the remote is unsettled
and the active repo must not be pushed. That was true when written and is false from
2026-08-13. **If both statements are still readable, this one is current** — and the parent file
needs the same correction, because a document that says two things is worse than one that says
the wrong thing.

**Never force-push, and never push to the archive.**

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

### Pulling Drive into the tree — `sync.ps1`

**One word, from anywhere:**

```powershell
D:\Dev\momentum\sync.ps1
```

**That is the whole command.** No arguments, no working directory, no activated
environment — the script names the venv interpreter in full and derives the repository from its
own location. `sync.ps1 -Pair christoph_open` does one pair; `-DryRun` copies nothing.

**Why this is written down.** Until 2026-08-15 the inbound copier had no trigger of its own: it
ran when a task ran, because a task running was what made someone invoke it. **`handoff/inbox/`
files arrive by the same run that consumes them, so the gap was invisible — but a UAT arrives
*between* tasks, and between tasks nothing runs.** Four UAT files sat in Drive while
`christoph/open/` held one `.gitkeep`. **Christoph was the one party who could have unblocked it
and no document stated the command.**

**A non-zero exit means a person must look** — a refused file, a differing file, an unreachable
source or destination. Nothing is ever overwritten.

**It also runs every 15 minutes as a Windows Scheduled Task**, inbound only. Register it once,
from an elevated PowerShell: `tools/register-sync-task.ps1`. **The export is never scheduled** —
it runs as a task's last action, after the commit, and a scheduled export would race a session
mid-commit.

### NOW.md — what is runnable, and on whom

**`tools/now.py` writes it into `claude/`, from the tree, on every `verify.ps1` run.**

**Its path is deliberately not backticked here.** The file is gitignored and does not exist
until the generator has run once, so a backticked pointer to it is red on a fresh clone —
measured, on the run that introduced this section. **The generator is the durable thing; the
artefact is a rendering of the tree that happens to be on disk.**

**Derived, never stored.** It is derived, never
stored: `ready`, `blocked` with the unmet dependency named, `superseded`, `on christoph`, `done`,
and rule 16's admin:product ratio. **A hand edit does not survive a run**, and
`tests/test_now_is_derived.py` asserts it.

## Who may decide — the product/admin line, applied a second time

**Rule 16 already draws this line to count the admin tax. From 2026-08-15 it also governs who may
decide.**

> **Product** — changes what the terminal renders, computes, or does for Christoph.
> **Admin** — everything else. Pipelines, protocols, tests, git, workflow, ledgers, syncs.

| | Gated on Christoph |
|---|---|
| **Product** — what a panel shows, what a number means, a spec change, a threshold, a UAT, an architectural choice | **Yes. Always.** |
| **Admin** — a failing test, a git conflict, a broken guard, a sync defect, a worktree, a duplicate ledger id | **No. Proceed.** |

**Claude Code may author its own task file — for admin only — and act on it in the same session.**
Until now only the design session could author task files, which is why a broken test guard waited
for a file to be written and a prompt relayed. **The file is still written; it exists for the
record and the review, not for permission.**

**Four guardrails, all already in force:**

1. **`class: admin` only.** A self-authored file carrying `spec` or `product` is defective.
   **Anything touching what Christoph sees, or what a number means, is a question file** and the
   gate stands.
2. **Rule 16 still binds.** It must name the product task it unblocks, and **admin unblocking
   admin remains forbidden.** That is what stops this becoming a machine for generating work.
3. **The tax is still counted.** Self-authored tasks appear in `NOW.md`'s ratio like any other.
   **Autonomy buys no exemption from the count.**
4. **Review moves after, not before.** The design session reads the done-note and may reject.

**Numbering: read the inbox, never infer.** The next free number, by the same rule as any other
file, and **a collision is a stop** — three duplicate ledger ids and two files numbered `035`
already say why.

**The risk, stated so it is watched:** rule 16 exists to *discourage* admin, and this makes admin
cheaper to produce. **If six self-authored admin tasks land in a day, that is the same failure
with a new author**, and `NOW.md`'s ratio is where it will show.

## docs/specs/ — the location of record

`SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` and `DRIVE-ARCHIVE-LIST.md` belong in
`docs/specs/`. **Drive is archive, not the record.** A spec that lives only in Drive is
invisible to the side that builds — Layer 0 was fully specified and never built for exactly
that reason.

**A spec quoted into a task file is a copy, and the copy is authoritative for that slice
only. The tree is authoritative for everything else.** Drive is archive: the sync was removed
2026-08-09, so nothing on disk points at it and its copies cannot drift back in.

**All four are now in the tree**, adopted 2026-08-10 under H9. `tests/test_spec_pointers.py`
asserts the three canonical ones are present and non-empty.
`tests/test_regime_prompt_invariants.py` pins `REGIME-PROMPT.md` at **v1.2 or higher** — the
version pin moved there under H10 when v1.2 landed, so the two cannot drift apart.

If any of these ever needs replacing, it comes from Christoph. **Do not reconstruct,
paraphrase or regenerate one** — from memory, or from quotations in handoff files. A
plausible reconstruction of a spec is worse than an absent one, because it will be read as
the record.

### A re-supplied document arrives pre-repair

Specs are authored in the design session, outside this tree, by someone who cannot see it.
**Every repair made here — a path substitution, a status header, a defect fix — is invisible
to the author and is dropped by the next supply of that document.** The file arrives
well-formed, the gate compares bytes and passes it, and the regression is visible only to
whoever remembers making the edit.

**A re-supplied document is re-repaired on landing. It is not authoritative over tree-side
edits.** `docs/specs/RE-SUPPLY.md` lists the invariants; `tests/test_resupplied_docs_are_repaired.py`
fails loudly and names re-supply as the likely cause. **Re-apply, do not re-author** — the
document that arrived is the current content, and the invariant is a repair made to its
predecessor.

**The one case where re-supply is not pre-repair, added 2026-08-12.** If Christoph pastes the
live file *out* of the tree and the design session amends that text and hands it back, no
tree-side edit can have been dropped — the design session was working from the current bytes,
not from memory. **That is the only safe supply route for an adopted spec, and it is
recognisable by exactly one property: the document went out before it came back.** A document
that arrives without having gone out is a reconstruction regardless of how correct it looks.
`test_resupplied_docs_are_repaired.py` cannot tell the two apart, so it will still fire — run
it, and if it fires on a round-tripped file, re-apply and record which invariant was missing.

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

| Path | What goes there | Written by |
|---|---|---|
| `handoff/inbox/NNN-*.md` | Build tasks. Written by chat, addressed to this session. | chat |
| `handoff/done/NNN-*.md` | One per completed task: what changed, what the tests said, what you found. | this session |
| `handoff/accepted/NNN-*.md` | A **byte-identical copy** of the done-note, made once both parties agree nothing further is owed. **The presence of the copy is the acceptance; nothing is authored here.** | **Christoph only** |
| `christoph/open/NNN-*.md` | Items only Christoph can do — UAT and EXTERNAL. **Never write here.** | chat |
| `christoph/done/NNN-*.md` | Their results. | **Christoph only** |
| `handoff/questions/*.md` | Anything needing a **decision rather than a choice**. Frontmatter carries `status: OPEN`. | this session |
| `docs/observations/*.md` | Durable findings about the system, outliving the task that found them. | this session |
| `handoff/*.md` (root) | A **standing instruction that is always live**. Not a task; it stays where it is and no done-note is ever created for it. | chat |

**`handoff/` is copy-and-keep: nothing there is ever moved.** A done-note is *created*
alongside its task file; both coexist permanently. The reason is addressability — `Do inbox
012` resolves a path by name, and a file that moves out from under that name breaks a
reference another party is holding.

**`christoph/` is copy-verify-retire, and only Christoph performs it.** Nothing addresses a
path into `christoph/open/`; its function is to answer *what is still outstanding*, which it
cannot do if completed items stay. Copy to `christoph/done/`, verify byte-identical, then remove the
original. **That is not a move** — a durable copy exists before anything is removed, so the
record is never at risk. **This is a property of `christoph/` alone and is not a precedent for
retiring anything in `handoff/`.** `docs/specs/HANDOFF-PROTOCOL.md` is the authority.

**Every task file, done-note and `christoph/` item carries a `**Status**` header** naming one
of the five states — `WRITTEN | HANDED OFF | RUNNING | REVIEWED | DONE`. **The key is
`**Status**`, never `**State**`**, and the five are the whole vocabulary — `OPEN` is not a
state. A done-note's *frontmatter* is a separate thing and may say what it likes: it describes
the work, while the header describes the handoff.

`handoff/` is **tracked**. In the old repo these files were untracked, so they existed on one
machine and in nobody's history — no sync, no git, no second copy anywhere.

`handoff/done/NNN-*.md` must be **readable cold** by someone with no session context: name
the files, quote the numbers, say what surprised you. "Done as specified" is not a handoff.
The test result belongs in it verbatim — a claim that the suite passed is worth less than the
count that passed and the count that did not.

**Writing a done-note is not the same as reporting.** It lands in a repo chat cannot see, and
on 2026-08-11 two done-notes — `012a` and `013` — were written correctly and never reached
the design session, which held a stale `RUNNING` for both. Nothing in the repo can detect
that. **State plainly, at the end of the note, that it needs to be pasted to chat.**

A **question** is not a task you would rather not do. It is a fork where the answer changes
what gets built and the choice is not yours to make. If you can pick a defensible option and
say why, that is a choice — make it, record it, move on.

### The Drive export — one-way, additive, and not a substitute for judgment

`export-handoff.ps1` copies `.md` files out to two Drive-mirrored folders, so the design
session can read them without Christoph pasting anything:

| Source (this tree) | Destination (Drive-mirrored) |
|---|---|
| `handoff/` (recursive) | `D:\claude-googledrive-sync\momentum-code-handoff\` |
| `christoph/done/` (flat) | `D:\claude-googledrive-sync\momentum-christoph-done\` |

**One-way. It copies new and changed files and deletes nothing, anywhere, ever.** Nothing is
ever read back: **nothing enters this tree except through the adoption gate**, and a mirror
that is also an input is how a superseded copy walks back in wearing the shape of current
work. `tests/test_export_scope_is_derived.py` asserts no Drive path is tracked by git.

**The repository is never mirrored.** Drive watches `D:\claude-googledrive-sync`, outside every
repo. An earlier setup pointed Drive at `handoff/` *inside* the working tree, where a sync
conflict creates a duplicate named something like "012 (1).md" inside `handoff/done/` — which
`git status` then reports as new work. (**That name is deliberately not written as a path
here**: `tests/test_spec_pointers.py` resolves every backticked repo-relative token in this
file, and it correctly failed on the illustration when it was. A hypothetical file must not be
spelled like a real one.)

**`docs/specs/`, `records/` and `christoph/open/` are never exported.** The scope is
**structural, not a forbidden-list**: those folders are absent because they are not named as
sources, and the test derives what may appear in each destination *from the source itself*. A
forbidden-list grows into a hiding place — every folder nobody thought of is implicitly
permitted.

**`christoph/open/` is excluded and this must not be "fixed" later**, because the obvious
improvement is to add it: that folder answers *what is still outstanding* **by being empty**,
and an additive export cannot represent empty — a retired item would sit in the mirror forever
saying the opposite, convincingly. Putting it in Drive needs a mirroring export that deletes,
which is a separate decision.

**Run it at the end of every task, after the commit**, and **state in the done-note whether it
ran and what `HEAD` it recorded.** No watcher, no scheduled job, no filesystem hook: a missed
export is visible in `verify.ps1` section 5; a background process that fails quietly is not.

**Syncing a done-note does not close it.** This is the natural misreading of the whole
mechanism. Christoph still holds the five states; `REVIEWED` still needs the verification
output and `DONE` still needs both parties. **An export removes a transport failure. It does
not remove a judgment.**

## Observations — findings that outlive the task that found them

**Carried forward from `momentum-harness/CLAUDE.md` on 2026-08-12 under 016 §5a.** The
predecessor's convention was complete and well-reasoned, and it sat **beneath a banner
declaring that everything below it is not current guidance** — the project's most-named
failure applied to the machinery for handling the project's failures. Re-stated here, in the
tree that is current. **The archive was read, not modified.**

An **observation** (`docs/observations/`) says **what was seen**, **what produced it**, and
**what would settle it** — one with no test that could resolve it is an opinion. It leaves
that folder by exactly three routes, and **never by being forgotten**:

1. **Promoted to a hypothesis**, with a threshold and a failure path declared *before* the
   data that tests it exists. That is where anything that could change a measurement goes.
2. **Promoted to a spec** in `docs/specs/`, if it turns out to describe intended behaviour
   rather than an open question.
3. **Dropped, with the reason recorded.** Deleting one silently loses the fact that someone
   once thought it mattered.

Write the observation so the reader's **default action is correct**. If the finding is gated —
work that must not be done yet — state the prohibition first and the gap second, and let the
filename carry it too. *"X is outstanding"* reads as a to-do and gets actioned on a quiet
afternoon by someone being helpful.

### The ledger, and why prose was not enough

`docs/observations/OBSERVATIONS.md` is **one row per finding**: id · date · what was seen ·
what produced it · what would settle it · status · review-by. `status` is
**`OPEN` · `PROMOTED` · `DROPPED`**, and the latter two require a `resolution:` naming where
it went or why it did not.

**Every row cites its source. A finding with no source does not go in.** And rows distinguish
an **observation** — something measured — from a **reading**, which is an inference about what
produced it. Conflating those is how a plausible explanation becomes a recorded fact.

`tests/test_observations_ledger.py` goes **RED while any row is `OPEN` past its `review-by`
date** — red for being *ignored*, not for being open. Missing or malformed `review-by` is also
red: **unknown is never read as answered.** **Deleting a row does not clear it** — the only
exits are `PROMOTED` or `DROPPED` with a `resolution:`. An earlier version of
`test_open_questions.py` keyed on a folder being non-empty, which made deletion the cheapest
route to green on a mechanism whose whole purpose was holding things open.

### Rows are added at done-note review

That is the one moment somebody is already reading. **A done-note that names a finding with no
ledger row has not finished reporting it** — the finding is then exactly what this project
keeps rediscovering: a correct observation sitting in a file nobody was instructed to open.

## Spend

Databento is billed per byte. Any sanctioned client must refuse a billable call without a
shown, approved estimate, and a $100/day ceiling in `~/.claude/spend_limits.yaml` overrides
every approval.

**No Databento key is reachable from any Claude-accessible config, deliberately.** The
consequence, stated plainly rather than discovered later: Claude Code cannot run Databento
pulls, and a reserve-then-close ledger cannot be exercised end to end. Any adopted module
touching Databento therefore arrives **untested against a live credential**, and its
provenance companion must say so.

## Captured market data

`records/` is gitignored and **must stay that way — never commit a tape file.** As of
2026-08-11 `records/tape/` holds roughly 2 GB from the QQQ session capture, of which 1.83 GB
is depth.

**`.gitignore` protects the repo, not the disk.**

### Retention — DECIDED 2026-08-12

**`records/tape/` is kept indefinitely, until Christoph says otherwise.** This is a recorded
decision, not the absence of one. v1.1 said *"no retention rule exists yet"*, which read as a
gap somebody might helpfully close; it is now closed, in this direction.

**Why.** The 2026-08-11 QQQ session **cannot be re-recorded** — that tape is a specific
morning and it is gone — and it is the substrate for Layer 0 row 14. **Never delete a session
that any fitted threshold cites as its basis**: a threshold whose basis file is gone has no
source string, which the threshold convention forbids outright.

**No retention policy for FUTURE captures is decided, and that absence is deliberate rather
than an oversight.** A multi-ticker run multiplies this — `012` measured ~7 GB/day for four
tickers with L2 — and nobody has costed the disk. **Do not read the rule above as "keep
everything forever."** It governs the sessions already on disk. The next capture needs its own
decision before it runs, and that decision is Christoph's.

---

## Version history

**Every change to this file increments the version and adds a row. A version is never reused and never decremented.**

| Version | Date | Change |
|---|---|---|
| **v1.7** | 2026-08-15 | **The workflow engine** (045). Records **`sync.ps1`** — the one-word command that pulls Drive into the tree — because until this day the inbound copier had no trigger of its own and **no document stated the invocation**: four UAT files sat in Drive while `christoph/open/` held one `.gitkeep`, and Christoph was the one party who could have unblocked it. Adds the 15-minute scheduled run, **which overturns `037`'s ruling against a daemon**: that objection was to *silence*, and `043`'s run record removed the silence. Adds NOW.md — written into `claude/` by `tools/now.py`, derived from the tree and gitignored, and **deliberately never named as a backticked path**, because a pointer to a generated file is red on a fresh clone. **And moves the decision line**: rule 16's product/admin split now governs who may decide, so Claude Code may author and act on its own `class: admin` task in one session — with four guardrails, of which the load-bearing one is that **admin unblocking admin remains forbidden**. `037` flagged this version bump as owed and correctly did not take it unasked; `045` asks. |
| **v1.6** | 2026-08-13 | **The active tree gets a remote** (017). Records `origin` as `trading-terminal` and the habit that follows from it: **push at the end of every session, because a commit is local and only a push survives the disk.** Names the archive explicitly — **`momentum` on GitHub is `momentum-harness` and is never pushed to** — since that collision is why a new repository exists rather than the old name reused. **Flags that `D:\Dev\CLAUDE.md` v1.1 still says the opposite** and must be corrected, rather than leaving a reader to guess which of two statements is current. Notes that the repository is `trading-terminal` and **not the `momentum-terminal` that 017 proposed**, so the unused name is not mistaken for the real one. |
| **v1.5** | 2026-08-13 | **The Drive export** (020). `export-handoff.ps1` carries `handoff/` and `christoph/done/` one-way to two Drive-mirrored folders, ending the class of failure where four correct done-notes were written on 2026-08-11 and none reached the design session. Records both destinations, the one-way direction, and that **the repository itself is never mirrored**. States **why `christoph/open/` is excluded** — it answers by being empty, and an additive export cannot represent empty — because the obvious "improvement" is to add it. Carries the sentence that is the natural misreading of the whole task: **syncing a done-note does not close it.** `verify.ps1` gains section 5, so a stale mirror is visible rather than silent. |
| **v1.4** | 2026-08-12 | **The retention position becomes a decision** (016 §6). `records/tape/` is kept indefinitely until Christoph says otherwise, with its reason: the 2026-08-11 QQQ session is unrepeatable and is Row 14's basis. v1.1 said *"no retention rule exists yet"*, which reads as a gap someone might helpfully close. **States explicitly that no policy for FUTURE captures is decided**, so the rule is not read as "keep everything forever". |
| **v1.3** | 2026-08-12 | **The observations convention, carried forward from the archive** (016 §5a). `momentum-harness/CLAUDE.md` held a complete version of it **beneath a banner saying nothing below is current guidance** — so the machinery for handling this project's recurring failure was itself an instance of it. Adds the three exit routes, the `OBSERVATIONS.md` ledger and its schema, the observation-versus-reading distinction, and the rule that **rows are added at done-note review**. The archive was read, not modified. |
| **v1.2** | 2026-08-12 | **A broken pointer fix, and nothing else.** Line 159 named `done` with a trailing slash and no parent — prose shorthand for `christoph/done/`, which `tests/test_spec_pointers.py` correctly read as an unresolvable repo-relative token. **Introduced by the v1.1 re-supply; not a content change.** Recorded as its own version because the rule has no size threshold: **a version that skips small fixes stops being a reliable identity for the file.** The rest of the file is byte-identical to v1.1. Checked for other bare-folder shorthand — a subfolder named without its parent, such as `open`, `accepted`, `inbox` or `questions` — and this was the only instance. **Written without trailing slashes deliberately: with them, this very row would have introduced five new unresolvable pointers**, which it did on the first attempt. |
| **v1.1** | 2026-08-12 | Handoff table gains `handoff/accepted/`, `christoph/open/`, `christoph/done/` and a *written by* column — **three of those Claude Code must never write to.** Adds: the `handoff/` copy-and-keep vs `christoph/` copy-verify-retire split; the `**Status**` header rule and its five-state vocabulary; the round-trip exception to the re-supply rule; the `records/` retention position; and the statement that **writing a done-note is not reporting it.** |
| **v1.0** | 2026-08-10 | The file as it stood at tree birth: adoption gate, evidence carry, `docs/specs/` as location of record, re-supply pre-repair, handoff convention, spend. |

**v1.0 was not numbered when it was written.** The number is applied here retrospectively and is a declaration made now, not a fact recovered from the file. Git history is the authority on what that content actually was.

**`D:\Dev\.claude.md` is a separate file and is not covered by this version.** It is stale — dated 2026-08-07, still describing `momentum-harness` as the umbrella, with corrupted venv paths — and its filename is a dotfile, so **it may not be read at all.** Confirm whether it is loaded before deciding to repair or delete it; do neither on inference.
