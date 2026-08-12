---
id: 015
title: A UAT that exists only in a done-note is not a UAT
status: DONE — exiting with the new test RED on five historical notes, as 015 instructs
owner: claude-code
ran: 2026-08-11
tree: D:\Dev\momentum
---

# 015 — a UAT must exist as a file

**Status** DONE

```
BEFORE : 99 passed, 0 failed     (014's baseline)
AFTER  : 103 passed, 1 failed
```

**The one failure is the new test, and it is the correct outcome.** Five historical done-notes
name a UAT that has no file. 015 says: *"report which and stop — do not weaken the rule to
make them pass."* I did not backfill and did not weaken.

---

## The detection rule, quoted

```python
#: **Positional, not lexical.** The first cell of a table row must be `UAT` —
#: matching the bare word anywhere would turn every done-note that *discusses*
#: UATs into a false positive, and the exclusion list to suppress those becomes
#: the hiding place. Same discipline as `test_handoff_state_declared`.
UAT_ROW = re.compile(r"^\|\s*\*{0,2}UAT\*{0,2}\s*\|(?P<rest>.+)$", re.M)

#: A declaration that nothing is owed.
NO_UAT = re.compile(r"\bnone\b", re.I)

#: `**Slice** S009` or `**Task** 012`, with or without backticks.
DECLARES = re.compile(r"\*\*(?:Slice|Task)\*\*\s*`?([A-Za-z]?\d+[a-z]?)`?")
```

`NO_UAT` is applied to **the first 80 characters** of the row only, so "None" has to be the
declaration rather than a word appearing later in a sentence about something else.

## The failure message, verbatim

```
AssertionError: these done-notes name a UAT in their exit table, but no file in christoph/ declares it:
    012a-preopen-correction.md  ->  needs a file declaring **Slice**/**Task** 012a
    H10-regime-prompt-v1.2.md  ->  needs a file declaring **Slice**/**Task** H10
    H11-resupply-rule-and-schema-fix.md  ->  needs a file declaring **Slice**/**Task** H11
    H8-and-corrections.md  ->  needs a file declaring **Slice**/**Task** H8
    M001-new-repo-and-adoption-gate.md  ->  needs a file declaring **Slice**/**Task** M001

A UAT named only inside a done-note is not a UAT: it sits in a folder nobody opens
again. THE FIX IS TO AUTHOR THE FILE — the design session authors it and Christoph
saves it to christoph/open/. See docs/specs/CHRISTOPH-TASKS.md.
If the task genuinely owes no UAT, its exit row should read `UAT | ... | None`, which
is a valid declaration and passes.
```

## How resolution D was reused

**Reused as-is, not duplicated.** The same manifest, the same derivation, the same shape:

```python
_CARRIED = re.compile(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*`(?P<rel>[^`]+)`", re.M)

def carried() -> set[str]:
    if not MANIFEST.exists():
        return set()
    return {m.group("rel") for m in _CARRIED.finditer(MANIFEST.read_text(encoding="utf-8"))}
```

A done-note recorded in `EVIDENCE-CARRY.md` is carried evidence: it completed in another
repository under a convention that did not exist, and its UAT was performed verbally if at
all. **Derived at test time, never a list.** `test_the_exemption_is_resolution_d_reused_not_a_second_mechanism`
asserts the manifest parses to something non-empty and that sampled paths really appear in it,
so the rule cannot quietly become a literal.

**It made no difference here**, and that is worth saying: **all six done-notes with a UAT row
are post-migration and none is exempt.** The exemption is in place for the same reason as in
`test_handoff_state_declared`, not because it was needed today.

---

## The five left red

| done-note | id | what its UAT asks |
|---|---|---|
| `012a-preopen-correction.md` | `012a` | compare the two depth books — **arguably already answered in the row itself** |
| `H8-and-corrections.md` | `H8` | confirm `docs\regime-snapshots\` fills after the next firing (expected empty) |
| `H10-regime-prompt-v1.2.md` | `H10` | paste v1.2 into the cloud task; predict whether the floor fires before reading |
| `H11-resupply-rule-and-schema-fix.md` | `H11` | read the four supersession answers — the only judgement in that task |
| `M001-new-repo-and-adoption-gate.md` | `M001` | write down your expected file count, then `git ls-files \| wc -l` |

**Nothing was invented for them.** Four are genuinely outstanding and want a `christoph/open/`
file authored by the design session. `012a`'s is the odd one — its row reads as a *result*
rather than a request, so it may only need its exit row rewording to `None`. **That is a
judgement about what was agreed, and not mine to make.**

---

## Exit tests

| test | result |
|---|---|
| **Green** | **103 passed, 1 failed** against 014's `99 passed, 0 failed`. Four new tests pass; the fifth is the rule reporting the five above. `S009`'s UAT resolves to `christoph/open/003-*.md`. |
| **Refusal A** | Renaming `christoph/open/003-*.md` added `S009-tui-frame-and-refusal-grammar.md -> needs a file declaring **Slice**/**Task** S009` to the failure list. Restored. |
| **Refusal B** | A temp done-note with `| **UAT** | Christoph | None. Machine-checkable. |` → **demanded a file: False**. Deleted. |
| **Refusal C** | A temp done-note mentioning UAT only in prose → **demanded a file: False**. Deleted. |
| **UAT** | **None.** This one is machine-checkable, which is the point of it — and declaring `None` here is the first use of the rule 3c adds. |

---

## Divergences from what was on disk

**Three, and the second changed the implementation.**

1. **`003` was not in `D:\Dev\_adopt\`.** Part 2 says it is. It was in **`handoff/inbox/`** —
   the folder Claude Code executes on *"do inbox NNN"*, which is exactly what
   `CHRISTOPH-TASKS.md` says must never hold a task addressed to a human. Moved to
   `christoph/open/`. It was untracked, so the move is clean.

2. **Done-note exit tables are TWO columns, not three.** 015's rule assumes
   `UAT | Christoph | None` — an owner cell and a content cell. Every done-note in this tree
   is `| test | result |`, so the UAT row has **one** cell after the label, mixing owner and
   content: `| **UAT** | **Yours.** Run it with no data… |`. Only `M001` has three.

   Part 2 says *"if the test's expected format differs from what the file declares, change the
   test to match the file"*. I applied that principle to the tables too: `UAT_ROW` captures
   everything after the label and `NO_UAT` scans it, so both shapes work. A test written to
   the three-column assumption would have matched nothing at all and passed vacuously — the
   worst outcome available.

3. **015's Green exit test expects a green suite**, but its own §Backfill instruction
   guarantees red on historical notes. The two cannot both hold. I followed the explicit
   instruction — *report which and stop* — over the optimistic exit criterion, on the grounds
   that "do not weaken the rule to make them pass" is unambiguous and the Green row is not.

---

## What was changed

```
tests/test_uat_has_a_file.py                          new — 5 tests
docs/specs/CHRISTOPH-TASKS.md                         amended in place (3a, 3b, 3c)
christoph/open/003-s009-read-the-empty-screen.md      moved from handoff/inbox/
```

`CHRISTOPH-TASKS.md` was **not re-authored** and no replacement was accepted from outside the
tree. No second exemption mechanism. Nothing backfilled. No `christoph/` file authored beyond
moving `003`. `handoff/accepted/` and every file in `EVIDENCE-CARRY.md` untouched. `SPEC.md`,
`BUILD-PLAN.md`, `REGIME-PROMPT.md` and `HANDOFF-PROTOCOL.md` untouched. `records/` and
everything belonging to `012` untouched.

**Not committed.** `momentum-harness` untouched at `1afcecf`.
