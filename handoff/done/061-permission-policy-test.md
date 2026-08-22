---
id: 061
title: The settings.json deny control is now carried by a test, not by memory
type: task
class: admin
owner: claude-code
unblocks: NOTHING
depends: none
touches: tests/test_permission_policy.py
bugs: []
---

**Status** RUNNING

# 061 — done. The deny entries are already present; the test found them present.

`tests/test_permission_policy.py` exists, asserts the property `061` asked for, and passes
against the real `.claude/settings.json` as it stood at the start of this session. **This
session did not add, edit, or need to add the deny entries** — they were already in the working
tree, uncommitted, before this task ran (`git diff` on `.claude/settings.json` shows only
Christoph's edits: the two lines under `deny`, plus unrelated `allow` additions). This session
never opened that file for writing.

---

## 1 — what the test checks, and why it does not pin the two strings

The property: **`permissions.deny` contains a `Write` or `Edit` entry — the two tool names this
policy file already uses for file mutation, confirmed by reading its own `allow`/`ask` sections —
whose pattern covers `.claude/settings.json` itself.** `Write`/`Edit` and `covers_settings_json`
are the whole check; nothing else in `deny` is inspected.

**Not the literal strings.** `covers_settings_json` glob-matches the pattern against two path
forms this repo's own policy already uses for the same file — `.claude/settings.json` (the form
Christoph pasted) and `//d/Dev/momentum/.claude/settings.json` (the form already sitting in
`ask`, added before this task). A wildcard covering either form would still be detected; `B-029`
is what pinning the exact pasted text would have produced instead.

## 2 — red, seen against the real content, not a synthetic stand-in

Per §2's demonstration requirement, before accepting green: copied the real `.claude/settings.json`
into `$env:TEMP\settings_test_061\`, stripped exactly the two `deny` lines
(`Write(.claude/settings.json)`, `Edit(.claude/settings.json)`) in a second copy, and called the
detector against both, outside pytest:

```
without control (expect False / RED):  False
with control    (expect True  / GREEN): True
```

Scratch directory removed afterward. **The real file was opened for reading only, at no point
for writing**, and the mutation happened to a copy under `$env:TEMP`, never to a copy inside the
repo.

## 3 — the two refusal cases, exercised

- **Malformed JSON.** A scratch file containing `{not json` raises `PolicyError` with `"is not
  valid JSON"` in the message — caught by `pytest.raises`, not surfacing as a bare
  `json.JSONDecodeError` traceback. A missing `permissions.deny` key does the same, named
  separately.
- **A verb that is not a real tool name.** `WriteAccess(.claude/settings.json)` in `deny` is not
  detected as a control — `WriteAccess` is not `Write` or `Edit`, so the entry is skipped rather
  than counted. This is the reason `covers_settings_json` gates on the tool name at all instead of
  a plain substring search over the deny list, which would have accepted it.

8 tests in the file, all green: 1 against the real policy (plus a cheap JSON/deny-list-shape
check), 4 against scratch fixtures (present via both path forms, absent, wrong verb), 2 for the
named-refusal cases.

## 4 — the deny entries were already there; §3 of the task did not apply

Task `061` §3 anticipated the deny entries not existing yet and said to leave the test red and
name `christoph/open/035-*` as the blocker. **That branch did not fire.** `git diff -- .claude/settings.json`
shows the two lines already present, uncommitted, when this session started — Christoph had
applied them before this task ran. Nothing in this session added them.

## 5 — found in passing, not fixed, logged as OBS-080

Running the full suite (via `verify.ps1`, see §7) surfaced a pre-existing defect unrelated to
this task: `handoff/inbox/056-for-code-task-two-false-guards.md`'s frontmatter contains an
unquoted colon inside prose (`"Rule 16: this counts in the..."`), which is invalid YAML.
`tests/test_task_file_shape.py` loops over every task file numbered 049+ with no per-file
exception handling, so `yaml.safe_load` raising on `056` aborts the loop before any other file —
including `057`–`061` — is ever checked. Three of that file's tests fail with a traceback rather
than a named violation.

**Not fixed here** — out of scope for a task touching `tests/test_permission_policy.py`, and
fixing another task's file from inside this one is how a task acquires work nobody scoped.
Logged as `OBS-080` in `docs/observations/OBSERVATIONS.md`, review-by 2026-11-22.

## 6 — two guards this task's own new file tripped, both fixed in this commit

The full-suite run (not the targeted one) caught two things a targeted run of
`tests/test_permission_policy.py` alone could not have: `test_adoption_log_complete.py`
went red because `tests/test_permission_policy.py` itself is a tracked file with no
`ADOPTION-LOG.md` row — `tests/` carries no native carve-out, so an authored test needs a row
the same as any other code-tree file. Added, following the exact format the other `053`/`054`/`061`-era
"authored in this tree; not imported" rows use. `test_donenote_bugs_block.py` went red because
this done-note (numbered `061`, inside its `FROM_TASK = 53` scope) had no `bugs:` key — added
`bugs: []`, since this task closed no bug. **Same shape `046` §5 named**: a targeted run of the
file you just touched cannot see a repo-wide guard that reads `git ls-files` or walks
`handoff/done/`. Full suite re-run after both fixes: back to the same 12 pre-existing failures,
none of them new.

## 7 — sync.ps1 exited 1, pre-existing, not this task's

`sync.ps1` (run first, per the closing sequence) refused to overwrite three differing
`handoff/inbox/` files — `040`, `043`, `052` — same shape `045` §5 and `046` §9.4 already
recorded for `040`/`043`; `052` differing is new to this run and not investigated further here,
for the same reason: resolving a handed-off file that changed is not this task's scope, and it
does not block `061`'s own work. It also pulled `christoph/open/035-*` and `036-*` in (2 new),
committed alongside this work since sync had already placed them in the tracked tree before
`verify.ps1` ran.

---

## 8 — another session was concurrently active in this checkout while this ran

While preparing this commit, `verify.ps1` (unstaged, code changes — a new §10 for `tws_order`)
and a new `handoff/inbox/062-for-code-task-tws-order-test-instrument.md` appeared in the working
tree, neither written by this session. **Left untouched, deliberately** — `OBS-036`'s exact
shape: mutating a shared checkout while another party holds uncommitted work there can destroy
it, and neither file was staged by this commit. `git commit` only commits the index, so this
work is unaffected by whatever lands in `061`'s commit. `sync-run-record.md` was updated a second
time after this session staged it (presumably by the other session's own `sync.ps1` run, or the
15-minute scheduled task); the staged copy is this session's own run and the newer content
remains as an unstaged diff afterward, not lost.

---

## Exit tests

| test | result |
|---|---|
| `tests/test_permission_policy.py` exists and passes | **green**, 8/8 |
| Seen red with the deny entries removed | **yes**, against a scratch copy of the real file's content — §2 |
| Does not read or write the real `.claude/settings.json` except to read it | **true** — grep confirms no test in the file opens `POLICY` for writing; the only writes are to `tmp_path`/scratch fixtures |
| Malformed JSON refusal | **green** — named `PolicyError`, not an unhandled exception |
| Non-real-tool-verb refusal | **green** — not detected as a control |
| UAT (Christoph) | **not run in this session** — §5 of `061` names it as his: confirm the test is green, then confirm a later session cannot write `.claude/settings.json` |

---

## The closing sequence

**`sync.ps1` first, then `verify.ps1`, then the commit, then `export-handoff.ps1`, then the
push** — all from the main checkout, no worktree.

- **`sync.ps1` ran.** 2 new (`christoph/open/035-*`, `036-*`), 3 REFUSED (`040`, `043`, `052`
  differ between Drive and the tree — §7). Exit 1.
- **`verify.ps1` ran** at the time recorded in `handoff/verify-output.md`, HEAD in its own §3.
  Not pasted or summarised here.
- **`export-handoff.ps1` runs after the commit that contains this note**, so its manifest HEAD is
  that commit.
- **Pushed to `origin` (`trading-terminal`).**

---

**This note needs to be pasted to chat.**
