---
id: 024
title: A subagent roster, with roles separated by tools rather than by instruction
status: READY
blocks: []
type: protocol
owner: claude-code
---

# 024 — Subagent roster: roles enforced structurally, not by instruction

**Create a small set of named subagents in `.claude/agents/`**, committed to the repo, each
with a **declared and restricted toolset**.

**The point is the restriction, not the role name.** A reviewer told not to edit will
eventually edit — it is one keystroke away and the fix always looks obvious in the moment.
**A reviewer with no `Edit` tool cannot.** That is the same construction this project uses
everywhere else: `Advisory` has no field a consumer can act on, `size_for()` cannot accept
a rule, the symbol process does not import the staging module. **The defect is made
unrepresentable rather than forbidden in prose** (`SPEC.md` §4.2a), because prose is what
this project has repeatedly learned does not hold.

**Four agents. Resist adding more.** Every agent is a context boundary and a place for
information to be lost in translation. **A roster that grows past what the work needs makes
handoffs, not throughput.**

---

## The roster

### 1. `architect` — decides shape, writes nothing

**Tools: `Read`, `Grep`, `Glob`, `WebFetch`. No `Write`, no `Edit`, no mutating `Bash`.**

Reads the spec and the tree, proposes an implementation shape, names the files and
signatures it would create, and **stops**. Its output is a plan another agent executes.

**Why the restriction earns its cost:** an architect that can write will write, and then the
plan is post-hoc narration of code that already exists. **The plan's value is that it can be
argued with before anything is built.**

### 2. `implementer` — the only agent that may mutate the tree

**Tools: `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`.**

Executes a plan. **The only agent with write access**, which makes "who changed this" answerable
without reading a transcript.

### 3. `reviewer` — finds defects, fixes none

**Tools: `Read`, `Grep`, `Glob`, `Bash`. No `Write`, no `Edit`.**

Reads a diff against the spec and reports findings. **It cannot fix what it finds**, and that
is deliberate twice over: a reviewer that fixes stops reporting, and its fixes are unreviewed
by construction.

**One rule that matters more than the tool list: the reviewer must not receive the
implementer's reasoning.** Give it the **diff and the spec section**, never the implementer's
transcript or its justification. **A reviewer handed "here is why I did it this way" reviews
the justification rather than the code**, and will agree with it — the reasoning is always
more persuasive than the diff, because it was written to be.

### 4. `test-author` — writes tests, does not touch the code under test

**Tools: `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`** — but its definition restricts it
to `tests/` and `live/tests/` paths.

**Why this is separate from the implementer, and it is the least obvious of the four:** a test
written by whoever wrote the code inherits its assumptions. It tests what the code does rather
than what the spec requires, and it passes for that reason. **This project's signature failure
is a test that goes green while the thing is wrong** — `test_no_secrets.py` passed twice with
a live key in a committed file, and `live/` shipped broken twice while staying green.

**The test author reads the spec, not the implementation.** Where it cannot tell what correct
behaviour is from the spec alone, **that is a finding about the spec** and it says so rather
than reading the code to find out.

---

## Making it structural

### The tool restriction is the mechanism

Each agent's frontmatter declares its `tools:` explicitly. **Do not omit the field and inherit
everything** — an inherited toolset is the same as no restriction, and it will be inherited
silently.

### A test asserts the restrictions hold

**Someone will add `Edit` to the reviewer "just for this one fix".** Add a test that parses
every `.claude/agents/*.md` frontmatter and asserts:

- `reviewer` and `architect` list **no** write-capable tool.
- `implementer` is the **only** agent with unrestricted write access.
- Every agent declares `tools:` explicitly rather than inheriting.

**A roster whose restrictions are not asserted is a roster of suggestions.**

### Each definition names what it may not do — and the list must match the tools

**A prohibition an agent could violate is a request.** So each definition's *"may not"* section
must be **satisfied by its tool list**, not merely stated alongside it. Where a prohibition
cannot be expressed as a missing tool — *"the reviewer must not receive the implementer's
reasoning"* — **say plainly that it is a convention and therefore weaker**, rather than letting
it sit next to the enforced ones and borrow their authority.

This is `016` part 7 and `020`'s Refusal A generalised: **a party must never be asked to
honour a constraint its own capabilities let it break.**

---

## When to use which — and when not to

**Most tasks are one agent, and that is fine.** Fan out only where the work is genuinely
independent; parallel agents editing one module cost more in conflicts than they save.

The three places this plan already names as worth splitting:

| Task shape | Agents |
|---|---|
| Behavioural tests across several modules | `test-author` × N, one per module, each writing its own new file |
| Fetch/compute plus the panel that renders it | `implementer` × 2, clean interface between them |
| Anything touching a stop level, a limit, or a size | `implementer`, then **`reviewer` on the diff** — non-optional |

**That last row is the one to hold to.** Everything that reaches position size goes through a
reviewer that did not write it and cannot fix it.

---

## Done when

- Four agent definitions exist in `.claude/agents/`, committed, each declaring `tools:`.
- The frontmatter test exists and **fails** when `Edit` is added to `reviewer` — demonstrate
  it failing before accepting that it passes.
- Each definition's *"may not"* list is satisfied by its tool list, with any convention-only
  item labelled as such.

---

## Deliverable

`handoff/done/024-for-code-subagent-roster.md`:

1. The four definitions, quoted in full.
2. **The frontmatter test going red** with `Edit` added to `reviewer`, then green without it.
3. Any prohibition you could **not** express as a missing tool, named as a convention.
4. **What you could not do**, and why. Empty is suspicious.
5. `verify.ps1` run at `<time>`.
