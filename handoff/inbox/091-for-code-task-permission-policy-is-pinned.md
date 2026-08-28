---
task: 091
class: admin
unblocks: NOTHING
depends: none
touches: one new test and one committed expectation file, both under tests/
---

# 091 — seven rules left the permission policy and the suite said nothing

**If `handoff/inbox/091-for-code-task-permission-policy-is-pinned.md` exists in your tree and `handoff/done/091-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

**`unblocks: NOTHING`, stated honestly.** No product task waits on this. It is a security control with no signal, and the judgment on whether it was worth a session is Christoph's.

---

## 0. What happened, and one correction to `B-147` before you start

**On 2026-08-24 Christoph removed seven entries from `permissions.ask` in `.claude/settings.json`** — the Bash and PowerShell forms of `git worktree add`, `git checkout` and `git branch`, plus `Bash(find:*)`. **The suite stayed green.**

**`B-147` states that nothing tests the shape of the `ask` list. That is too broad, and the design session wrote it from one session's report without reading the second test file.** Read both before you start:

- **`tests/test_permission_policy.py`** — asserts the `deny` list contains an entry covering `.claude/settings.json` itself, plus the malformed-policy refusals. Says nothing about `ask`.
- **`tests/test_permission_policy_is_shell_symmetric.py`** — **does** assert `ask` and `deny`, for `git` commands only: every git restriction must bind under both shell tools, and a named required set must be present in `deny`.

**So the real gap is narrower and worth stating exactly: `git` entries are covered; nothing else is.** Christoph's seven removals passed because he removed both shell forms of each — symmetrically. **Had he removed only the three Bash forms, `test_every_git_restriction_binds_under_both_shells` would have gone red.** The guard worked. What it does not cover is every non-git entry: `Bash(find:*)`, `Bash(rm:*)`, `Bash(rmdir:*)`, `Bash(mv:*)`, the `Remove-Item`/`Move-Item` family, the `Set-Content`/`Add-Content`/`Out-File` family, the schtasks pair, the env and registry writes, and both `.gitignore` entries.

**`B-147`'s resolution field also says the expectation belongs in `config/`. It does not — §3 corrects that.**

**Part 0 is: confirm the two paragraphs above by reading both test files, and say in the done-note whether they hold.** The design session read them through a bridge and has been wrong once today already about this same policy file.

---

## 1. Why this is worth pinning at all, and why `ask` counts

**`B-146` measured, on 2026-08-24, that `ask` genuinely binds under auto mode** — a `mv` was stopped by the rule `PowerShell(Move-Item:*)`, named verbatim in the prompt. **This overturns the measurement recorded in the project instructions** (*"`deny` binds; `ask` does not, under auto mode"*), which is also quoted inside `test_the_worktree_and_uncommitted_work_guards_are_present_under_both`'s own assertion message.

**Do not fix that docstring in this task.** It is a comment quoting a superseded measurement, the correction belongs in the instructions first, and rewriting a test's prose while pinning its subject is how two changes become indistinguishable in one diff. **Report it in the done-note and leave it.**

**The consequence that makes `ask` load-bearing:** `B-146` also measured that path `deny` rules bind against shell commands, so `christoph/done/`, `christoph/open/`, `records/` and the Drive landing folder are protected by `deny` alone. **But there is no path `deny` anywhere else in `D:\Dev\momentum`** — so `Bash(rm:*)`, `Bash(rmdir:*)`, `Bash(mv:*)` and the `Remove-Item` family in `ask` are the only thing standing between a session and a silent deletion inside the repo. **Those are exactly the entries nothing currently tests.**

---

## 2. Part A — generate the expectation, never invent it

**The expectation is a snapshot of the file as it stands the moment you write it. It is not a proposal.**

**Do not add, remove or reorder anything on the way in.** The seven removals were Christoph's ruling; a test encoding a set the design session preferred would go red on a correct decision, and somebody would then "fix" the policy to match the test. **That inversion is the failure mode this task exists to avoid, and it is worse than the gap it closes.**

- **Generate it by reading `.claude/settings.json` and writing out what is there** — `allow`, `ask` and `deny`, all three arrays.
- **Sort within each array** so a reordering is not a diff. **Membership is the fact; order is not.**
- **The done-note states which state was pinned**, including that it is the post-removal state and names the seven entries that are absent by decision.

---

## 3. Part B — where it lives, and it is not `config/`

**`config/` is settings — every setting, one file per domain, one loader.** An expectation is not a setting: **a setting is something you may change to change behaviour, and this file must be changed only to record a change somebody else already made deliberately.** Putting it in `config/` invites exactly the edit that empties it of meaning.

**It lives beside its test, under `tests/`.** Name it so nobody mistakes it for a policy: something that reads as a recorded expectation, not as a second copy of the policy. **Say in the file's own header that it is generated from `.claude/settings.json`, that editing it changes nothing about what a session may do, and that the only correct reason to edit it is to accept a change already made to the real file.**

**`.claude/settings.local.json` is gitignored** (`.gitignore:61`, `.claude/**/*.json`) and is per-machine. **Do not pin it — and say so in the test's docstring rather than leaving a reader to assume it is covered.** It currently carries twenty-plus `allow` entries that widen this session's permissions and that no test, on any machine, can see. **That is a real second gap; name it in the done-note and do not fix it here.**

---

## 4. What the test must assert

**Name the diff. Never merely that something changed.**

A guard that says *the permission policy has changed* is one a reader accepts blindly, because it gives them nothing to judge. **The failure message must name which entries were added and which were removed, in which array, so the reader can accept or reject each one on sight.**

**Assert membership, not text.** `B-029` is what pinning exact strings produces — a test that goes red when wording changes while the control still holds. Here the strings *are* the membership, so equality is right — **but compare as sorted sets and say in the message which side each difference is on.**

**Do not assert anything about what the entries mean.** No "these must be in `ask`", no required set, no shape rules. **`test_permission_policy_is_shell_symmetric.py` already owns the meaning of the git entries, and duplicating it here is how two guards come to disagree.** This one owns one fact only: *did the file change without anyone saying so.*

---

## 5. Exit tests

**Green.**

- **Part 0's confirmation in the done-note** — whether §0's reading of the two existing test files holds.
- **The expectation file is generated from the live policy, sorted, and committed**, with the seven absent entries named in the done-note.
- **The suite passes against the current file, unmodified.**

**Refusal.**

- **Remove one `ask` entry in a scratch copy and the test goes red naming that entry** — **demonstrated red before green**, and the message must contain the entry's own text.
- **Add one entry, same.**
- **Reorder without changing membership and the test stays green.** Order is not the fact.
- **A malformed policy file is a named refusal, not a crash** — reuse `test_permission_policy.py`'s existing `PolicyError` rather than inventing a second vocabulary for the same failure.

**UAT (Christoph).**

- **Remove any one line from `ask` in the real file, run the suite, read the message, put the line back.** The test must name the line he removed. **If it says only that the policy changed, it has failed this task's whole point.**

---

## 6. Not in this task

- **`.claude/settings.json` itself.** Denied to every Claude, and Christoph's alone. **Do not edit it, do not propose a membership for it, and do not "restore" anything that looks missing.**
- **The superseded measurement quoted in `test_the_worktree_and_uncommitted_work_guards_are_present_under_both`'s assertion message.** §1 — report, do not fix.
- **`.claude/settings.local.json`.** §3 — name the gap, leave it.
- **`C:\Users\chbic\.claude\` — the user-level settings and the `hooks/` directory.** Denied, outside the repo, and a separate live problem of Christoph's. **Do not read them and do not reason about them.**
- **The twelve pre-existing failures.** `086` triaged them and this task adds nothing to that set.

---

## 7. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**The done-note carries Part 0's confirmation, which state was pinned and when, the seven entries absent by Christoph's decision, the `settings.local.json` gap, and the stale measurement quoted in the existing test's own message.**

---

**This note needs to be pasted to chat.**
