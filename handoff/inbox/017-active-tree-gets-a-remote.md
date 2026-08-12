# 017 — the active tree gets its own remote, and a push habit

**Status** WRITTEN · **Date** 2026-08-12 · **Type** infrastructure · **Tree** `D:\Dev\momentum`

> **Run after `016`.** Part 3 edits `CLAUDE.md`, which `016` also versions. Running these out of
> order produces two version bumps racing each other.
>
> **Number not confirmed.** The design session cannot see the inbox. **If `017` is taken, say so
> and this file is re-issued under the correct number** — it is not renamed in place.

---

## Why this exists

**Nothing in the active tree has ever been pushed.** Everything since 2026-08-10 — the adoption
gate, the protocol, the TUI, 126 tests, every done-note — exists on one disk. A drive failure
today loses all of it.

The cause is a naming collision, not neglect: **the GitHub repo named `momentum` maps to the
ARCHIVED local tree**, `momentum-harness`, renamed on GitHub before the active tree existed.
Pushing `D:\Dev\momentum` at it would put the active tree on top of the archive's history.

**Decided 2026-08-12: a new repository, and the archive is not touched.** Renaming the archive
would work, but it means moving history that is deliberately frozen in order to solve a
problem a new repo solves in minutes with nothing to untangle.

---

## Part 1 — Christoph creates the repository

**This part is his and cannot be done from a session.** It is written here so the sequence is
readable, and it is repeated as a `christoph/open/` item.

He creates an **empty private repository** on GitHub — no README, no `.gitignore`, no licence,
because an initialised repo means the first push needs a merge and the first thing in the
history is a conflict resolution.

**Proposed name: `momentum-terminal`.** Not `momentum` — that name is taken by the archive and
reusing it is the collision this task exists to end.

He then supplies the clone URL. **Nothing in this task guesses it.**

---

## Part 2 — before the first push, three checks

**A first push publishes the entire history, not the current state.** Everything below runs
*before* the remote is added, and **any failure stops the task.**

**2a — nothing sensitive is tracked.** Run the full suite and confirm `test_no_secrets`
passes. **State in the done-note that it ran against tracked files** — and if its scope is
narrower than the whole history, say so plainly rather than letting a green run imply more
than it checked.

**2b — `records/` is genuinely excluded.** Confirm with `git check-ignore` on an actual tape
file, not by reading `.gitignore`. The pattern rules are unanchored and match at any depth;
`scanner_watchlists/` needed an explicit un-ignore for exactly this reason, and the record
looked committed until someone went looking.

**Report the repository size that will actually be pushed**, and confirm it does not include
the 2 GB of tape.

**2c — the working tree is clean.** `016` commits everything outstanding. If anything is still
uncommitted, **stop and report it** rather than pushing a partial state — the first commit
reachable from a remote is the one people trust most.

---

## Part 3 — add the remote and push

Add the URL Christoph supplied as `origin`, push the default branch, and set upstream tracking.

**Do not touch, rename, remove or re-point any remote on `momentum-harness`.** It is archived
and read-only, and its remote is the thing this task exists to avoid disturbing.

**Then verify the push independently of its own output.** A push that reports success is a
claim; `git ls-remote` against the new URL, compared to local `HEAD`, is a check. **Report both
hashes.**

### The habit, written into `CLAUDE.md`

> **Push at the end of every session.** A commit is local; only a push survives the disk. The
> active tree's remote is `momentum-terminal`. **`momentum` on GitHub is the ARCHIVED tree and
> is never pushed to.**

**Increment the version and add a history row.** Which version depends on what `016` landed —
**read the file, do not assume `v1.2`.**

**Remove or correct** the v1.1 text saying the remote is unsettled and the active repo must not
be pushed. It was true when written and is the opposite of true afterwards. **Do not leave both
statements in the file**; a document that says two things is worse than one that says the wrong
thing, because a reader cannot tell which is current.

---

## Part 4 — what a push does not protect

**`records/` is gitignored, so the tape does not go to GitHub.** That is correct — 2 GB of
JSONL does not belong in git — but it means **the unrepeatable 2026-08-11 QQQ session is still
on one disk after this task completes.**

**Do not solve this here.** Do not add it to git, do not add an LFS configuration, do not write
a sync script. It needs a decision about where a second copy lives, and that decision is
Christoph's.

**Write it as a `christoph/open/` EXTERNAL item** stating the exposure in one paragraph: what
the file is, why it cannot be re-recorded, and that this task deliberately did not cover it.

---

## Do not

- Do not create, rename, or modify anything on GitHub. **Christoph creates the repository.**
- Do not push, or add a remote, before Part 2's three checks pass.
- Do not touch `momentum-harness` or any of its remotes.
- Do not run `push_all.ps1`. It iterates every directory under `D:\Dev` and pushes each; four
  are archived and read-only.
- Do not modify anything in `records/`, or add any tape file to git.
- Do not modify `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` or `HANDOFF-PROTOCOL.md`.
- Do not commit anything found uncommitted at Part 2c — **report and stop.**

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full suite before the push, count reported as observed. `git ls-remote` hash matches local `HEAD`. |
| **Refusal A** | Claude Code | `git check-ignore -v` on a real file in `records/tape/`, output quoted. Confirm it is ignored **and** name the rule that ignores it. |
| **Refusal B** | Claude Code | Confirm `momentum-harness`'s remote configuration is byte-identical before and after this task. **Quote both.** |
| **UAT** | Christoph | Open the new repository in a browser. Confirm the code is there, **the tape is not**, and the archive at `momentum` is unchanged. Write the record to `christoph/open/`. |

## Done-note must state

- The repository size pushed, and confirmation the tape was excluded.
- **Both hashes** — local `HEAD` and `git ls-remote`.
- The `check-ignore` output verbatim, with the matching rule named.
- Which `CLAUDE.md` version this produced, and what the previous one was.
- **What `test_no_secrets` actually covers**, stated honestly, since a first push is when the
  gap between "tracked files scan clean" and "history contains nothing sensitive" matters most.
- Anything in this task that was wrong on contact.

## Left open, deliberately

| Item | Owner |
|---|---|
| Where a second copy of `records/tape/` lives | Christoph — Part 4 |
| Whether the archive on GitHub is eventually renamed for tidiness | Christoph — not needed, cosmetic |
| Tape compression ratio and the disk-space warning threshold | a later task, different subject |
