# 062 — tws_order has no instrument the Definition of Done can reach

**If `handoff/inbox/062-for-code-task-tws-order-test-instrument.md` exists in your tree and `handoff/done/062-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

```
Status: WRITTEN
class: admin
unblocks: S031, S032
depends: —
touches: verify.ps1, config/
```

---

## Why this exists

**PROCESS v1.6 §8 defines four Definition of Done conditions. The first is: tests green, each seen red first.**

**`verify.ps1` reports on `D:\Dev\momentum`. `tws_order` is a different repo.** So for any story whose work lands in `tws_order`, condition 1 has nothing to run and nothing to read — **the story cannot reach `REVIEWED` no matter how good the code is.**

**Two Priority-1 stories are already blocked by this.** S031 (`--risk-usd`) and S032 (the cash and margin refusal) are the spine of epic 7, and **the terminal computes no share count itself**, so both land in `tws_order` and neither can be verified.

**This task does not write either story. It builds the instrument they will be checked with.**

---

## What is not known, and must be read before anything is written

**The design session cannot see your tree and has not read `tws_order`.** Everything below is written as a plan against a repo whose state is unread. **Part 1 exists to replace that with observation.**

**If Part 1 contradicts the plan, stop and write a question file. Do not adapt the plan silently.** A well-formed instrument pointed at the wrong repo is exactly the failure this project catalogues most.

---

## Part 1 — read and report. Write nothing.

Establish and record, each as a plain observation:

1. **Where `tws_order` is.** Absolute path. Whether it is inside `D:\Dev`.
2. **Whether it is a git repo**, its HEAD, and whether it has a remote.
3. **Whether it has a test suite at all** — test files, a runner, a config. Name what you found, or state plainly that there is none.
4. **How the suite is invoked**, if one exists. The literal command.
5. **Whether the suite currently passes.** Run it once. Report the raw result.
6. **Whether a secrets test exists in it.** DoD condition 1 names one specifically.

**Report all six in the done-note whatever they say.** *There is no suite* is a complete and useful answer to 3.

### Stop conditions

**Write a question file and end the session if any of these hold:**

- **`tws_order` is outside `D:\Dev`.** `.claude/settings.json` is narrow on writes outside that root, and a task that needs a permission it does not have is a task that will half-complete. Report the path and stop.
- **There is no test suite and no runner.** Creating one is a larger piece of work than this task scopes, and it changes what S031 and S032 cost. That is a decision with a size attached and it is not this task's to make.
- **The suite exists and is red.** Report what is red. A new instrument pointed at an already-failing suite reports a failure that predates it, and the first green will look like a fix.

---

## Part 2 — `verify.ps1` reports on `tws_order`

**Only if Part 1 cleared every stop condition.**

`verify.ps1` gains a section that reports, into `verify-output.md`:

- **`tws_order`'s absolute path and its HEAD at run time.** Both, always — a result with no HEAD beside it cannot be tied to a commit.
- **The suite's result**, as raw output. **Do not summarise it and do not quote a test count.**
- **Whether the suite was reachable at all**, as a distinct state from passing and from failing.

### Three states, and they must not read alike

| | Renders |
|---|---|
| Suite ran, passed | The raw result, with path and HEAD |
| Suite ran, failed | The raw result, with path and HEAD |
| **Suite could not be run** | **A named line saying so and why.** Never blank, never absent, never an old result |

**The third is the one that matters.** A section that silently renders nothing when the repo is unreachable is indistinguishable from a section that was never added — **and the reader concludes the instrument does not exist rather than that the repo could not be reached.** Same shape as B-090.

### Constraints

- **`verify.ps1` still describes one worktree of `momentum`.** This section describes a second repo and must say which repo each line is about. **Two repos in one output file with unlabelled lines is a well-formed value answering a different question.**
- **Run `tws_order`'s suite from its own checkout**, never from a `momentum` worktree.
- **Any scratch goes to `$env:TEMP`.** Never either repo.
- **Touch no `tws_order` source.** This task adds an instrument; it does not change the thing measured.

---

## Part 3 — demonstrate red

**A test that passes is not a test that works.**

**Show the new section reporting a failure before accepting it reporting success.** Break something reversible — a deliberately failing temporary test in `tws_order`, or an unreachable path — confirm `verify-output.md` renders the failing state and names it, then revert.

**Record in the done-note what you broke, what the output said, and that you reverted it.** **A section only ever seen green carries no information**, which is the whole reason condition 1 says *seen red first*.

---

## Exit tests

**Green** — `verify.ps1` runs from the main checkout of `momentum` and `verify-output.md` contains the `tws_order` section with path, HEAD and raw result.

**Refusal** — the could-not-be-run state renders as a named line. **This is the refusal test and it is not exempt.** An instrument whose failure state is invisible is worse than no instrument.

**UAT — Christoph** — he opens `verify-output.md` and answers one question: **can he tell which repo each line is about, and whether `tws_order`'s suite passed, without asking anybody?** That is a question about whether a person can read it, which is the only kind of question a UAT is for.

---

## Done-note must contain

- **All six Part 1 observations**, whatever they say.
- **What was broken in Part 3, what the output said, and confirmation it was reverted.**
- **That `verify.ps1` ran, and when.** **Never a test count.**
- **Any `tws_order` finding that changes what S031 or S032 cost** — as an `OBSERVATIONS.md` entry, resolved `PROMOTED` or `DROPPED`, never deleted.

**Do not paste or summarise `verify-output.md`. The design session reads it through the export.**

---

## Closing sequence

**Sync, work, verify, export, push. All from the main checkout.** `CLAUDE.md` carries it; it is not restated here.
