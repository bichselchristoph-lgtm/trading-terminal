---
id: 024
title: A subagent roster whose restrictions are tool lists, and the .claude/ exception it needed
type: protocol
owner: claude-code
---

**Status** RUNNING

# 024 — done-note

**Four agents exist in `.claude/agents/`, committed, each declaring `tools:` explicitly.**
`tests/test_subagent_roster.py` goes red when `Edit` is added to `reviewer` — demonstrated
below before the green was accepted.

**Two things this task had to do that the task file did not anticipate**, both recorded here
because both touch a rule older than `024`:

1. **`.claude/` was gitignored outright**, by an M001 §6 rule that exists because the
   predecessor's `.claude/settings.local.json` held a live Databento key. The roster has to be
   committed or it does not exist. **The exception is four markdown files wide** and is fenced
   by its own test, seen red against a planted `.claude/agents/settings.local.json`.
2. **`test_no_secrets.py::test_claude_config_is_not_tracked` went red the moment the roster
   was committed** — correctly. It is narrowed, not deleted.

**Built in a worktree**, `.claude/worktrees/024-subagent-roster`, on branch
`worktree-024-subagent-roster`. **The shared checkout was not touched.** See §6.

---

## 1 — The roster

| agent | `tools:` | what the list actually stops |
|---|---|---|
| `architect` | `Read, Grep, Glob, WebFetch` | **Everything.** No `Write`, no `Edit`, **no `Bash` at all** — the only form of *"no mutating Bash"* a tool list can express |
| `implementer` | `Read, Write, Edit, Bash, Grep, Glob` | Nothing — it is the writer. That is the point: **one writer makes *who changed this* answerable without a transcript** |
| `reviewer` | `Read, Grep, Glob, Bash` | `Write` and `Edit`. **Not `Bash`** — see §3 |
| `test-author` | `Read, Write, Edit, Bash, Grep, Glob` | Nothing. Its scope restriction is a convention — see §3 |

Each definition carries a **"what you may not do"** table with a *stopped by* column naming
either the missing tool or the word **convention**. No prohibition sits next to an enforced
one borrowing its authority.

**Four, and I did not add a fifth.** `024` says every agent is a context boundary and a place
for information to be lost in translation; `test_the_four_agents_exist` pins the set, so
adding one is a decision that edits a test rather than a directory.

---

## 2 — The test, red then green

**Red, with `Edit` added to `reviewer`** — the edit somebody will actually make:

```
E       AssertionError: reviewer declares ['Edit'], and its whole value is that it cannot.
E
E         A reviewer that fixes stops reporting, and its fixes are unreviewed by construction.
E         An architect that can write will write, and then the plan is post-hoc narration of
E         code that already exists.
E
E         If a fix is needed, it goes to the implementer. Do not add the tool.
E       assert not ['Edit']

FAILED tests/test_subagent_roster.py::test_the_read_only_agents_have_no_write_tool[reviewer]
FAILED tests/test_subagent_roster.py::test_the_implementer_is_the_only_agent_that_can_write
3 failed, 13 passed
```

**Two tests fired, not one**, and that is worth having: the per-agent restriction and the
*only one writer* invariant are different claims and a change could break either alone. The
third red was `test_the_roster_is_tracked`, which was correct at that moment — the definitions
were not yet staged.

**Green, after restoring `tools: Read, Grep, Glob, Bash`:**

```
tests/test_subagent_roster.py            16 passed
tests/test_claude_dir_stays_ignored.py   19 passed
tests/test_no_secrets.py                 22 passed
tests/test_adoption_log_complete.py       6 passed
63 passed in 2.64s
```

---

## 3 — What could **not** be expressed as a missing tool

**Four prohibitions are conventions. Every one is labelled as such in its own definition**,
and `test_every_unenforceable_prohibition_is_labelled` asserts the labelling exists rather
than trusting it.

| # | prohibition | why the tool list cannot hold it |
|---|---|---|
| 1 | **the reviewer must not receive the implementer's reasoning** | Nothing can stop a caller pasting a justification into a prompt. `024` names this one itself |
| 2 | **the reviewer must not write via `Bash`** | **It has `Bash`.** `echo > file` is one keystroke away |
| 3 | **the test-author must write only under test directories** | It holds `Write`/`Edit` — it must, to create test files — and a tool list cannot say *"here but not there"* |
| 4 | **the implementer must not push, or write into `christoph/`** | It has `Bash`, so `git push` is available to it |

**Number 2 is the one that matters and it is a real hole in this roster.** The reviewer's
whole value is that it cannot fix what it finds, and the tool list makes that look airtight
while `Bash` quietly makes it false.

**I did not close it by removing `Bash`.** A reviewer that cannot run the suite is guessing —
reproducing a defect is most of the evidence that it is one. **The trade is stated in
`reviewer.md` under a heading that names it as a hole**, and
`test_bash_is_write_capable_and_the_roster_says_so` **asserts that the documentation of the
weakness is present** — it fails if someone removes the honesty rather than the weakness.

**What would actually close it: a `PreToolUse` hook refusing mutating shell commands for that
agent, and a path-scoped write guard for `test-author`. Neither exists.** Recorded as
**OBS-038**.

---

## 4 — The `.gitignore` exception, and how narrow it is

`.claude/` was ignored as a **directory**, which made the exception impossible before it made
it dangerous: **git does not descend into an ignored directory**, so no negation inside one
can rescue anything. The rule is now four lines plus a guard:

```
.claude/*
!.claude/agents/
.claude/agents/*
!.claude/agents/*.md
.claude/**/*.json
```

**The last line is last deliberately.** Later rules win in git, so it holds even if someone
widens the negation above it — and widening is the obvious "improvement" (`!.claude/agents/**`)
that a future reader reaches for.

### Seen red, twice, in a throwaway worktree

**Demo A — negation widened to `!.claude/agents/*` and the belt-and-braces line deleted**,
with a real `.claude/agents/settings.local.json` planted in the tree:

```
E       AssertionError: .claude/agents/settings.local.json is NOT ignored.
E
E         The only permitted exception under .claude/ is .claude/agents/*.md. This path is
E         outside it, so the negation in .gitignore is wider than it is meant to be — and
E         the file it admits is the shape that held a live Databento key in the
E         predecessor tree.
E
E         Narrow the negation. Do not add an exception for this path.

8 failed, 11 passed
```

**Demo B — negation widened, belt-and-braces KEPT.** This is the one that proves the layering
rather than the rule:

```
$ git check-ignore -v --no-index -- .claude/agents/settings.local.json
.gitignore:44:.claude/**/*.json    .claude/agents/settings.local.json      <- still blocked

$ git check-ignore -v --no-index -- .claude/agents/notes.txt
.gitignore:43:!.claude/agents/*    .claude/agents/notes.txt                <- now trackable

FAILED ...[.claude/agents/notes.txt]
FAILED ...[.claude/agents/roster.yaml]
FAILED ...[.claude/agents/nested/roster.md]
```

**The JSON stayed blocked by the last line while three other shapes leaked**, and the test
caught the leak. That is the belt-and-braces doing exactly what its comment claims.

**Both demonstrations ran in `git worktree add --detach`, never in the shared tree** —
OBS-036, written four hours earlier under `032`, applied to its own author.

The planted file was removed; `git status` is clean of it.

---

## 5 — The credential scan now covers a path that is **committed**

**`.claude/agents/` is the first `.claude/` location in this tree's history whose contents get
pushed.** A key pasted into an agent definition would leave the machine.

**The walk already reached it** — `.claude` is deliberately absent from `SKIP_DIRS`, `.md` is
in `TEXT_SUFFIXES` — so nothing had to be widened. **What was missing was teeth**, and this
file has been caught by that exact gap before: `test_dot_claude_is_not_skipped` exists because
the module's claim to scan `.claude/` was **vacuous**, the tree having had no `.claude/` at
all. Two tests added:

- **`test_the_walk_reaches_a_planted_key_in_the_roster`** — plants a synthetic key in a temp
  `.claude/agents/reviewer.md`, asserts the walk reaches the file *and* the pattern matches it.
- **`test_the_real_roster_is_actually_scanned`** — the non-vacuous half: the four **real**
  definitions appear in what the scan actually read. Skips if the roster is absent, so a
  pre-`024` checkout does not fail for a directory that does not exist.

**`test_claude_config_is_not_tracked` is narrowed, not deleted**, and renamed
`test_no_claude_config_file_is_tracked`. It asserted `.claude/` held *no* tracked file, which
was right until this task and went red on four markdown files that hold no credential and
never could. **What M001 §6 protects is the config surface** — JSON under `.claude/` is where
a key sits. It now asserts no `.json`/`.yaml`/`.env` is tracked there.

**Its docstring states why it is not a duplicate** of
`test_claude_dir_stays_ignored.py::test_only_the_roster_is_tracked_under_claude`: that one
owns the **scope** rule (*only `agents/*.md`*), this one owns the **credential** rule (*no
config file*), and it would still fire if the scope rule were later relaxed to admit some new
non-JSON config format. Two rules, two files, said out loud so neither is mistaken for a
duplicate and quietly removed.

---

## 6 — Built in a worktree, and what that changed about the numbers

**`024` is the first task under the new standing rule: work in a worktree, not the shared
checkout.** Branch `worktree-024-subagent-roster`, based on `4597841`.

**The suite reports differently from a worktree and none of it is about `024`:**

| | main checkout | this worktree |
|---|---|---|
| result | `292 passed, 8 failed` | **`326 passed, 11 failed`** |

`+37` passing is exactly this task: 19 + 16 + 2. The failure sets differ by five:

**Green here, red in main:** `test_pytest_collection::test_every_directory_holding_tests_is_declared`
— red in main only because the `029` worktree is a full checkout nested inside it. **OBS-034.**

**Red here, green in main — four, all worktree artifacts:**

- `test_evidence_carry_intact` (×2) — **OBS-033**, the CRLF/LF hash anomaly that is green only
  in the one working copy predating the `.gitattributes` pin, plus gitignored evidence that is
  simply absent from a fresh checkout.
- `test_spec_pointers::test_claude_md_pointers_resolve` — `CLAUDE.md` names paths (`records/`)
  that are gitignored and therefore absent here.
- `test_sync_from_drive::test_the_destination_paths_are_inside_the_repo` — **a real finding,
  and it belongs to `025`.** `config/sync.yaml` pins its destination to
  `D:\Dev\momentum\docs\regime-snapshots`, an absolute path in the main checkout, so it is
  genuinely outside any worktree. **Recorded as OBS-039 and deliberately not touched** —
  changing a `025` input from inside `024` is how a task acquires work nobody scoped.

**The seven shared failures are the same seven as `032`'s baseline.** None introduced, none
fixed.

---

## 7 — What I could not do

**Not empty.**

1. **The reviewer's `Bash` write path is open**, and the `test-author`'s scope is a convention.
   §3, OBS-038. Closing either needs a `PreToolUse` hook that does not exist, and building one
   is not `024`.
2. **Nothing verifies the roster is ever USED.** Four definitions and a frontmatter test prove
   the restrictions hold *if* an agent is invoked; nothing makes anyone invoke one, and
   `024`'s *"anything touching a stop level, a limit, or a size goes through a reviewer"* is a
   process rule with no enforcement point in this repo. **That is the same shape as the three
   unreachable features `032` found** — a mechanism that exists and nothing reaches. Not
   solvable from inside the tree, and I am flagging it rather than pretending the frontmatter
   test covers it.
3. **`export-handoff.ps1` was NOT run**, and this is a deliberate departure from
   `CLAUDE.md`'s *run it at the end of every task*. Exporting from a worktree would put a
   branch's `handoff/` into the Drive mirror that the design session reads as **main's** —
   a superseded-copy-walks-back-in failure of exactly the kind the one-way export exists to
   prevent. **It should be run after this branch is merged**, from the main checkout.
4. **I did not merge to main.** The standing instruction is to stay out of the shared
   checkout, and merging is a shared-checkout operation. **This branch needs merging by
   Christoph**, the same way `017` and `029` did.
5. **The `.claude/` exception widens M001 §6, and no test can tell you it was worth it.**
   The narrowness is asserted; the *decision* is not, and cannot be. It is recorded here and
   in the `.gitignore` comment so a future reader meets the reasoning before the rule.

---

## 8 — Files

| file | change |
|---|---|
| `.claude/agents/architect.md` | new — `Read, Grep, Glob, WebFetch` |
| `.claude/agents/implementer.md` | new — the only writer |
| `.claude/agents/reviewer.md` | new — no `Write`/`Edit`; names its own `Bash` hole |
| `.claude/agents/test-author.md` | new — spec-not-implementation, scope is a convention |
| `.gitignore` | `.claude/` → four-line negation + `.claude/**/*.json` guard |
| `tests/test_subagent_roster.py` | new — 16 tests |
| `tests/test_claude_dir_stays_ignored.py` | new — 19 tests |
| `tests/test_no_secrets.py` | narrowed one test, added two |
| `tests/test_adoption_log_complete.py` | six allowlist entries, count now 40 |
| `docs/observations/OBSERVATIONS.md` | OBS-038, OBS-039 |

---

## Exit

| kind | item | destination |
|---|---|---|
| MERGE | branch `worktree-024-subagent-roster` into `main` | **Christoph** — §7 item 4 |
| EXPORT | `export-handoff.ps1` after the merge, from the main checkout | **owed** — §7 item 3 |
| UAT | none | **None** |

`verify.ps1` was run in this worktree — see `verify-output.txt` on this branch, read directly.
**Not quoted here, per HANDOFF-PROTOCOL v1.2.** Note that its section 1 will show the eleven
failures §6 explains, and its section 5 will show the Drive mirror at main's `HEAD` rather
than this branch's, **because the export was deliberately not run.**

**This note needs to be pasted to chat.**
