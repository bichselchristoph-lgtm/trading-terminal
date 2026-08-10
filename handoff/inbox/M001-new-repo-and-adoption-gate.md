# M001 — New repo, adoption gate, evidence carry

**Status** OPEN · **Date** 2026-08-10 · **Type** migration · **Depends on** H9a
**Order:** H9a → **M001** → H9 v3 → H8. H9a's inventory is the input; without it there is no adoption candidate list and this task has nothing to work from.

> Read this cold. The session that wrote it cannot answer questions and cannot see the repo.

---

## What this does

`momentum-harness` is a mix of authored and wholesale-imported folders, and the import is what produced the current state: a `README.md` describing another repo's tree, a condition-code vocabulary invented by an unidentified codebase, mockups pointing at `D:\tradesignals\`, and a spec directory where nothing declares whether it is current.

**This has happened once already.** `tradesignals` → `momentum-harness`, folders carried across wholesale. Doing it again the same way repeats it. **The fix is not a cleaner copy — it is a gate**, in the same shape as the watchlist ingestion that already works: a file lands in an unversioned drop folder, passes every check, and is copied into the repo only after, so **git history records what was actually adopted rather than everything ever carried across.**

**New tree:** `D:\Dev\momentum`. Named to match `SPEC.md` §3.1 defect 4, which already instructs that `tradesignals\` references become `momentum\`.

**`momentum-harness` is not deleted and not modified beyond §1.** It becomes read-only reference, the same status `tradesignals` holds now.

---

## §0 — Two things before a new directory exists under `D:\Dev`

**§0a is Christoph's and is blocking — it becomes dangerous the moment the new repo exists. §0b is already done; what remains of it is recorded below so it is not re-raised.**

**0a. Delete `push_all.ps1`.** It iterates every directory under `D:\Dev` and pushes each, and four of those remotes are archived and read-only (H2). **Creating `D:\Dev\momentum` adds a fifth target to a script that pushes without asking.** Delete it before the directory exists, not after.

**0b. The Databento key is already rotated** (Christoph, 2026-08), and the new key was deliberately never given to Claude. **H1's security half is closed** — the string in `D:\Dev\.claude\settings.local.json` is a dead credential, not a live exposure.

**Two things remain, and neither is urgent enough to block §1.**

1. **Delete the three stale allow-rules anyway.** They hold a credential that no longer works, so anything reaching for them fails auth rather than falling back — which is the correct failure, but it will present as a confusing Databento error rather than a missing-config error. Note the likely form: a key inside an `--extra-index-url https://user:key@…` line.
2. **The new repo's `test_no_secrets.py` must scan `.claude/`, `requirements*.txt` and every dependency-manifest format, and match on Databento's key shape (`db-` prefix) rather than on assignment syntax.** The old one passed only because it never looked there. Build it correctly at birth — see §2.

**Consequence to state plainly rather than discover later:** with no key in any Claude-accessible config, Claude Code cannot run Databento pulls and `harness/spend.py`'s reserve-then-close ledger cannot be exercised end to end. That is fine — Databento work is gated behind slice 017 — but it means any adopted module touching Databento arrives **untested against a live credential**, and its provenance companion must say so.

---

## §1 — Freeze the old repo

1. Add `ARCHIVED.md` at `momentum-harness` root: this repo is reference only as of 2026-08-10, the active tree is `D:\Dev\momentum`, nothing here is authoritative, and files leave only through M001's adoption gate.
2. Add the same statement as the **first section** of `momentum-harness/CLAUDE.md`, so a Claude Code session opened there sees it before doing anything.
3. **Do not delete, rewrite, `git rm`, or reorganise anything else in it.** Tenet 11 — a changed source lowers confidence, never discards. This repo is now a source.

---

## §2 — Bootstrap the new tree

`D:\Dev\momentum`, `git init`, and **only** the following. Everything else arrives through §3.

```
.gitignore              written fresh — must include .claude/ and .venv/
pytest.ini              testpaths covers every test directory, not just tests/
requirements.txt        written fresh; no index URL carrying credentials
CLAUDE.md               written fresh — NOT copied
README.md               written fresh — one screen, and true
docs/specs/             the four canonical documents (H9 supplies them)
handoff/inbox/          empty
handoff/done/           empty
tests/                  the three tests below
ADOPTION-LOG.md         empty table with headers
```

**`CLAUDE.md` and `README.md` are written, not carried.** The old `README.md` describes a tree that does not exist; copying it forward is how it survived this long. `CLAUDE.md` keeps the handoff convention and the `docs/specs/` status rule, and drops everything referring to the old tree.

**`pytest.ini` fixes the collection defect at birth:** the old one set `testpaths = tests`, so seven behavioural tests in `live/tests/` were never collected and two consolidations shipped a broken `live/` that stayed green.

---

## §3 — The adoption gate

### The drop folder

```
D:\Dev\_adopt\                 unversioned, outside both repos, never committed
```

A candidate is copied from `momentum-harness` into `_adopt\` with a provenance companion, and **enters `D:\Dev\momentum` only after passing every check below.** A failed adoption leaves no trace in the new tree — same rule as a failed watchlist drop.

### Four refusals

| # | Refusal | Why |
|---|---|---|
| 1 | **No provenance companion** | `<name>.provenance.md`: source path in the old repo, origin from H9a's table, the reason it is being adopted, and what depends on it. **No default, no inferred value.** |
| 2 | **No test** | Nothing enters `core/`, `live/`, `harness/` or `tools/` without at least one behavioural test that fails if the file's behaviour changes. Import-smoke does not count — `regime_pull.py` passed import coverage while raising `NameError` on the first call. |
| 3 | **Same name, different content** | A name already in the new tree with different bytes refuses. Never silently overwrite; never auto-rename. |
| 4 | **Origin `unknown` or `imported` in H9a's table, without an explicit adoption decision** | An `authored` row can be adopted on its merits. An `imported` or `unknown` row requires Christoph to say, in the provenance companion, why this project is adopting a predecessor's artifact. **The `by`-less status exists precisely because that decision was never made last time.** |

### Every adoption is logged

`ADOPTION-LOG.md`, one row per file: `date · path in new tree · source path · origin (from H9a) · reason · test that covers it · adopted by`.

### The test that makes it stick

`tests/test_adoption_log_complete.py` — **every tracked file outside the §2 bootstrap allowlist appears in `ADOPTION-LOG.md`.** A file that arrives by any other route goes red.

This is the whole mechanism. Without it the gate is prose, and a convention that lives in prose depends on someone remembering. With it, wholesale import is not discouraged — it is impossible without a visible failing test.

---

## §4 — Evidence carries differently

**Evidence is not adopted. It is carried, verbatim, and it does not pass through the gate**, because the gate's question — *is this worth keeping* — does not apply to a record of what happened. Evidence cannot be regenerated from a spec, and the trade log is already the highest-leverage missing artifact in the system.

Carry byte-identical, verify by hash, log the hashes:

```
records/
records_truncated/
spend_ledger.jsonl              harness/spend.py's reserve-then-close ledger
membership_evidence.json
handoff/done/                   what was built and what surprised the builder
handoff/inbox/                  open tasks — carry, then triage in §5
```

**Do not clean, dedupe, reformat, prune or "tidy" any of it.** If a file looks wrong, say so in the done-note and carry it anyway. **Do not regenerate any of it** — a regenerated ledger is a well-formed value answering a different question, and it will be read later as a record of what happened.

**`records_truncated/` carries too, despite the name**, unless H9a's table shows it imported and unreferenced. Establish which before deciding; do not decide from the name.

**Git history does not carry.** The new repo starts at commit one. `momentum-harness` retains its history and stays on disk — that is where history lives now, and `ARCHIVED.md` says so.

---

## §5 — Triage the inbox on arrival

Seven task files carry across. **Three need a decision before the new tree treats them as work pending**, and an untriaged inbox is indistinguishable from a backlog:

- **`005-regime-context.md`** — `SPEC.md` §3.2 deleted the regime surface from the terminal entirely. Expected: close as superseded. Read it before agreeing.
- **`008a-ibkr-data-verification.md` / `008b-keepuptodate.md`** — the 008 slot is split, which `BUILD-PLAN.md` §3 did not anticipate; it reserves 008 for *make `live/` testable*. Establish what each contains and whether the slice still has a home.
- **The rest** — carry as-is.

**H4 applies on arrival:** the inbox tasks were **untracked** in the old repo, so the convention that assumes chat syncs `handoff/` was silently not holding. `git add` them in the new tree, and confirm `.gitignore` does not exclude `handoff/`.

---

## §6 — Do not

- Do not delete `momentum-harness`, or anything inside it beyond §1's two additions.
- Do not adopt `core/config/condition_codes.yaml`. Its own banner says the codes are a vocabulary the codebase invented and the delivery carries no condition field (H6). If it is needed, it is **written fresh against the delivery**, not carried.
- Do not adopt `live/regime/regime_pull.py`. Slice 008 deletes it; Layer 1 lives in the scheduled task (`SPEC.md` §3.2). **Name the last commit in `momentum-harness` containing it in the done-note**, so it is retrievable in one command.
- Do not adopt `live/_to_merge/` until H5 and H9a §3b have established what "step 7" refers to.
- Do not copy `.claude/` in any form.
- Do not adopt anything H9a marks `imported` that nothing references. Name it; leave it.

---

## What this changes downstream

**`BUILD-PLAN.md` §3 assumes the existing tree.** Slice 008 is *make `live/` testable* — in a repo where `live/` exists only once adopted, and where adoption already requires a behavioural test (refusal 2), 008's content changes substantially. **Do not renumber or reinterpret the slices in this task.** Report the collision; `BUILD-PLAN.md` needs a v1.2 written deliberately once adoption is done, not a quiet renumber inside a migration.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | `pytest` passes in `D:\Dev\momentum` with the three tests present. **A near-empty test run is the expected result** and is not a problem to solve by adopting more. |
| **Refusal** | Claude Code | Three, each proving one gate holds. (a) Copy a file directly into the new tree bypassing `_adopt\` and confirm `test_adoption_log_complete` fails naming it. (b) Drop a candidate into `_adopt\` with no `.provenance.md` and confirm the adoption refuses. (c) Drop a candidate whose name already exists with different bytes and confirm refusal 3 fires without overwriting. |
| **UAT** | Christoph | Confirm `push_all.ps1` is gone and the Databento key is rotated **before** `D:\Dev\momentum` exists. Then: `git log --stat` in the new repo — every commit should be one adoption or one bootstrap file, and you should recognise every one. **Write down how many files you expect the new tree to hold before running `git ls-files | wc -l`.** The gap is the finding. |

## Done-note must state

- Confirmation, from Christoph, that §0a was completed before the new directory was created. (§0b's rotation is already done; record only whether the stale allow-rules were deleted.)
- Every adopted file with its `ADOPTION-LOG.md` row.
- Every evidence file carried, with source and destination hashes, and any hash mismatch.
- The triage decision on `005`, `008a`, `008b`, quoting enough of each to justify it.
- Every candidate refused, which refusal fired, and whether it was later adopted.
- The `BUILD-PLAN.md` slice collisions, named, with no proposed renumbering.
