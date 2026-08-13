# 023 — done — `verify.ps1` writes a file, and the paste step retires

**Status** RUNNING · **Date** 2026-08-13 · **Type** protocol · **Tree** `D:\Dev\momentum`

> **This note needs to be pasted to chat** — or, from this task onward, read directly.
> **It is deliberately shorter on evidence than every note before it**, and that is the change:
> the evidence is `verify-output.txt`, and merging it into here is what the gate now forbids.

---

## 1. What changed in `verify.ps1`, and what did not

**Three changes. No section's content changed.**

| Change | Detail |
|---|---|
| **`Say` replaces `Write-Host`** | A one-line function that prints **exactly what `Write-Host` printed** and also keeps the line. 56 call sites. **Tee, not redirect** — console output is unchanged, because a task that silences a familiar tool is a task that gets worked around |
| **`HEAD at start` in the header** | Captured before section 1 runs, compared against `HEAD` at the end |
| **The file write** | `verify-output.txt` in the repo root, **overwritten each run, never appended** |

**Confirmation that no section's content changed**, and it is a comparison rather than an
assertion: the run at **15:04:34** (before) and the runs at **15:08:04–15:08:27** (after) are
identical line for line across all five sections and the runtime block — `2 failed, 236 passed`,
the same two named failures, the same 179 evidence rows, the same export block. **The only added
line is `HEAD at start`**, which 023 asks for.

`Say` cannot change content by construction: it is `Write-Host $msg` plus a list append.

### Overwrite, not append

The file describes **one run of one tree at one `HEAD`**. A growing file invites reading a stale
section as current — the exact confusion this gate exists to prevent.

### The `TREE MOVED` warning goes in the header, not the footer

If `HEAD` at start and end differ, sections above and below the change describe different
commits and **the file cannot say which is which**. A reader opening it out of context must not
have to reach the end to learn that. It is inserted at the header position in the file and
printed to the console at the moment it is discovered.

### A defect I introduced and caught in the same task

**The first version reported `CANNOT COMPUTE:` in front of a `HEAD` it had just read correctly,
and then compared that string against a clean one at the end and announced `THE TREE MOVED`.**
A false alarm on the loudest line in the file, on the very first run.

Cause: `& git rev-parse HEAD | Select-Object -First 1`. **`Select-Object -First` stops the
pipeline as soon as it has its object**, which terminates `git` early and can leave
`$LASTEXITCODE` non-zero on a command that succeeded. It is a race — the second run was clean,
which is the worst kind.

Fixed by capturing first and selecting after, in a `Get-Head` helper used at both ends.
**Confirmed over three consecutive runs: no warning, correct `HEAD` every time.**

### The header comment was false and is now corrected

`verify.ps1` opened with **`IT NEVER MODIFIES ANYTHING`**. That is no longer true. It now reads
`IT MODIFIES NOTHING IN THE TREE, WITH EXACTLY ONE EXEMPTION`, names the file, and says why the
exemption is stated rather than left to be discovered — **a reader who finds an unexplained write
is right to distrust the rest of the script.**

`test_verify_output_is_ignored.py` pins that the exemption stays the only one: no `git add`, no
`git commit`, no `New-Item`, and **exactly one** `Remove-Item` (the section-4 rehash script, in
the system temp directory, not in the tree).

---

## 2. The `git check-ignore` assertion, quoted

```python
def check_ignore(rel: str) -> bool:
    """Exit 0 = ignored, 1 = not ignored. `--no-index` so the answer is about the
    rules, not about whether the file happens to exist right now."""
    r = subprocess.run(["git", "check-ignore", "--no-index", "-q", rel],
                       cwd=REPO, capture_output=True)
    return r.returncode == 0


def test_verify_output_is_ignored() -> None:
    assert check_ignore(OUTPUT), (
        f"`git check-ignore` says {OUTPUT} is NOT ignored. verify.ps1 writes it on "
        "every run, so an unignored file means the next `git add -A` commits a "
        "machine-local snapshot of one moment as though it described the tree."
    )
```

**Asked of git, not of `.gitignore`'s text.** A substring match proves the line is present; it
does not prove the line has effect, and the negation blocks in this file are load-bearing.

Four more tests around it: it must be ignored **before it exists** (a fresh clone is exactly when
someone runs the script and commits the result); the helper must return `False` for `README.md`
and for `verify.ps1` itself, or it proves nothing; the rule must be **anchored** — `docs/verify-output.txt`
must *not* be ignored, since an unanchored rule would swallow a file of that name at any depth;
and `verify.ps1` must still name the path this test guards, so the two cannot drift.

The rule, in `.gitignore`:

```
/verify-output.txt
```

---

## 3. The rewritten protocol section, quoted in full

`docs/specs/HANDOFF-PROTOCOL.md` is now **v1.2**. The `REVIEWED` row:

> | **REVIEWED** | **All three of:** the done-note exists; `verify-output.txt` exists, is **newer than the done-note**, and its `HEAD` **matches** the note's; and the design session has read both and named every open issue. | … |

and the `RUNNING` gate, which no longer names a paste:

> | **RUNNING** | Christoph answers yes. | Claude Code writes the done-note **and runs `verify.ps1`**. Design session reads both directly. |

The new section, in full:

> ## The verification gate — rewritten in full, v1.2 (023)
>
> **The last action of any task that changes the tree is to run `verify.ps1`.** Unprompted, every time, after the commit. It writes `verify-output.txt` in the repo root, overwritten each run.
>
> **The done-note states one line: that `verify.ps1` was run, and at what time. Nothing more.**
>
> **Do not paste its output into the done-note, and do not summarise it.** The file is the **evidence**; the note is the **claim**. Merging them destroys the only independence the gate has — a claim checked against a summary written by the claimant is not checked.
>
> ### Why this changed, recorded so it is not reverted
>
> **The paste step rested on a premise that is no longer true.** The gate was designed when the design session **could not see the repo**, so Christoph was the only channel, and his job was to carry raw output he was explicitly not expected to interpret.
>
> **The design session now reads the tree directly.** It has staged and read files under `handoff/done/`, enumerated `handoff/inbox/` to assign task numbers, and listed the tree in full. **For reading, the courier step is obsolete**, and Christoph's objection to it is correct: he gets no value from pasting output he cannot interpret, and a step with cost and no benefit is a step that will be skipped inconsistently rather than deliberately.
>
> **The property is preserved and strengthened, not dropped.** The gate exists so that *a done-note is not its own evidence*. Reading the raw artifact is a **stronger** form of that: the design session compares the note against the file itself rather than against a report of it.
>
> **This paragraph is the reason.** A protocol change with no recorded reason gets reverted by the next person who reads the old rationale and finds it persuasive — and the old rationale is still persuasive, because it was correct when it was written.
>
> ### What `verify-output.txt` must satisfy
>
> | Check | Why |
> |---|---|
> | **Exists** | Absent means the task did not finish its last step, whatever the note says |
> | **Newer than the done-note** | An older file describes a tree from before the work. **Same failure as a stale mirror**: it looks exactly like a current one |
> | **Its `HEAD` matches the note's** | Two files describing two commits cannot corroborate each other |
> | **Its header shows no `TREE MOVED` warning** | The script captures `HEAD` at start and at end. If they differ, sections above and below describe different commits and **the file cannot say which is which** |
>
> ### Two limits, both unchanged in force
>
> **1. Nothing reports on `verify.ps1`.** It reports on the repo, and if it ever printed a comfortable falsehood — a summary line it mis-parsed, a section it silently skipped — nothing would catch it. **This task did not close that gap and this protocol keeps saying so.** The mitigation is only that the script has no opinion: it prints raw facts, so a falsehood would have to be a transcription error rather than a judgment error.
>
> **2. The direct read depends on Christoph's desktop being connected.** When it is not, **the paste is the fallback** — an exception, not the routine. **Do not read this section as "the channel is unconditional."** While the fallback is in use, rule 4's original allocation applies in full: whether the whole of it arrived is Christoph's to report, because he is again the only party who can see both sides.

**Two other edits followed from it**, both flagged here because 023 asked for a full rewrite of
the gate and these sit outside the new section:

- **Rule 3** was *"The paste is the channel; there is no other."* It now names `verify-output.txt`
  as the independent artifact, carries `016`'s three contradictory test counts as the case it
  exists for, and adds that **a summary of the file is not a substitute for the file.**
- **Rule 4** listed *"whether the whole of it arrived"* among the facts only Christoph can see.
  For a note read directly, truncation is visible to the reader. **It returns to him whenever the
  fallback channel is in use**, and the amendment says so rather than deleting the clause.

---

## 4. What I could not do

1. **I could not test the `TREE MOVED` path against a real mid-run commit.** It was exercised
   accidentally and convincingly by the `$LASTEXITCODE` defect above — the warning rendered in
   full, in the header, with both values — but that was a false positive. **A true positive needs
   a commit landing between section 1 and the end of the run**, and staging one would mean
   committing from another process while the suite runs. **Not attempted.** The comparison itself
   is one `-ne` on two strings from the same helper.
2. **`test_verify_output_is_ignored.py` cannot prove the file is *never* committed** — only that
   the rule ignores it today. Someone can still `git add -f`.
3. **Nothing reports on `verify.ps1`.** Unchanged by this task and recorded in the protocol.
   `test_verify_ps1_still_modifies_nothing_else` is the nearest thing, and it checks the script's
   *text*, not its behaviour.
4. **`git add -A` swept in a file that is not mine, and the gate caught it.**
   `tools/probe_keepuptodate_scale.py` — 406 lines, task **021**'s investigation script — was
   authored into the tree at **15:10:58**, three minutes before 023 committed, and the blanket add
   took it along. **023's commit message says nothing about it, which made that commit a false
   record of what happened.**

   `test_every_tracked_file_is_accounted_for` went red immediately: `tools/` is a code tree with
   no native-prefix carve-out, so the file needs a provenance row and a **behavioural** test, and
   import-smoke does not count. **That is 021's to provide.**

   Un-tracked in a follow-up commit. **The file is untouched on disk and stays there.** The
   lesson is about the blanket add, not the file: **the tree can change under a long task**, and
   `git add -A` commits whatever arrived meanwhile.

5. **I did not add the version-pin test `HANDOFF-PROTOCOL.md` says it is owed.** Its own version
   history states *"a version pin belongs in a test … that test does not exist yet and is owed by
   the next task file."* **023 is a task file that touched this document and did not add it**, so
   the debt is now one task older. It is not in 023's scope and I am naming it rather than
   quietly leaving it.

---

## The suite

| When | Result |
|---|---|
| Before 023 | **227 passed, 2 failed** |
| After 023 | **236 passed, 2 failed** |

Nine new tests. The two failures are unchanged and both blocked on a person: 020's UAT gate, and
the task files carrying `status: READY` in frontmatter instead of a `**Status**` header.

## 5. The one line

**`verify.ps1` run at 2026-08-13 15:14 +02:00.**

**Its output is deliberately not reproduced here.** It is in `verify-output.txt` at the repo root,
written by that run. **This is the first note written under v1.2** — `020`, `026` and `027` each
quoted a verify summary table into the note, which v1.2 now forbids, and those notes are not
retro-edited because they were correct under the protocol in force when they were written.
