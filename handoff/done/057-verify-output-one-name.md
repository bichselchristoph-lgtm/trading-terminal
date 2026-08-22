---
id: 057
title: verify-output is named .txt in four places and is .md in one
type: task
class: admin
task_version_executed: 1.0
owner: claude-code
tree: D:\Dev\momentum
branch: 057-verify-output-one-name, merged to main
bugs:
  - id: B-090
    action: close
    status: FIXED
    priority: 1
    title: verify.ps1 names its own output artifact under two different strings
    spec: PROCESS-SPEC
    resolution: >-
      The literal `verify-output` now occurs exactly once in verify.ps1, at
      the line that actually defines $outFile (`handoff\verify-output.md`).
      Lines that previously named the stale `.txt` literal (the header block,
      and two comments near section 8) now refer to it in prose ("the verify
      output file", "the verify output") with no filename at all. Line 73's
      original comment block (already correct, .md) was also folded into
      prose so the single remaining literal is unambiguous rather than
      merely the majority. verify.ps1 now also states its own output path as
      a fourth header line, written before section 1, so a reader holding
      the file never has to consult a document to learn where it came from.
      Exit tests: test_verify_output_is_named_in_exactly_one_place,
      test_the_check_can_actually_fail, both in
      tests/test_verify_output_named_once.py.
bugs_note: >-
  B-090 is the only bug this task touches. OBS-078 (below) is a separate,
  unrelated, pre-existing finding surfaced while running the full suite for
  this task -- not fixed here, not this task's to fix.
---

**Status** RUNNING

# 057 — verify-output is named .txt in four places and is .md in one

Gate checked first: `handoff/inbox/057-for-code-task-verify-output-one-name.md` did not exist
in the tree at task start. Pulled in via `sync.ps1` (the correct channel), confirming the gate
before doing anything else.

## What was wrong, and what B-090 actually cost

`verify.ps1` wrote its output to `handoff\verify-output.md` (line 73, unchanged since before
this task) while four of its own comments referred to the file by three different names — `.md`
correctly once (line 32) and `.txt` incorrectly three times (the old lines 64, 640, 643). The
design session searched for `verify-output.txt`, did not find it, and concluded the
verification gate had never been reachable — a false conclusion the file's own comments
produced.

## Part 1 — one literal, one site

`grep -n "verify-output" verify.ps1` before this task: five matches (lines 32, 64, 73, 640,
643). After: **exactly one**, at line 73 (now 74, after Part 2's added line), where `$outFile`
is actually defined.

- Line 32's comment (`**It writes \`handoff/verify-output.md\`**`) — already correct in
  content, folded into prose (`**It writes the verify output file**`) anyway, since the task's
  own stated outcome ("appears exactly once, at line 73") requires reducing every site to
  prose, not just the three wrong ones. A comment that happens to be right is still a second
  site.
- Lines 64, 640, 643 — the three wrong `.txt` references — now read "the verify output file" /
  "the verify output" with no filename, matching the task's own suggested forms.
- Line 73 (the actual `$outFile = Join-Path $repo 'handoff\verify-output.md'` assignment) —
  **untouched**, per instruction: "Do not change line 73. `.md` is the definition."

## Part 2 — the file states its own path

Added a fourth header line, written immediately after `HEAD at start` and before section 1:

```
Say "output file    $outFile"
```

`$outFile` is defined at line 74, well before this header block, so it is in scope. A reader
holding the file now sees its own path on line 4, and a reader who cannot find the file at that
path learns the *document* pointing at it is wrong, not that the instrument never ran.

## Part 3 — demonstrated red before accepting green

Per instruction, the demonstration used a **scratch copy under `$env:TEMP`**, never the repo
(rule 20):

1. Copied `verify.ps1` to `$env:TEMP\057-demo\verify.ps1`. Counted `verify-output`: **1**
   (matches the real file).
2. Appended a second `# ... verify-output ...` comment line to the scratch copy. Counted again:
   **2**.
3. Ran the exact assertion (`n == 1`) against the planted copy via a standalone script — **it
   raised `AssertionError: the literal \`verify-output\` occurs 2 times ... not exactly once`**,
   exit code 1. Red, for the right reason: a genuinely planted second occurrence, not an
   unrelated failure.
4. Restored the scratch copy to the clean state (re-copied from the real, fixed `verify.ps1`).
   Ran the same assertion again: **`PASS: exactly one occurrence`**, exit code 0.
5. Removed the scratch directory (`$env:TEMP\057-demo`) entirely. Nothing under the repo at any
   point.

The permanent test, `tests/test_verify_output_named_once.py`, carries the same demonstration in
miniature as `test_the_check_can_actually_fail` — it asserts the real file is at count 1, plants
a second occurrence **in memory only**, and asserts the count changes to 2. This is the rule
being tested, not the current file's content being pinned: the expected count is the literal
`1`, independent of what the file happens to say.

## A new, unrelated finding — not fixed here

Running the full suite after the fix surfaced `tests/test_export_scope_is_derived.py::
test_destination_contains_nothing_outside_its_source[1]`, red: the Drive folder
`momentum-christoph-done` holds `.gitkeep` (since 2026-08-11) and
`018-for-christoph-task--check--screenshot.png` (since 2026-08-16), neither ever exported by
`export-handoff.ps1` (which correctly refuses non-`.md` files and prints so on every run).
**Pre-existing — both files predate this session by days — and not caused by anything in this
task.** Recorded as `OBS-078`. Not fixed here: out of scope for a `verify.ps1` naming task, and
the test's own message rules out fixing it by widening the test.

## Exit tests

**Green** — `verify.ps1` ran from the main checkout, HEAD `1f255f1` at that point (before this
branch's merge). The Part 3 test was seen red first, for the right reason (a genuinely planted
second literal), then green. No test count is quoted as a headline number; the two new tests are
named above, and the full suite's named failures are listed for the reader rather than counted.

**Refusal** — not applicable, stated per the task's own exemption: this task renders nothing and
has no input that can be missing.

**UAT** — none authored here. Christoph's own `Select-String -Path D:\Dev\momentum\verify.ps1
-Pattern 'verify-output'` now returns exactly one match, at the line that defines `$outFile` —
the same instrument that found the defect confirms the fix.

## Worktrees

Not touched. Same five reported by `verify.ps1` section 7 as every prior task this session.

## Closing sequence

`sync.ps1` → `verify.ps1` → commit (branch `057-verify-output-one-name` merged into `main`,
`--no-ff`) → `export-handoff.ps1` → push to `origin` (`trading-terminal`), all from the main
checkout, no worktree.

---

**This needs to be pasted to chat.** Per the handoff convention, chat cannot see this repo —
writing it here is not the same as it being read.
