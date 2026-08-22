---
id: 057
title: verify-output is named .txt in four places and is .md in one
class: admin
unblocks: NOTHING
closes: B-090
touches: verify.ps1
---

## Gate

**If `handoff/inbox/057-for-code-task-verify-output-one-name.md` exists in your tree and
`handoff/done/057-*.md` does not, this task is for you. Otherwise stop reading and ignore
this message.**

---

## What is wrong

`verify.ps1` line 73 writes `handoff\verify-output.md`. Lines 64, 640 and 643 refer to
`verify-output.txt`. Line 32 has it right.

**Observed 2026-08-22** by `Select-String -Path D:\Dev\momentum\verify.ps1 -Pattern 'verify-output'`,
run by Christoph, output pasted into the design session. Five matches, four of them comments,
three of those wrong.

**The cost is not cosmetic, and it is already paid.** The design session looked for
`D:\Dev\momentum\verify-output.txt`, did not find it, and concluded that the verification gate
had never been reachable and that no task had ever truly been REVIEWED. **That conclusion was
false.** The file exists, it is current, and it exports to Drive on schedule.

**An artifact that exists under one name and is documented under another produces confident
wrong conclusions rather than confusion.** That is the whole finding.

---

## Part 1 — one literal, one site

**Lines 64, 640 and 643 stop naming a literal.** They refer to `$outFile`, or to
*"the verify output"* in prose with no filename at all.

**After this change the string `verify-output` appears exactly once in `verify.ps1`, at line 73,
where the file is actually named.**

**Do not change line 73.** `.md` is the definition. The artifact has history in Drive back to
2026-08-16 and renaming it would create a second file, byte-plausible beside the first, which is
the supersession failure this project has now hit four times — for no gain.

**Why comments and not just documents.** A comment describing a script's own output, sitting a few
lines from the code that contradicts it, is the self-reference trap at small scale: the check and
its subject share a file, so nothing external ever disagrees. **The fix is positional — one
definition, everything else derived from it.**

---

## Part 2 — the file states its own path

`verify.ps1` already writes repo path, run time and HEAD-at-start into the output. **Add the
absolute path of the output file itself as a fourth line.**

**What this buys.** A reader holding the file never has to consult a document to learn where it
came from. And a reader who cannot find the file learns that the *document* is wrong, rather than
concluding the instrument never ran. **That is exactly the inference that was drawn today, and it
was drawn because the artifact could not speak for itself.**

---

## Part 3 — a test, and it must be seen red first

**Assert that the literal `verify-output` occurs exactly once in `verify.ps1`.**

**Demonstrate red before accepting green.** Add a second occurrence in a scratch copy, run the
test, confirm it fails, remove it, run again. **A test never seen failing is a test whose green
means nothing** — `test_no_secrets.py` went green on both occasions a live API key sat in a
committed file.

**The test asserts the rule, not the current output.** It must not be written by reading the
current file and pinning what it finds. That is B-029, and it is how the 038 units test came to
agree with whatever the code did.

---

## Not in this task

- **Do not rename the output file.** Line 73 stands.
- **Do not touch the project instructions.** §2 and §4 carry `verify-output.txt` and that is the
  half that actually misled a reader. **It is a full-file reissue by the design session, pasted by
  Christoph, and B-090 stays open until it is done.**
- **Do not change what `verify.ps1` measures.** Only how it names its own output.
- **Do not add a second output file** in any format, for any reason.

---

## Scratch

**`$env:TEMP`. Nothing under the repo**, including the red-demonstration copy in Part 3.

---

## Exit tests

| Test | What |
|---|---|
| **Green** | The suite ran, with the Part 3 test **seen red first**, and the red was caused by a second `verify-output` literal rather than by anything else |
| **Refusal** | **Not applicable, and stated rather than skipped.** This task renders nothing and has no input that can be missing, so there is no refusal state to snapshot. It is the one exemption and it is named here so its absence is not read as an omission |
| **UAT** | Christoph runs the same `Select-String` that found the defect and reads one match. **The instrument that found it is the instrument that confirms it** |

---

## Done note

**States that `verify.ps1` ran and when. It does not quote a test count and does not paste or
summarise the output.**

**Name B-090 in the note.** A task that fixes a defect and does not name it leaves the tracker
lying.

**If Part 3's test cannot be made to fail for the right reason, stop and write a question file
rather than accepting a green.** A test that passes because it cannot fail is the defect, not the
fix.
