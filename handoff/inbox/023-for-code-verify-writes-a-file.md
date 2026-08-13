---
id: 023
title: verify.ps1 writes its output to a file, and the paste step retires
status: READY
blocks: []
type: protocol
owner: claude-code
---

# 023 — `verify.ps1` writes a file, and Christoph stops being the courier

**The premise the paste step rested on has changed.** The verification gate was designed
when the design session **could not see the repo**, so Christoph was the only channel and
his job was to carry raw output he was explicitly not expected to interpret.

**The design session now reads the tree directly.** In this session it staged and read
`handoff/done/008b-keepuptodate.md`, enumerated `handoff/inbox/` to assign task numbers 021
and 022, and listed `D:\Dev\momentum\` in full. **The courier step is obsolete for reading**,
and Christoph's objection to it is correct: he gets no value from pasting output he cannot
interpret.

**What must not be lost is the property, not the mechanism.** The gate exists so that
**a done-note is not its own evidence**. `016` part 1 records the case: `015` claimed
`103 passed, 1 failed`, `012` claimed `2 failed, 102 passed`, and the tree was at
`126 tests, 2 failed, 124 passed`. **Neither note described this tree**, and nothing was
contradicted or confirmed because there was nothing independent to compare against.

**Reading the raw artifact directly preserves that property and strengthens it** — the
design session compares the note against the file itself rather than against a report of it.

---

## Standing constraints

- **`verify.ps1` still does not interpret.** No `PASS`, no verdict, no exit-code-as-opinion.
  Its whole value is that it has no view — a script that says "all good" is one more claim
  to verify, not a way of verifying claims. **This task changes where the output goes and
  nothing about what it says.**
- **It still never modifies the tree** — no writes, no `git add`, no fixture creation.
  **The output file is the single exception**, and it must be the only one.
- **A section that cannot be computed still prints why and continues.** A script that aborts
  halfway reports less the more wrong things are.

---

## Part 1 — Write the output to a file as well as the console

**Tee, do not redirect.** Console output stays exactly as it is — Christoph may still want
to glance at it, and a task that silences a familiar tool is a task that gets worked around.

Write to **`verify-output.txt`** in the repo root. **Overwrite each run, do not append**:
the file describes one run of one tree at one HEAD, and a growing file would invite reading
a stale section as current — the exact confusion the gate exists to prevent.

**The header must make the run self-describing**, because the file will be read out of
context by a party that was not present when it ran:

```
verify.ps1  --  D:\Dev\momentum
run at 2026-08-13 11:04:22 -04:00
HEAD at start  <sha>
```

**Capture HEAD at the start as well as in section 3.** If the two differ, the tree moved
mid-run and **the file must say so in its header rather than leaving it to be noticed** —
that is precisely the 2026-08-12 catch, and it should be loud rather than latent.

---

## Part 2 — Gitignore it

`verify-output.txt` is **generated, per-machine, and describes a moment**. Committing it
would create a second source of truth about the tree that ages badly and diffs noisily.

Add it to `.gitignore` and **assert with `git check-ignore` in a test**, the same way the
archive directory already is. The negation blocks in that file have swallowed an intended
path before.

---

## Part 3 — Run it at the end of every task, unprompted

**Append to the standing task convention**: the last action of any task that changes the
tree is to run `verify.ps1`. **Do not paste its output into the done-note, and do not
summarise it** — the file is the evidence and the note is the claim, and merging them is
what this whole mechanism exists to prevent.

**The done-note states one line: that `verify.ps1` was run, and at what time.** Nothing more.

---

## Part 4 — Amend `docs/specs/HANDOFF-PROTOCOL.md`

**Rewrite the verification-gate section in full** — not a patch. `REVIEWED` is now reached
when:

1. The done-note exists.
2. **`verify-output.txt` exists, is newer than the done-note, and its HEAD matches.**
3. The design session has read both and named every open issue.

**Delete the instruction that Christoph pastes output.** Replace it with the direct read,
and **record why the change was made** — that the design session gained repo access, so the
courier step became cost with no benefit. **A protocol change with no recorded reason gets
reverted by the next person who reads the old rationale and finds it persuasive.**

**Keep the limit that was always true and still is:** `verify.ps1` reports on the repo and
nothing reports on `verify.ps1`. If it ever printed a comfortable falsehood, nothing would
catch it. **That gap is not closed by this task and the protocol should keep saying so.**

**One new limit to record:** the design session's read depends on Christoph's desktop being
connected. **When it is not, the paste is the fallback** — an exception, not the routine, and
the protocol should name it as such rather than pretending the channel is unconditional.

---

## Done when

- `verify.ps1` writes `verify-output.txt` and still prints to console, unchanged in content.
- The header carries repo path, run time, and **HEAD at start**, with a loud line if HEAD
  moved during the run.
- `verify-output.txt` is gitignored, asserted by a `git check-ignore` test.
- `HANDOFF-PROTOCOL.md` is rewritten with the new `REVIEWED` definition, the recorded reason
  for the change, the unchanged self-reporting limit, and the new connectivity limit.

---

## Deliverable

`handoff/done/023-for-code-verify-writes-a-file.md`:

1. What changed in `verify.ps1`, and confirmation that **no section's content changed**.
2. The `git check-ignore` assertion, quoted.
3. The rewritten protocol section, quoted in full.
4. **What you could not do**, and why. Empty is suspicious.
5. **The one line**: `verify.ps1` run at `<time>`. **Not its output.**
