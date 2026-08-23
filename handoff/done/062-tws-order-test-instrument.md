---
id: 062
title: verify.ps1 gains a tws_order section — S031 and S032 can now reach REVIEWED
type: task
class: admin
owner: claude-code
unblocks: S031, S032
depends: none
touches: verify.ps1, docs/observations/OBSERVATIONS.md
bugs: []
---

**Status** RUNNING

# 062 — done. `verify.ps1` §10 reports on `tws_order`; both the green and the refusal states were demonstrated red-then-green.

`sync.ps1` pulled `062` in first (see §7 below). Part 1 cleared every stop condition, so Part 2 and
Part 3 both ran.

---

## Part 1 — the six observations, as instructed, whatever they said

1. **Where `tws_order` is.** `D:\Dev\tws_order` — inside `D:\Dev`, sibling of this checkout.
2. **Git repo, HEAD, remote.** Yes. HEAD `3e165a4b4009bc56e1a4f73a46e4756bb1b34195`. `origin` →
   `https://github.com/bichselchristoph-lgtm/tws_order.git`.
3. **Test suite.** Yes — `tests/test_cli.py`, `test_config.py`, `test_sizing.py`, `test_stops.py`.
   A `.pytest_cache` was already present, so it had been run before this task.
4. **Invocation.** `C:\venvs\trading\Scripts\python.exe -m pytest --color=no`, run from `tws_order`'s
   own root. No `pytest.ini`/`pyproject.toml`/`setup.cfg` exists there; pytest's default discovery
   finds `tests/` unassisted, confirmed by running it both with and without an explicit `tests`
   argument — identical result either way.
5. **Did it pass.** Yes: `37 passed, 1 warning in 0.32s`–`0.95s` across three separate runs today.
6. **A secrets test.** No — `grep -ril secret tests` and a repo-wide case-insensitive `secret` search
   both return nothing. DoD condition 1 names one specifically; `tws_order` does not have one.

None of the three stop conditions fired: the repo is inside `D:\Dev`, a runner exists, and the
suite was green before this task touched anything. No question file was needed.

---

## Part 2 — `verify.ps1` §10

Added a tenth section, `TWS_ORDER -- a second repo's suite, path and HEAD beside it`, placed after
§9 (QUESTIONS) and before the runtime footer. It:

- Derives `$twsOrderPath` as the sibling of `$repo` (`Split-Path -Parent $repo` + `\tws_order`) —
  the same pattern §7 already uses for the worktree roots, rather than a second hardcoded absolute
  path.
- Prints `tws_order path` and `tws_order HEAD` (via `git -C $twsOrderPath rev-parse HEAD`).
- Runs the suite via `Push-Location`/`Pop-Location` around a `try`/`finally`, so a crash mid-call
  cannot leave the script's own working directory pointed at the wrong repo for the sections after
  it. Never invoked from a `momentum` worktree.
- Prints the raw pytest output verbatim — no summary line extraction, no test count, same rule
  §1 already follows.
- On any of three unreachable conditions — path missing, not a git checkout, `python` missing —
  prints a **named** `tws_order SUITE COULD NOT BE RUN: ...` line instead of nothing.

Also updated the closing line (`nine facts` → `ten facts`) and the file's own header comment, which
had drifted: it said "seven facts" while the closing line already said "nine" — sections 8 (NOW) and
9 (QUESTIONS) were added under `045`/`054` without the header being updated. Both now say ten and
explain the gap, so the header and the footer agree again.

**No `tws_order` source file was touched**, other than the one temporary file described in Part 3,
added and removed within this task.

---

## Part 3 — demonstrated red, both ways, before accepting green

**Green**, first: ran `verify.ps1` (via `pwsh`, see the finding below) with `tws_order` reachable and
its suite passing. `handoff/verify-output.md` §10 rendered path, HEAD and the raw `37 passed` result.

**Failed-suite red**: added `D:\Dev\tws_order\tests\test_verify_instrument_red_TEMP.py`, one test,
`assert False`. Re-ran `verify.ps1`. §10 rendered the full raw failure — traceback, `AssertionError`,
`1 failed` in the collected-items count context — under the same `tws_order path`/`HEAD` lines.
Deleted the temp file immediately after; `git -C D:\Dev\tws_order status --short` confirmed clean
before continuing.

**Refusal red** (the exit test named explicitly as "not exempt"): temporarily edited `$twsOrderPath`
in `verify.ps1` itself to point at `tws_order_TEMP_062_REFUSAL_TEST` (a path that does not exist).
Re-ran `verify.ps1`. §10 rendered:
```
tws_order path       D:\Dev\tws_order_TEMP_062_REFUSAL_TEST
tws_order SUITE COULD NOT BE RUN: the path does not exist
```
— a named line, not a blank section. Reverted `$twsOrderPath` to the correct derivation and ran
`verify.ps1` a final time to leave `verify-output.md` in the true green state (quoted under
Exit tests, below).

**`tws_order`'s own tree was touched only for the middle demonstration, and reverted before the
refusal demonstration ran** — confirmed by `git status --short` in `tws_order` showing clean both
before and after.

---

## Found in passing: `verify.ps1` does not parse under Windows PowerShell 5.1

`powershell.exe -File verify.ps1` fails to parse — `The string is missing the terminator: "` and
four cascading "Missing closing '}'" errors, none near any real defect. Confirmed with
`[System.Management.Automation.Language.Parser]::ParseFile` against the **unmodified, committed**
file at HEAD before this task's edits: same five errors, same relative line offsets. `pwsh`
(PowerShell 7) parses the identical file with zero errors. The file is UTF-8 without a BOM and
contains em-dashes and other non-ASCII punctuation throughout its comments; Windows PowerShell 5.1
reads a BOM-less script using the system codepage rather than UTF-8, and something in that
misdecoding breaks its tokenizer downstream. **Not investigated further or fixed here** — out of
this task's scope, and every run in this task used `pwsh` once found. Every `verify.ps1` run this
session and going forward should use `pwsh`, not `powershell.exe`, until someone decides whether to
fix the encoding or just document the requirement.

---

## Found in passing, and logged: a second live session in the same tree, `031`'s scenario recurring

Between Part 1 and this task's final `verify.ps1` run, `git status` began showing nine modified
files and one new untracked file that this session never touched: `live/attach/attach.py`,
`live/attach/ibkr.py`, `live/tui/app.py`, `live/tui/day_record.py`, `live/tui/grammar.py`,
`tests/test_session_basis.py`, `live/tests/test_attach.py`,
`live/tests/test_attach_is_reachable_by_key.py`, `live/tests/test_qqq_2026_08_13_regression.py`,
and untracked `live/tests/test_pacing_guard.py`. Timestamps cluster at 07:46:47–07:48:38 on
2026-08-23 — inside the window this task's own `verify.ps1` run was executing. **None of these are
`061`'s files** (`061`'s `touches:` names only `tests/test_permission_policy.py`, and `061` had
already committed as `8be92f84e...` before this happened — confirmed by `git log`), so this is a
third, separate, still-uncommitted writer, unidentified. This session did not stage, edit, or
revert any of the nine/one paths — followed `OBS-036`'s precedent exactly. Logged as `OBS-081` in
`docs/observations/OBSERVATIONS.md`, review-by 2026-11-23. Section 1 of the same `verify.ps1` run
reported 13 failures in the momentum suite; whether any trace to this concurrent WIP is unknown and
not chased here — out of `062`'s scope.

---

## Exit tests

| test | result |
|---|---|
| Green — §10 present with path, HEAD, raw result | **yes**, quoted above and in `verify-output.md` |
| Refusal — could-not-be-run renders as a named line | **yes**, quoted above |
| `tws_order` source untouched (net) | **yes** — one temp file added and removed, confirmed clean before and after |
| UAT (Christoph) | **not run in this session** — his question is stated in `062`: can he tell which repo each line is about, and whether `tws_order`'s suite passed, without asking anybody |

---

## The closing sequence

- **`sync.ps1` ran first.** `1 new` (`062` itself), **3 REFUSED** (`040`, `043`, `052` differ
  between Drive and the tree — same three `061` §7 already named; not investigated further here,
  same reasoning). Exit 1.
- **`verify.ps1` ran three times** (green, failed-red, refusal-red) plus once more to restore green
  — all via `pwsh`, not `powershell.exe` (see finding above). The state in `handoff/verify-output.md`
  right now is the final, correct, green run. Not pasted or summarised here — never a test count.
- **`export-handoff.ps1` runs after the commit that contains this note**, so its manifest HEAD is
  that commit.
- **Committed narrowly, not broadly.** `git add` named exactly `verify.ps1`,
  `docs/observations/OBSERVATIONS.md`, `handoff/inbox/062-*.md`, and this done-note — never
  `git add -A`. The nine modified and one untracked path from the finding above are, deliberately,
  not part of this commit.
- **Pushed to `origin` (`trading-terminal`).**

---

**This note needs to be pasted to chat.**
