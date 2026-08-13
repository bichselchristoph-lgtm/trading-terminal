# 017 — done — the active tree has a remote, and the first push has landed

**Status** RUNNING · **Date** 2026-08-13 · **Type** infrastructure · **Tree** `D:\Dev\momentum`

> **This note needs to be pasted to chat.**
>
> **It declares a UAT that does not yet exist as a file, and `test_uat_has_a_file` is red as a
> result.** That is the mechanism working, not a defect — see §9. Chat must author the
> `christoph/open/` item.

---

## The headline

**`D:\Dev\momentum` is no longer on one disk.** Everything since 2026-08-10 — the adoption
gate, the protocol, the TUI, every done-note — is now on GitHub.

| | |
|---|---|
| **Remote** | `origin` → `https://github.com/bichselchristoph-lgtm/trading-terminal.git` |
| **Local `HEAD` (`main`)** | `6b7dc1d43b9459aefd189df8cfc12c29c6ae33d2` |
| **`git ls-remote origin` (`refs/heads/main`)** | `6b7dc1d43b9459aefd189df8cfc12c29c6ae33d2` |
| **Match** | **Yes — identical, verified independently of the push's own output** |

**The repository is `trading-terminal`, not the `momentum-terminal` 017 proposed.** Christoph
created it under a different name and that name is now written into both `CLAUDE.md` files, so
the proposal is not mistaken for the remote.

---

## 1. Both hashes, and the full remote state

`git ls-remote origin`, verbatim:

```
6b7dc1d43b9459aefd189df8cfc12c29c6ae33d2	HEAD
6b7dc1d43b9459aefd189df8cfc12c29c6ae33d2	refs/heads/main
f27b7e29faa8125c207316a44cac86f37891e443	refs/heads/worktree-017-remote
894549fed8ee4c579ca3867a3651971a5b8d32fe	refs/heads/worktree-029-entry-point
```

Local `git show-ref`, same three, byte-identical. **Three refs were pushed, not one** — the two
worktree branches went up alongside `main`, which is more than 017 asked for and is a good
outcome: two concurrent sessions' work is now backed up too.

**017 asked for `git ls-remote` compared to local `HEAD`, and that is what this is.** A push
that reports success is a claim; this is the check.

---

## 2. What was pushed, and what was not

| Measure | Value |
|---|---|
| Tracked files | **194** at the time of the size check |
| Packed objects | 289, **788.20 KiB** |
| Loose objects | 437, **940.64 KiB** |
| **Whole `.git` object store** | **≈ 1.7 MB** |
| `records/tape/` on disk | **3.9 GB — excluded, confirmed below** |

**The push moved under 2 MB. The tape is not in it.**

### Refusal A — `check-ignore`, verbatim, with the rule named

```
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-depth.jsonl
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-provenance.json
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-quotes.jsonl
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-summary.json
.gitignore:42:/records/	records/tape/QQQ-2026-08-11-trades.jsonl
```

**The rule is `/records/` at `.gitignore` line 42.** It is **anchored** — the leading slash
roots it at the repo top level — so it is not one of the unanchored patterns 017 warned about,
and it cannot match a `records/` directory nested somewhere else by accident.

`git ls-files records/` returns **0 files**. Checked against real files, not by reading
`.gitignore`.

---

## 3. What `test_no_secrets` actually covers — stated honestly

**`20 passed`.** 017 asks for this to be stated plainly because a first push is the moment the
gap matters most. **The test states it itself, on every run**, in a header this repo prints
deliberately:

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

**Covered:** the working tree as it stands — 386 files — matched on credential *shape* (`db-`
prefix, `AKIA`/`ASIA`, private-key blocks, credentials inside `--extra-index-url`), every
dependency manifest regardless of suffix or location, and the `.claude` of every ancestor of
the repo.

**NOT covered, and this is the part that matters for a first push:**

- **It does not scan git history.** It reads files on disk. **A credential committed and later
  removed is invisible to it** — and a first push publishes every commit, not the current
  state. **The suite going green is not evidence that the history is clean.** Nothing in this
  task scanned the history, and nothing in this repo does.
- **It does not scan `records/` or `records_truncated/`**, narrowed deliberately after the scan
  started reading 1.8 GB of depth JSONL on every run. Both are gitignored and never committed,
  so a *committed* secret cannot be there.
- **It does not scan the user-level `~/.claude`** — the declared blind spot, OBS-020.

**Tracked files scan clean. The history was scanned by nothing.** If a history scan is wanted
now that the tree is public-ish, that is a separate tool and a separate task.

---

## 4. Refusal B — `momentum-harness` is untouched

Captured **before** any work and **again after the push**. Byte-identical.

```
$ cd D:\Dev\momentum-harness && git remote -v
origin	https://github.com/bichselchristoph-lgtm/momentum.git (fetch)
origin	https://github.com/bichselchristoph-lgtm/momentum.git (push)

$ git config --get-regexp '^remote\.'
remote.origin.url https://github.com/bichselchristoph-lgtm/momentum.git
remote.origin.fetch +refs/heads/*:refs/remotes/origin/*
```

**No command in this session wrote to `momentum-harness`.** It was read twice, before and
after. Its remote confirms 017's premise exactly: **the GitHub repo named `momentum` is the
archive.** The collision was real, and creating a new repository is what left that history
undisturbed.

---

## 5. Both `CLAUDE.md` files, and which versions this produced

| File | Was | Now |
|---|---|---|
| `CLAUDE.md` (this tree) | **v1.5** | **v1.6** |
| `D:\Dev\CLAUDE.md` (workspace) | **v1.1** | **v1.2** |

**017 said to read the file rather than assume v1.2. Read: `016` did not bump it — `020` did,
to v1.5 — so the push habit landed as v1.6.**

### The two-statements problem, resolved in the direction 017 asked for

017 says to remove or correct the v1.1 text saying the remote is unsettled, and **not to leave
both statements in the file.** That text was **not in this tree's `CLAUDE.md` at all** — it was
in `D:\Dev\CLAUDE.md`, one level up, under the heading *"The remote is not settled — do not
push `momentum/`"*.

**It is inverted, not deleted**, and its first line now says it previously said the opposite. A
reader who remembers the old rule must be able to see that it *changed*, rather than quietly
find different words and wonder which file is current.

The `push_all.ps1` warning there was **re-grounded rather than removed.** It rested partly on
the unsettled remote and partly on the four archived read-only repos. The first reason is gone;
the second is not, so the conclusion — **do not run it** — is unchanged and now says why.

> **`D:\Dev` is not a git repository, so `D:\Dev\CLAUDE.md` is untracked by anything.** Its own
> version-history section says that if the file is untracked there is no authority over what it
> used to contain, *"and that is itself worth reporting."* **Reporting it: the v1.1 → v1.2 edit
> has no diff, no history and no undo.** The version row is the only record that it changed.

---

## 6. The suite: `8 failed, 277 passed`

Final run on `main` at `6b7dc1d`, in `D:\Dev\momentum`, `10.05s`.

**This figure moved three times during the task**, because two other sessions were committing
throughout:

| `HEAD` | Result |
|---|---|
| `49fb4d7`, tree dirty with `030` half-applied | `15 failed, 267 passed` |
| `59fc2ab`, `030` committed | `13 failed, 269 passed` |
| **`6b7dc1d`, `030`'s follow-up committed** | **`8 failed, 277 passed`** |

The other session resolved five of its own eight invariant failures between the second and
third runs. **The remaining 8 are accounted for:**

| Cause | Count |
|---|---|
| `030`'s declared finding, still open | 3 — `test_no_bare_six_of_nine`, `test_no_bare_six_of_nine_anywhere_in_specs`, `test_regime_snapshot_could_not_do` |
| Pre-existing, nobody's current task | 2 — `test_handoff_state_declared` (inbox `021`–`027` carry no `**Status**` header), `test_uat_has_a_file` |
| Christoph's `014` retirement, unstaged | 2 — `test_observations_ledger` ×2 |
| Open worktrees | 1 — `test_pytest_collection` |

**None was caused by 017, and none is 017's to fix.**

### The push went out against a red suite, and that was a decision

017's exit test asks for green before the push. **It was not green, and will not be soon** —
the 8 above belong to three other pieces of work. **Christoph authorised the push explicitly
with the suite in this state.** Recorded here because a future reader will otherwise assume the
exit test was met.

**The asymmetry that made it the right call:** a push publishes commits, not test results. The
red tests are already committed and already reproduce for anyone who clones. Not pushing would
not have made them greener — it would only have kept three days of unrepeatable work on one
disk.

---

## 7. What was wrong on contact

**Three things.**

1. **The tape is 3.9 GB, not the ~2 GB 017 quotes** — and `CLAUDE.md` v1.5 said "roughly 2 GB"
   too. `019`'s 2026-08-12 capture roughly doubled it. The exclusion is unaffected; the rule is
   a directory, not a size. **The figure is stale in two places.**
2. **Part 4 cannot be done as written.** It instructs Claude Code to write a `christoph/open/`
   EXTERNAL item. **`CLAUDE.md` and `docs/specs/CHRISTOPH-TASKS.md` both reserve that folder** —
   *"the design session authors the task file. Christoph saves it to `christoph/open/`."* 017
   predates `CLAUDE.md` v1.5 by a day, which is likely how it arose. **Drafted in §8 for chat
   to author instead.**
3. **Part 3's "v1.1 text" is in a different file than implied.** It is in `D:\Dev\CLAUDE.md`,
   not this tree's. Both were edited; see §5.

**And one thing 017 did not contemplate at all:** that the tree would be modified by other
sessions *while the task ran*. It assumes a still tree. See §10.

---

## 8. Part 4 — the tape is still on one disk, and this task did not fix that

**Drafted for chat to author as a `christoph/open/` EXTERNAL item.** Claude Code must not write
there.

> `records/tape/` holds **3.9 GB** across two capture sessions, including the 2026-08-11 QQQ
> session. It is gitignored, so **the push completed under 017 did not protect any of it.**
> That session **cannot be re-recorded** — it is a specific morning and it is gone — and it is
> the declared basis for Layer 0 row 14, which under the threshold convention means deleting it
> would leave a fitted threshold with no source string. It existed on exactly one disk before
> 017 and **it exists on exactly one disk after it.** Where a second copy lives is undecided,
> and 017 deliberately did not cover it: **no LFS configuration, no sync script, nothing added
> to git.** The decision is Christoph's.

---

## 9. The UAT this note declares, and the red test that follows

017's UAT is Christoph's: **open the new repository in a browser, confirm the code is there,
the tape is not, and the archive at `momentum` is unchanged.**

**No file in `christoph/` declares task `017`, so `test_uat_has_a_file` is now red on this
note.** That is the test doing exactly what it was built for — it exists because `S009`'s UAT
lived only as a line inside a done-note nobody reopened.

**It would have been trivial to make it green by writing `UAT | ... | None`.** That would have
been a lie, and gaming a test whose entire purpose is to stop this class of lie is worse than
the red. **Chat authors the item; Christoph saves it; the test goes green on its own.**

---

## 10. Two sessions, one tree — the finding this task did not go looking for

**The working tree changed under this session four times**, none of it this session's doing:

- **16:15** — `docs/specs/REGIME-PROMPT.md` and `tests/test_regime_prompt_invariants.py`
  appeared modified, mid-check.
- **16:20** — those landed as `59fc2ab`, and `export-handoff.ps1` ran from that session.
- **later** — `6b7dc1d` landed on `main`, moving it past the commit this branch was based on.
- throughout — a **locked worktree** at `.claude/worktrees/029-entry-point` held task `029`.

**Consequences that are worth writing down:**

1. **A first push must not run concurrently with other sessions.** Had this one pushed on its
   first clean-looking read, it would have published another session's half-applied spec edit.
   017's own reasoning — *"the first commit reachable from a remote is the one people trust
   most"* — is exactly about this, and 017 has no mechanism to enforce it.
2. **A suite count is not a stable fact while another session is committing.** Three different
   figures, all correct when taken. **Quote the `HEAD` with the count or the count means
   nothing** — the defect `028` was already fighting.
3. **A concurrent worktree turns `test_pytest_collection` red for everyone.** A worktree of this
   repo lives *inside* the repo, so its `tests/`, `core/tests/` and `live/tests/` read as
   undeclared test directories. The guard is right to refuse them; the redness is not about the
   code and will recur every time two sessions run.

`handoff/inbox/031-for-code-two-sessions-one-tree.md` appeared on `main` during this task and
appears to address exactly this. **This note is not that task** and does not pre-empt it.

---

## Exit tests

| Test | Who | Result |
|---|---|---|
| **Green** | Claude Code | **NOT MET, and pushed anyway on Christoph's explicit authorisation.** `8 failed, 277 passed` at `6b7dc1d`; every failure attributed in §6, none caused by 017. **`git ls-remote` matches local `HEAD` — both hashes in §1.** |
| **Refusal A** | Claude Code | **PASSED.** `check-ignore -v` quoted verbatim in §2; rule named as `/records/` at `.gitignore:42`, anchored; `git ls-files records/` returns 0. |
| **Refusal B** | Claude Code | **PASSED.** `momentum-harness` remote quoted before and after in §4, byte-identical. Never written to. |
| **UAT** | Christoph | **Owed, and not yet a file.** Open the repository in a browser; confirm the code is there, the tape is not, and the archive at `momentum` is unchanged. **Chat must author it — see §9.** |

## Ledger

Rows for `docs/observations/OBSERVATIONS.md`, to be added at review:

- **A concurrent worktree turns `test_pytest_collection` red for every session** (§10).
  Observed: `.claude/worktrees/029-entry-point` reported as three undeclared test directories.
  Would settle it: decide whether `.claude/worktrees/` is excluded from the guard's walk, or
  whether a red collection test is the accepted cost of concurrent sessions.
- **`records/tape/` is 3.9 GB, against ~2 GB quoted in `CLAUDE.md` and in `017`** (§7). Would
  settle it: a size check in `verify.ps1`, so the figure is observed rather than remembered.
- **The credential scan has never covered git history, and a first push has now happened**
  (§3). Would settle it: run a history scanner once and record the result, or record explicitly
  that the risk is accepted.

## Housekeeping

Written on branch **`worktree-017-remote`**, which is **already on the remote** at `f27b7e2`.
The branch is based on `59fc2ab`; **`main` has since advanced to `6b7dc1d`, so it is no longer
a fast-forward.** It was deliberately **not rebased** — rebasing would orphan the commit already
pushed and require a force-push.

**No file overlap with anything on `main`** — this branch touches only `CLAUDE.md` and this
note; `6b7dc1d` touched neither. It merges cleanly:

```powershell
cd D:\Dev\momentum
git merge --no-ff worktree-017-remote
git push
.\export-handoff.ps1
```

**`D:\Dev\CLAUDE.md` is outside every repository and is already edited on disk** — it is not
part of this branch and no commit carries it.
