---
id: 046
title: A committed permission policy — and the measurement of whether it binds
type: task
class: admin
owner: claude-code
commits: 58b0926, f35bd3a, e2e3a93
---

**Status** RUNNING

# 046 — done. `ask` does not bind, and a `Bash`-only `deny` is one env var from no `deny` at all.

**Three commits, not two.** `58b0926` built the policy, `f35bd3a` measured it and moved the
irreversible set out of `ask`, and **`e2e3a93` — "046 part 2" — found that every one of those
rules was spelled `Bash(...)` and stops applying the moment the session switches to the
PowerShell tool.** The task file names two commits because it was written against what was known
at the time; the third is the same task and is reported here.

**The task file for this work was written AFTER the work and after the push.** That is stated in
the file itself and repeated here so it is not discovered later: `046` is a record, not an
authorisation.

---

## 1 — the three probes, as observed

**Run against the live session immediately after `58b0926` landed. These are observations, not
expectations.**

| class | probe | observed |
|---|---|---|
| `deny` on a path | `Read` a `.env`-shaped path | **BLOCKED** |
| `deny` on a shell | `git clean -n -d` | **BLOCKED** |
| `ask` on a shell | `git push --dry-run origin main` | **RAN UNPROMPTED** |

**The third one is the finding.** `git push --dry-run origin main` matches `Bash(git push:*)` in
`ask` and does **not** match the exact-string `allow` entry `Bash(git push origin main)`. It ran
with no prompt.

**The settings file was loaded** — two `deny` rules fired out of it in the same minute, so this is
not "the file was ignored". **`ask` is the class that failed to bind**, and the cause is auto
mode: shell commands route through the classifier, which approves what `ask` would have prompted
for.

**Why the probe had to be chosen carefully, and this is the part worth carrying forward.** The
obvious probe is plain `git push origin main`. **It proves nothing** — pushes were already
unprompted before `.claude/settings.json` existed, so a successful push is consistent with the
policy binding, not binding, and not being loaded at all. **A probe that every hypothesis
predicts is not a measurement.** `--dry-run` was chosen because it lands in `ask` and misses the
exact `allow`, so the three hypotheses give three different answers.

---

## 2 — what moved class, and why that class

**Seven entries moved from `ask` to `deny` in `f35bd3a`:**

```
git worktree remove      git reset --hard      git restore
git worktree prune       git checkout --       git stash drop
                                               git stash clear
```

**Every one of them is a route to another session's worktree or to uncommitted work** — which is
to say, the entire class the policy was written for **sat in `ask`, the one class measured not to
bind.** The policy as committed at `58b0926` looked complete and protected nothing that mattered.

**The general forms stay in `ask` deliberately.** Plain `git reset` unstages and plain
`git checkout <branch>` switches; neither destroys, and moving them to `deny` would block ordinary
work to no benefit.

**`autoMode.classifyAllShell: true` was set in the same commit.** It suspends `Bash` allow rules
while auto mode is active, so every shell command is classified rather than silently allowed.
**The cost is stated rather than buried: the `allow` list stops saving prompts in auto mode**,
which is a partial trade against the reason it was written.

**Verified after the change:** `git worktree prune --dry-run` **blocked**; `git worktree list`
still **allowed**. **And the rule then caught its own author** — a restore command containing
`git checkout --`, typed later in the same task, was refused.

Rule counts across the three commits, from the file:

| | `allow` | `ask` | `deny` |
|---|---|---|---|
| `58b0926` | 43 | 22 | 26 |
| `f35bd3a` | 43 | 19 | **33** |
| `e2e3a93` | **75** | **51** | **44** |

---

## 3 — every prefix gap found, and what covers it instead

**A permission rule is a prefix match, and prefix matching leaves gaps. These are not papered
over and they are not fixed by a rule, because a rule cannot reach them:**

| what steps around it | why the prefix misses |
|---|---|
| `git reset HEAD~1 --hard` | the flag is **reordered past the prefix** — `git reset --hard:*` never matches |
| `git checkout <file>` | discards the file **without the `--`**, so `git checkout --:*` never matches |

**Both are covered by `autoMode.classifyAllShell`, not by a rule**, and that is the honest
statement of the coverage. The classifier reads the command; the prefix reads a string.

**The consequence, stated because it is the thing a reader would otherwise get wrong: outside
auto mode, those two spellings are not covered at all.** The rule list is not the whole
protection and must not be read as if it were.

---

## 4 — part 2: a `Bash`-only `deny` is one environment variable from no `deny` at all

**Found by being handed the env var, not by reading the policy:**

```powershell
[Environment]::SetEnvironmentVariable('CLAUDE_CODE_USE_POWERSHELL_TOOL','1','User')
```

That switches Claude Code to the PowerShell tool. **All eleven `deny` rules committed in
`58b0926` and `f35bd3a` read `Bash(git ...)`, and there were zero PowerShell denies.** So
`PowerShell(git worktree remove ...)` matched nothing, and every protection built and verified
two commits earlier **stopped applying.**

**Not loosened. ABSENT.** And the policy file would still read exactly as it did when it was
reviewed — **which is what makes this the tree's recurring shape rather than an ordinary bug.**

**Mirrored:** 11 `deny` and 8 `ask` rules gained PowerShell twins. `allow` gained the read-only
git set, PowerShell's own read-only verbs, and the `&` call-operator spellings for the three
`.ps1` scripts.

**PowerShell aliases were a live hole even before this.** `rm`, `ri`, `del`, `erase`, `rd`,
`rmdir` all resolve to `Remove-Item`; `mv`, `move`, `mi` to `Move-Item`. **Only the canonical
names were in `ask`.** All aliases added, plus `Set-Content`, `Add-Content`, `Clear-Content` and
`Out-File` — those write anywhere, and the `Write()`/`Edit()` path denies do not reach a shell.

**Structural, not remembered** (standing rule 4).
`tests/test_permission_policy_is_shell_symmetric.py` asserts every git rule in `ask` and `deny`
has a twin under both tools, **and names the eight worktree/uncommitted-work denies explicitly so
it cannot pass vacuously against a policy with no git rules at all** — `OBS-037`'s shape.
**Seen RED against the exact state of `f35bd3a`: 8 `ask` rules and 11 `deny` rules reported
Bash-only.**

**Scoped to `git` deliberately.** The two shells have different vocabularies — `find` and `rm`
are Bash's, `Remove-Item` and `Set-Content` are PowerShell's — and demanding a twin for each
would force meaningless entries. **`git` is the one command spelled identically under both, so an
asymmetry there is always an oversight.** `allow` asymmetry is permitted and stated: it fails
safe, costing a prompt rather than the work.

**The env var was not set by `e2e3a93`.** It is set afterwards, so there is no window in which the
policy is live and the protections are not.

---

## 5 — A RED WAS COMMITTED AT `58b0926`, AND THE FULL SUITE WOULD HAVE CAUGHT IT

**Reported at the top of its own section because it is the most transferable thing in this task.**

`58b0926` was committed on a **targeted test run** — `tests/test_claude_dir_stays_ignored.py`,
the file the work had just changed. **The full suite then found a second guard, in a different
file, that the same commit broke:**

```
tests/test_no_secrets.py::test_no_claude_config_file_is_tracked
```

That test asserts **no `.json`, `.yaml`, `.yml` or `.env` file is tracked under `.claude/`**.
`58b0926` added `.claude/settings.json` to the index. **The commit was red at the instant it
landed.**

**Confirmed here, not taken on the commit message's word:**

```
$ git ls-files -- .claude
.claude/agents/architect.md
.claude/agents/implementer.md
.claude/agents/reviewer.md
.claude/agents/test-author.md
.claude/settings.json          <- added by 58b0926

$ git show 58b0926:tests/test_no_secrets.py   # the assertion as it stood in that commit
configs = [p for p in tracked if p.lower().endswith((".json", ".yaml", ".yml", ".env"))]
assert not configs
```

**Why the targeted run could not see it.** The two tests are **deliberately not the same
assertion**, and `test_no_claude_config_file_is_tracked`'s own docstring says so: one owns the
**scope** rule (*only `agents/*.md` may be tracked*), the other owns the **credential** rule
(*no config file is tracked*). Two files, two rules, written apart on purpose so that relaxing one
cannot silently relax the other. **That separation is exactly what made a single-file run
blind.** The design that protects the tree from a careless edit is the design that punishes a
narrow test run.

**Fixed in `f35bd3a`**, narrowed the same way as its sibling: one exact filename,
case-insensitive, **restated rather than imported**, so relaxing the scope rule cannot relax the
credential rule with it. `test_the_config_rule_still_catches_the_file_it_exists_for` is new and
was **seen red** against a `startswith(".claude/settings")` exemption — which readmits
`settings.local.json`, the file that held the predecessor's live Databento key.

**The rule this yields, and it is not "run the full suite more often" — it is narrower and
therefore usable:** *when a change makes a previously-untracked file tracked, or previously-
ignored path visible, the targeted test is the wrong instrument by construction.* Tracking is a
repo-wide property and every guard that reads `git ls-files` is a potential subscriber. **There is
no way to know which ones from the file you are editing.**

---

## 6 — what this task cannot claim under rule 16

**It names no product task, and none was invented.**

Guardrail 2 of `CLAUDE.md` v1.7 requires a self-authored `class: admin` task to name the product
task it unblocks, and forbids admin unblocking admin. **`046` unblocks nothing.**

The closest true statements are all *protection*, not unblocking:

- the `deny` on `git clean` is the only thing between a session and `records/tape/` — **2 GB of
  2026-08-11 QQQ capture that cannot be re-recorded**, cited by Layer 0 row 14 as its basis;
- the worktree and uncommitted-work denies protect what a concurrent session is holding.

**Stretching "protects" into "unblocks" is precisely the move rule 16 exists to stop.** Had this
task been authored before the work, under `045` Part 4's gate, **guardrail 2 would have refused
it.** The design session may reject `046` on that ground alone and that would be the rule working.

**And the risk `045` asked to have watched is now visible:** `046` is the first self-authored
admin task, and it is admin that unblocks no product. **`NOW.md`'s ratio is where to watch
whether that becomes a pattern.**

---

## 7 — what the full suite said

**Before `046` (`512c5ac`, from `verify-output.txt` of the previous run):**

```
8 failed, 480 passed, 1 warning in 37.68s
```

**After all three commits:**

```
8 failed, 486 passed, 1 warning in 38.26s
```

**The eight named failures are identical, file for file and function for function**, before and
after:

```
tests/test_handoff_state_declared.py::test_every_task_file_declares_a_state
tests/test_observation_ids_are_unique.py::test_every_observation_id_is_allocated_once
tests/test_observations_ledger.py::test_every_retired_uat_has_a_register_row
tests/test_observations_ledger.py::test_refusal_b_a_retired_uat_with_no_destination_is_red
tests/test_regime_prompt_invariants.py::test_no_bare_six_of_nine
tests/test_regime_prompt_invariants.py::test_no_bare_six_of_nine_anywhere_in_specs
tests/test_regime_snapshot_could_not_do.py::test_the_format_still_lacks_a_key
tests/test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file
```

**No previously-passing test was made to fail. +6 passing**, which is `046`'s new coverage.

**None of the eight is `046`'s**, and none is newly red. `test_observation_ids_are_unique` is the
`OBS-044`–`OBS-047` duplication recorded as `OBS-062`, **still awaiting Christoph's ruling on
which set is renumbered** — it must not be resolved unilaterally, because both sets are cited from
files already exported.

**Reds seen before each guard was accepted:**

| guard | mutation it was seen red against |
|---|---|
| `.gitignore` scope | `!.claude/settings*.json` → 2 failed, **including `settings.local.json` readmitted** |
| `.gitignore` scope | `!.claude/agents/**` appended after the negation → 8 failed |
| `test_the_config_rule_still_catches_...` | a `startswith(".claude/settings")` exemption |
| `test_permission_policy_is_shell_symmetric` | the exact state of `f35bd3a` — 8 `ask`, 11 `deny` Bash-only |

---

## 8 — three rows added to `OBSERVATIONS.md`

**`CLAUDE.md` is explicit that a done-note naming a finding with no ledger row has not finished
reporting it.** Ids read from the ledger, not inferred — highest was `OBS-064`.

| id | what |
|---|---|
| **OBS-065** | **`ask` does not bind in auto mode; `deny` does.** Measured, three probes |
| **OBS-066** | **Prefix matching leaves reachable gaps** — `git reset HEAD~1 --hard`, `git checkout <file>` — covered by `classifyAllShell`, not by a rule |
| **OBS-067** | **A `Bash`-only policy is one environment variable from no policy**, and the file reads unchanged either way |

**Two of the three were named in the instruction for this note. `OBS-067` was not, and I added
it** — it is a durable finding about the system, it is named in this note, and the convention
requires a row for anything named here. **If the design session disagrees it exits by `DROPPED`
with a reason**, which is the correct route and costs nothing.

---

## 9 — what I could not do

1. **Measure whether `ask` binds outside auto mode.** Every probe ran in one session, in auto
   mode. **The conclusion is therefore "`ask` does not bind *here*", not "`ask` never binds"** —
   and `OBS-065` says so in those words. A session in default mode would settle it and none was
   available.
2. **Verify the PowerShell twins actually fire.** `e2e3a93`'s rules are asserted **structurally**
   — the symmetry test proves the entries exist under both tools. **It does not prove the
   PowerShell tool honours them**, which needs a session with `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`
   and the same three probes re-run. **That is the exact gap `f35bd3a` closed for Bash by
   measuring, and it is open for PowerShell.** Named here so it is not read as verified.
3. **Test the two prefix gaps.** `git reset HEAD~1 --hard` and `git checkout <file>` are reported,
   not exercised — exercising them means running a command whose entire purpose is destroying
   uncommitted work, and a `--dry-run` does not exist for either.
4. **Resolve the sync's two refusals.** `sync.ps1` exits 1 on `040` and `043` differing between
   Drive and the tree — **unchanged from `045` §5, not caused here, and not mine to resolve**: a
   handed-off file that changes breaks a reference another party holds.

---

## 10 — one thing worth carrying beyond this task

**Three times in three commits, the thing that was wrong was invisible in the artefact being
reviewed.**

- `58b0926`'s red was in a *different test file* from the one the change touched.
- `f35bd3a`'s `ask` failure was invisible in a policy file that read correctly.
- `e2e3a93`'s absent protection was invisible in a policy file that read **identically** to the
  one that had been verified.

**In all three, reading the file would have confirmed it was right.** What found each one was
running something — the suite, a probe, a shell switch. **This is the argument for measurement
stated three ways in one afternoon**, and it is the same shape as `045` §10 and `043`'s
self-reporting instrument.

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | **full suite**, not targeted. 8 failed / 486 passed; same 8 as before, +6 passing |
| **Refusal** | Claude Code | four guards, each seen red against the exact mutation — §7 |
| **Measured** | Claude Code | the three probes of §1, as observed |
| **UAT** | Christoph | **None.** `.claude/settings.json` governs a Claude Code session's own permissions; **it renders nothing and computes nothing, so there is no screen to read.** A UAT here would be Christoph re-running a probe, which is a test and is in §1 |

---

**This note needs to be pasted to chat.**
