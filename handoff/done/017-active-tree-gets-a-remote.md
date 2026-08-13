# 017 — HALTED at Part 2 — the active tree still has no remote

**Status** RUNNING · **Date** 2026-08-13 · **Type** infrastructure · **Tree** `D:\Dev\momentum`

> **This note needs to be pasted to chat.**
>
> **Nothing was pushed. No remote was added. No repository was created.** The task halted at
> its own stopping conditions, all three of which fired. This note records what was verified
> so that the run is not repeated from scratch when the blocker clears.

---

## The headline

**017 cannot complete today, and two of the three reasons are not about 017 at all.**

| # | Gate | Result |
|---|---|---|
| **1** | **Part 1 — Christoph creates the repository** | **NOT DONE.** No repository exists and no clone URL has been supplied anywhere in the tree. The task says *"Nothing in this task guesses it."* |
| **2** | **Part 2c — the working tree is clean** | **FAILED**, and it got dirtier *during* this session. A concurrent session is executing `030` in the shared checkout right now. |
| **3** | **Exit test "Green" — full suite before the push** | **FAILED.** `13 failed, 269 passed` at `59fc2ab`. Eight of those are `030`'s, committed and known. |

Parts 2a and 2b **passed** and are reported in full below, so they do not need re-running.

**017's number is not taken.** There is one `017` in `handoff/inbox/` and none in
`handoff/done/` before this note. The task's own caveat about re-issue does not apply.

---

## 1. Part 1 — no clone URL exists

`momentum` has **no remote configured at all**:

```
$ git remote -v
(no output)
```

A search of the whole tree for `momentum-terminal` or any `github.com/*/momentum` URL returns
**two hits, both inside the task file itself** (lines 38 and 83 of
`handoff/inbox/017-active-tree-gets-a-remote.md`) — the proposed name and the `CLAUDE.md`
habit text. Nothing in `christoph/done/` supplies a URL. There is no `christoph/open/` item
for repository creation.

**Part 3 is therefore unreachable**, and with it the `CLAUDE.md` edit, which would otherwise
assert a remote that does not exist.

---

## 2. Part 2a — `test_no_secrets` passed, and here is exactly what that covers

**`20 passed`**, run on its own. The task asks for this to be stated honestly, because a first
push is when the gap matters most. **It is stated by the test itself, on every run**, in a
header the repo prints deliberately:

```
credential scan roots:
  PRESENT  repo                     D:\Dev\momentum  (386 files read)
  PRESENT  Dev/.claude              D:\Dev\.claude  (1 files read)
  ABSENT   Dev/.claude.json         D:\Dev\.claude.json
  ABSENT   Dev/.mcp.json            D:\Dev\.mcp.json
  ABSENT   D:/.claude               D:\.claude
  ABSENT   D:/.claude.json          D:\.claude.json
  ABSENT   D:/.mcp.json             D:\.mcp.json
  NOT COVERED: the user-level ~/.claude - see OBS-020
```

**What it covers:** the **working tree as it stands right now** — 386 files, matched on
credential *shape* (`db-` prefix, `AKIA`/`ASIA`, private-key blocks, credentials embedded in
`--extra-index-url`), plus every dependency manifest regardless of suffix, plus the `.claude`
of every ancestor of the repo.

**What it does NOT cover, and this is the part that matters for a first push:**

- **It does not scan git history.** It reads files on disk. **A credential committed and later
  removed is invisible to it**, and a first push publishes every commit, not the current state.
  The suite going green is **not** evidence that the history is clean.
- **It does not scan `records/` or `records_truncated/`** — deliberately narrowed after the
  scan started reading 1.8 GB of depth JSONL on every run. Those are gitignored and never
  committed, so a *committed* secret cannot be there.
- **It does not scan the user-level `~/.claude`** — the declared blind spot, OBS-020.
- **It does not cover untracked files it happens to read** in any way that distinguishes them
  from tracked ones. It reads the tree, not the index.

**So: tracked files scan clean; the history was not scanned by anything.** If a history scan
is wanted before the first push, that is a separate tool and a separate task.

---

## 3. Part 2b — `records/` is genuinely excluded

`git check-ignore -v` against real files in `records/tape/`, verbatim:

```
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-depth.jsonl
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-provenance.json
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-quotes.jsonl
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-summary.json
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-trades.jsonl
```

**The rule that ignores it is `/records/` at `.gitignore` line 42.** It is **anchored** — the
leading slash roots it at the repo top level — so it is not one of the unanchored patterns the
task warned about. Its stated purpose in the file is *"Local append-only run state, carried as
evidence but not tracked."*

`git ls-files records/` returns **0 files**. Nothing under `records/` is tracked.

### The size that would actually be pushed

| Measure | Value |
|---|---|
| Tracked files | **194** |
| Packed objects | 289, **788.20 KiB** |
| Loose objects | 437, **940.64 KiB** |
| **Whole `.git` object store** | **≈ 1.7 MB** |
| `records/tape/` on disk | **3.9 GB — excluded** |

**A push would move under 2 MB.** The tape is not in it.

> **Wrong on contact:** the task says *"confirm it does not include the 2 GB of tape."*
> **`records/tape/` is 3.9 GB, not 2 GB.** `CLAUDE.md` v1.5 also still says "roughly 2 GB".
> The 2026-08-12 capture under `019` roughly doubled it. The exclusion is unaffected — the
> rule is a directory, not a size — but the figure quoted in two places is now stale.

---

## 4. Part 2c — the tree is not clean, and it is moving

At session start:

```
 M christoph/open/013-s010-check-against-your-charts.md
 D christoph/open/014-for-christoph-account-parameters.md
?? christoph/done/014-for-christoph-account-parameters.md
?? handoff/inbox/029-for-code-the-app-has-no-entry-point.md
?? handoff/inbox/030-for-code-regime-prompt-v1.8-full-text.md
```

**Fourteen minutes later, two more files had changed without this session touching anything:**

```
 M docs/specs/REGIME-PROMPT.md          (mtime 16:15:43)
 M tests/test_regime_prompt_invariants.py
```

`docs/specs/REGIME-PROMPT.md` in the checkout is now **v1.8, dated 2026-08-13**, against
**v1.2** at `HEAD`. That is task `030` — *"regime-prompt v1.8 full text"* — **in flight in the
shared checkout as this note is written.** There is also a locked worktree at
`.claude/worktrees/029-entry-point` on branch `worktree-029-entry-point` at `894549f`,
carrying task `029`.

**By 16:20 that session had committed** — `59fc2ab`, *"v1.8 lands byte-identical, and eight
invariants now disagree with it"* — and had run `export-handoff.ps1`, which put its own
done-note into the Drive mirror. So `030` is finished. But it finished **after** this session
had already run its checks, which is the point:

**This is the strongest of the three reasons to halt, and it is a scheduling problem, not a
one-off.** 017's own argument is that *"the first commit reachable from a remote is the one
people trust most"*. Had this session pushed on its first clean-looking read, it would have
published a snapshot containing another session's half-applied spec edit. **Nothing was
committed to `main` and nothing was pushed**, per the task's explicit instruction.

**A first push should not be run concurrently with other sessions.** 017 assumes a still tree
and says so implicitly by requiring one; the tree was not still, twice, inside four minutes.

The `christoph/` entries are **Christoph's own copy-verify-retire of `014`, mid-flight** — the
`done/` copy exists and the `open/` original is removed but not yet staged. That is the
protocol working, not a defect.

---

## 5. The suite: `13 failed, 269 passed` — and only 2 are the tree's

**Two runs, because the tree moved between them.** This is the honest sequence rather than a
tidy single number:

| When | `HEAD` | Result |
|---|---|---|
| ~16:18 | `49fb4d7`, working tree dirty with `030` half-applied | `15 failed, 267 passed` |
| **~16:22** | **`59fc2ab`, `030` committed** | **`13 failed, 269 passed`** — *the authoritative figure* |

The second is the one to quote. **Every failure in it is accounted for**, which took a
comparison run against a clean `HEAD` in a scratch worktree to establish — see Housekeeping for
that worktree's disposal:

| Cause | Count | Tests |
|---|---|---|
| **`030`, committed and known** | **8** | `test_regime_prompt_invariants` ×5, `test_regime_snapshot_could_not_do`, `test_regime_snapshot_path`, `test_resupplied_docs_are_repaired::test_invariant_2` |
| **Pre-existing, and nobody's current task** | **2** | `test_handoff_state_declared` (inbox `021`–`027` carry no `**Status**` header), `test_uat_has_a_file` (`020`'s done-note names a UAT with no file in `christoph/`) |
| **Christoph's `014` retirement, mid-flight** | **2** | `test_observations_ledger::test_every_retired_uat_has_a_register_row`, `::test_refusal_b_a_retired_uat_with_no_destination_is_red` |
| **Concurrent worktrees** | **1** | `test_pytest_collection::test_every_directory_holding_tests_is_declared` — reports `.claude/worktrees/029-entry-point/` and its three test directories |

8 + 2 + 2 + 1 = **13.** The accounting is exact.

**`030`'s commit message names its own eight** — *"v1.8 lands byte-identical, and eight
invariants now disagree with it"* — and that is the same eight counted here. Two tests that
were red before it committed are now green: `test_spec_pointers::test_every_spec_declares_status`
and `test_resupplied_docs_are_repaired::test_invariant_1`.

**None of the 13 is 017's to fix, and none is caused by 017.**

**The clean-`HEAD` run reported `6 failed, 276 passed`**, but **4 of those 6 were artifacts of
being a worktree**, not tree defects — `test_evidence_carry_intact` ×2, `test_spec_pointers::
test_claude_md_pointers_resolve` and `test_sync_from_drive::test_the_destination_paths_are_inside_the_repo`
all fail in a worktree because gitignored paths (`records/`, the Drive folders) do not exist
there. **They pass in the real checkout.** Quoted here so nobody reads "6 failed at HEAD" as a
finding — the real pre-existing count is **2**.

### `test_pytest_collection` is load-bearing and a worktree trips it

**A worktree of this repo lives inside the repo** (`.claude/worktrees/`), so its `tests/`,
`core/tests/` and `live/tests/` are seen by the collection guard as undeclared test
directories. **This is not a bug in the guard** — it correctly refuses to let a test directory
exist unlisted. But it means *any* concurrent worktree session turns that test red for
*everyone*, and the redness is not about the code. Worth an observation row; it will recur.

---

## 6. Refusal B — `momentum-harness` is untouched

Captured **before** any work and **again after**. Byte-identical.

```
$ cd D:\Dev\momentum-harness && git remote -v
origin	https://github.com/bichselchristoph-lgtm/momentum.git (fetch)
origin	https://github.com/bichselchristoph-lgtm/momentum.git (push)

$ git config --get-regexp '^remote\.'
remote.origin.url https://github.com/bichselchristoph-lgtm/momentum.git
remote.origin.fetch +refs/heads/*:refs/remotes/origin/*
```

**No command in this session wrote to `momentum-harness`.** It was read twice.

Note the archive's remote confirms 017's premise exactly: **the GitHub repo named `momentum`
is the archive.** The collision is real.

---

## 7. Part 3 and Part 4 — what was deliberately NOT done

**Part 3 — the remote, the push, the `CLAUDE.md` edit.** Not started. It depends on a URL that
does not exist. **`CLAUDE.md` is unmodified**; it still carries the v1.1 text saying the remote
is unsettled and the active repo must not be pushed. **That text is still true today** and must
stay until the push actually happens. Correcting it now would make the file describe a remote
that is not there — the exact two-statements problem 017 warns about, arrived at from the other
side.

**For whoever finishes this:** the version to supersede is **v1.5**, so the push habit lands as
**v1.6**. `016` did not bump it; `020` did.

**Part 4 — the tape's single-copy exposure.** 017 asks for a `christoph/open/` EXTERNAL item.

> **Wrong on contact, and it is a protocol conflict rather than a slip.** `CLAUDE.md` says
> `christoph/open/` is **written by chat** and *"Never write here."* `docs/specs/CHRISTOPH-TASKS.md`
> is the authority and agrees: *"the design session authors the task file. Christoph saves it to
> `christoph/open/`."* **Claude Code cannot satisfy Part 4 as written.** 017 predates
> `CLAUDE.md` v1.5 by a day, which is likely how it arose.
>
> **The item is therefore drafted here for chat to author.** Its substance, in one paragraph:
>
> *`records/tape/` holds 3.9 GB across two capture sessions, including the 2026-08-11 QQQ
> session. It is gitignored, so the push this task performs will not protect it. That session
> cannot be re-recorded — it is a specific morning — and it is the declared basis for Layer 0
> row 14, which under the threshold convention means deleting it would leave a fitted
> threshold with no source string. It exists on exactly one disk today and will still exist on
> exactly one disk after 017 completes. Where a second copy lives is undecided, and 017
> deliberately did not cover it: no LFS config, no sync script, no git addition. The decision
> is Christoph's.*

---

## 8. What is needed to unblock, in order

1. **Christoph creates the empty private repository** (proposed `momentum-terminal`; **not**
   `momentum`) — no README, no `.gitignore`, no licence — **and supplies the clone URL.**
   **This is the only true blocker.** Everything else below is a judgment call.
2. **`029` lands or reverts** (`030` already has, at `59fc2ab`), and Christoph's `014`
   retirement is staged, so the working tree is clean and no worktree is open.
3. **Decide what to do about the 13.** They will not all clear on their own:
   - The **8 from `030`** are that task's declared finding, not a regression. Someone has to
     say whether the invariants or the document are wrong before they go green.
   - The **2 pre-existing** need their own tasks — `021`–`027` need `**Status**` headers, and
     `020` needs its UAT file.
   - The **2 from `014`** clear when Christoph stages his retirement.
   - The **1 collection failure** clears when the worktrees close.

   **A first push against 13 red is a decision, not an oversight** — and it is Christoph's.
   The alternative reading, that 017 waits until the suite is green, could wait a long time.
   **017 as written assumes green and does not contemplate this**; that is the judgment it
   hands back.
4. Then Parts 2c, 3 and the `CLAUDE.md` v1.6 bump run as written.

---

## Exit tests

| Test | Who | Result |
|---|---|---|
| **Green** | Claude Code | **NOT MET.** `13 failed, 269 passed` at `59fc2ab`; 8 are `030`'s declared finding, 2 pre-existing, 2 mid-retirement, 1 from open worktrees. No push, so **no hash pair to compare** — `git ls-remote` has no URL to run against. |
| **Refusal A** | Claude Code | **PASSED.** `check-ignore` output quoted verbatim in §3; rule named as `/records/` at `.gitignore:42`, anchored. |
| **Refusal B** | Claude Code | **PASSED.** `momentum-harness` remote quoted before and after in §6, byte-identical. |
| **UAT** | Christoph | **None** yet — no repository exists to open, so there is nothing to verify. It is owed once Part 1 and Part 3 land, and chat should author it then. |

## Ledger

Two findings in this note warrant `docs/observations/OBSERVATIONS.md` rows, added at review:

- **A concurrent worktree turns `test_pytest_collection` red for every session** (§5). Seen:
  `.claude/worktrees/029-entry-point` reported as three undeclared test directories. Would
  settle it: decide whether `.claude/worktrees/` is excluded from the guard's walk, or whether
  a red collection test is the accepted cost of concurrent sessions.
- **`records/tape/` is 3.9 GB, not the ~2 GB quoted in `CLAUDE.md` v1.5 and in `017`** (§3).
  Would settle it: a size check in `verify.ps1`, so the figure is observed rather than
  remembered.

## Housekeeping

This note was written on branch **`worktree-017-remote`**, because the shared checkout was
being edited by another session throughout and could not be safely written to. **The branch is
based on `59fc2ab`**, the current tip of `main`, so it lands as a fast-forward with no conflict
— it adds exactly one new file and touches nothing else:

```powershell
cd D:\Dev\momentum
git merge --ff-only worktree-017-remote
git worktree remove .claude/worktrees/017-remote
.\export-handoff.ps1
```

**Until that runs, this note is not on `main`, is not in the Drive mirror, and chat cannot see
it.** The worktree removal is part of the sequence rather than an afterthought: while it exists
it adds rows to `test_pytest_collection`'s failure for every other session.

**No push, no remote, no `CLAUDE.md` edit, nothing on GitHub, and `momentum-harness` untouched.**
