---
id: 033
title: An admin task file must name the product task it unblocks — with a test
type: admin
unblocks: none
owner: claude-code
---

**Status** WRITTEN

**If `handoff/inbox/033-for-code-the-admin-tax-has-a-test.md` exists in your tree, this is for
you. If it does not, stop reading and ignore this message.**

# 033 — The admin tax, made checkable

**This file breaks the rule it enforces, and says so.** It is admin, it unblocks no product
task, and it would fail its own test. **Christoph authorised it explicitly on 2026-08-13** as
the guard on rule 16 itself. **That authorisation is the exemption — not a pattern, not a
category.** See Part 3.

---

## Why

**On 2026-08-13 ten done-notes landed and two of them changed what the terminal does.** The
pipeline read `1 of 12 built` at both ends of the day. The design session wrote six task files,
at least two of which existed only to correct its own errors.

**Project instructions rule 16** now requires an admin task file to name the product task it
unblocks. **Today that is enforced by two people remembering.** This makes it fail.

---

## Part 1 — The rule, in its testable form

**Every task file numbered `033` or higher** in `handoff/inbox/` declares in its frontmatter:

```yaml
type: product | admin
```

- **`product`** — changes what the terminal renders, computes, or does for Christoph.
- **`admin`** — everything else.

**A file with `type: admin` must also carry:**

```yaml
unblocks: S011        # the product task this exists to make possible
```

**`unblocks` must name either a slice `SNNN`, or a task file whose own `type` is `product`.**
**An admin file naming another admin file fails.** That is the whole point — *admin unblocking
admin is how six files get written in a day.*

**Scoped by number, not by a list.** Files below `033` predate the rule and are exempt because
they were written under a convention that did not exist. **Derive the boundary from one declared
constant with the reason beside it.** *An exclusion list grows until it is a hiding place; a
positional rule does not* — the same construction `test_handoff_state_declared` uses, and the
same reason.

---

## Part 2 — Demonstrate it red, three ways

**Each of these must be seen failing before green is accepted**, using temporary fixture files
in `tmp_path`, never by editing a real inbox file:

1. A file numbered `034` with **no `type`** at all.
2. A file with `type: admin` and **no `unblocks`**.
3. A file with `type: admin` whose `unblocks` names **another admin file**.

**And one that must pass:** `type: admin`, `unblocks: S011`.

---

## Part 3 — The self-reference trap, handled deliberately

**This file would fail its own test.** `type: admin`, `unblocks: none`.

**Exempt it by id, in one line, with the reason inline** — not by a pattern, not by allowing
`unblocks: none` generally:

```python
#: 033 is the guard on rule 16 and cannot name a product task it unblocks.
#: Authorised by Christoph, 2026-08-13. EXACTLY ONE id. A second entry here is
#: a hiding place; if another file needs exempting, that is a finding about the
#: rule, not a line to add.
RULE_16_EXEMPT = frozenset({"033"})
```

**Add a test asserting `RULE_16_EXEMPT` has exactly one member.** It goes red the moment
somebody widens it, which is the only way this stays a rule rather than a habit.

**A check whose subject includes its own definition matches itself** — §7. This is that trap,
seen coming.

---

## Part 4 — One line where Claude Code will read it

`CLAUDE.md` gains a short entry: **a task file that fails this test is defective and should be
reported rather than run.** Christoph refuses it at the inbox; Claude Code refuses it at the
tree. **Two checkers, one rule, neither depending on the other noticing.**

**Do not restate rule 16 in full there.** It lives in the project instructions; `CLAUDE.md`
names the test and the consequence.

---

## Done when

- The test exists and **has been seen red on all three cases**, quoted.
- The passing case passes.
- `RULE_16_EXEMPT` has one member, and a test says so.
- `CLAUDE.md` carries the one line.

---

## Deliverable

`handoff/done/033-for-code-the-admin-tax-has-a-test.md`:

1. The three reds, quoted verbatim.
2. The exemption constant and its test, quoted.
3. **Whether any existing file numbered ≥ 033 fails** — at time of writing only this one exists.
4. **What you could not do**, and why. Empty is suspicious.
5. `verify.ps1` run at `<time>`. Do not quote its output.

---

**Work in a worktree, not the shared checkout. Remove it when the task completes.**
