---
id: 053
title: The ledger ruling, and connecting the mechanisms that were specified and never wired
type: task
class: admin
version: 3.0
originates: 044-q1 · project instructions §4 the verification gate · rules 7, 21 and 22
closes: B-030 · B-027
answers: 044-q1
unblocks: the REVIEWED state for 049, 050 and 051 — Part 2. And Part 6, without which no reissued task file can ever reach the tree.
depends: none
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 053 — the ledger ruling, and the mechanisms that were never wired

**Type: task. Class: admin.**

**v3.0 is the last version of this file.** If a correction is needed after this, **it gets a new
number** — which is Part 6's whole subject.

**The through-line: every part is a mechanism specified in a document and never connected to
anything.** That pattern has fired five times in two days. **Part 5 makes it detectable rather than
discovered.**

---

## Addressing

**If `handoff/inbox/053-for-code-task-ledger-ruling-and-verify-export.md` exists in your tree and
`handoff/done/053-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Scratch in `$env:TEMP`, never the repo.**

---

## Read this before anything else

**The design session reissued `049`, `050`, `052` and `053` under the same filenames, repeatedly.**

**`handoff/` is copy-and-keep. The inbound copier's rule is: present and differing ⇒ do not
overwrite, report and stop.** So **once any version reached the tree, no later version could arrive.**
It refused, exited 1, and looked exactly like the 040/043 refusals standing since `045`.

**So the version of a task you executed may not be the version that exists in Drive.** Specifically:
**`052` was probably run at v3.0, whose Parts 2 and 3 were later withdrawn and which lacked the
worktree isolation ruling.**

**That is the design session's defect, not yours.** The rule broken is one it wrote: *a correction
arrives as a new task, never as an amendment.* **It applied the Google Docs convention — where
replacement in place is correct — inside the one system where it is forbidden.**

**Do not resolve any of those conflicts by overwriting. Report them by name.**

---

## Part 1 — the ruling on `044-q1`

**Apply the reason, not the rule. `021`'s three rows move forward. `037`'s rows keep `OBS-044`,
`OBS-045` and `OBS-046`.**

**`044`'s rule — *the earlier allocation keeps the number* — was never the goal.** It was a means to
**do not change what an exported done-note appears to have said**, and it was written under a false
belief about which set was earlier. You established from git that `021`'s rows came first.

**When a means and its end separate, the end is the durable half.**

**The arithmetic settles it.** The letter retargets **twenty citations across nine exported files**;
the reason breaks nothing, since **`021`'s done-note cites none of the three.**

**You were right to stop.** `044`'s own clause — *if any reallocation would change what an exported
done-note appears to have said, stop and report* — **is triggered by the literal reading. That is the
clause working, not the task failing.**

### What to do

**Reallocate `021`'s three rows forward.** **Read the next free ids from the ledger at execution
time.** **Do not use `OBS-065`–`067` from the question file** — those are ids as of that file's world,
read two days ago. **The question was right about the action and cannot be right about the numbers.**

**If `021`'s done-note turns out to cite any of them, stop and report** rather than editing an
exported file.

**`tests/test_observation_ids_are_unique.py` goes green because the duplication is gone**, not
because the test was weakened. **It must not become `xfail`.** Confirm red before, green after.

**And correct the count: three duplicated ids, not five.** `B-030` repeats `044`'s wrong number —
taken from the task file rather than the ledger.

---

## Part 2 — `verify-output.txt` is written where nothing exports it

**`verify.ps1` writes it at the repository root. The outbound pair exports `handoff/`,
`christoph/done/` and `handoff/questions/`. The root is not among them.**

**So `REVIEWED` has never been reachable by its own definition.** Every report has arrived by
Christoph pasting terminal output into chat — **the exact thing the protocol forbids:** *nothing
exists only in a terminal.*

**Write it to `handoff/verify-output.txt`.** One path change, no new pair — **a copier is configured,
never duplicated.**

**Then run `verify.ps1`, then the export, then confirm it appears in the export manifest.** **Confirm
by reading the manifest, not by reasoning about the config.**

**`export-run-record.md` and `sync-run-record.md` stay at the root.** They sit outside every source
and destination **because a record that only exists where the copy lands cannot report failing to
reach there.** **Report only** whether the design session can see them without a bridge, and if not,
what content signal could travel instead. *A count that self-clears, never a clock.*

---

## Part 3 — a task file may not state where output goes

**Routing is protocol. A task file says what to produce; the protocol alone says where it lands.**

**`044` told you to paste a question into chat. The questions channel already existed**, specified
about 150,000 characters earlier in the same session. **The design session routed around its own
mechanism, toward the place it happens to read, and the cost landed on Christoph.**

**Add to `CLAUDE.md`:**

```
ROUTING IS PROTOCOL, NOT TASK CONTENT.

A task file states what to produce — a done-note, a question file, a bug row.
It does not state where output goes. Destinations come from config/sync.yaml
and the handoff protocol, never from task prose.

If a task file names a destination, that is a finding. Report it and use the
protocol path. A task file is authoritative about its own work and is not
authoritative about the channel.
```

**Do not build a lint for this.** Grepping prose for destinations is unbounded — **a check that
catches four phrasings and misses the fifth is worse than none, because it would be trusted.**

---

## Part 4 — bug findings become structured data

**There is no path from a bug you find to the tracker.** You write prose; the design session retypes
the sheet by hand. **All 88 rows exist because they were typed.**

**Every done-note carries a `bugs:` block in frontmatter**, present and possibly empty:

```yaml
bugs:
  - id: B-030
    action: correct
    status: NEW
    note: count is three, not five — taken from the task file rather than the ledger
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: verify-output.txt written outside every exported path
    spec: PROCESS-SPEC
    summary: ...
    actual: ...
    expected: ...
```

**`id: NEW` for a row that does not exist yet. You do not allocate `B-NNN`** — the design session
holds the sheet and allocates on rebuild. **Allocating from your side would be a number inferred
rather than read**, which is what produced five duplicate ledger ids.

**`bugs: []` when there are none. An empty block and a missing block must not look alike.**

**Generate done-note and question destinations from `config/sync.yaml`** rather than reading them from
task text. **That is what makes Part 3 positional rather than remembered.**

---

## Part 5 — the tests

**Each seen RED before accepted green.** **A green suite over an unreachable feature is this
project's oldest recorded defect, and a policy test is exactly the kind that passes because it never
looked.**

| # | Test | Catches | Expected today |
|---|---|---|---|
| **1** | Every artifact in `config/outputs.yaml` is inside a path `config/sync.yaml` exports | **Part 2, and the next instance rather than only this one** | **RED** |
| **2** | Done-note frontmatter parses; `bugs:` present; entries have `id`, `action`, `status`; `id` is `B-NNN` or `NEW` | Part 4 | RED |
| **3** | Task file has an addressing gate, a `class`, an `unblocks:` when admin, **and no destination field** | Part 3 | unknown |
| **4** | Observation ids unique across the ledger | Part 1 | **already red** |
| **5** | **The inbound run record reports zero content conflicts, by name** | **Part 6** | **RED — 040, 043, and the reissues** |
| **6** | **One task id, one file in `handoff/inbox/`** | **B-027** | **RED — `035` has two** |

**Test 1 needs the declared outputs to be data.** Add `config/outputs.yaml` listing each artifact the
protocol says must travel and what produces it. **Prose cannot be tested; a list can.**

**No allowlist on tests 5 or 6.** **An allowlist for known conflicts is how a red test becomes
furniture** — and 040 and 043 have been furniture since `045`.

**All of these run in the normal suite that `verify.ps1` executes. Do not add a write-time hook** — a
check invoked by the writer is the self-reference trap, since the session that skips writing the note
also skips the check.

**Nothing can verify what was printed to a terminal.** A test sees files. **The only enforceable
version is that the file exists and is well-formed.**

---

## Part 6 — the allocation log, and the two standing conflicts

### 6a — an append-only allocation log

**`handoff/ALLOCATIONS.md`, one line per task number, never rewritten:**

```
049  2026-08-15  validate the owned corpus
050  2026-08-15  the tape window
051  2026-08-15  the basis audit
052  2026-08-16  product-spec pointer
053  2026-08-16  ledger ruling and the unwired mechanisms
```

**Not a counter.** **A counter is a cached count and can be wrong; a log can only be incomplete, and
incompleteness shows as a gap.** Reading the last line is an observation about a record of events,
not a claim about a total.

**Seed it from `handoff/inbox/`, `handoff/done/` and git history**, and **report every number that
appears more than once or not at all.**

**Be honest about its limit:** it makes allocation cheap; **it would not have prevented the reissues,
because the design session was not allocating — it thought it was replacing a document.**

### 6b — resolve or rule on 040 and 043

**Test 5 cannot go green while they stand, and a permanently red test has stopped carrying
information.**

**They have differed between Drive and the tree since `045` §5 and `046` §9.4 and nobody has owned
them since.** **Report what differs — bytes, or content, and which side is newer.** **Do not
overwrite either.**

**If the difference is only the reissue defect, say so and the design session retires the Drive
copy.** **If it is a genuine divergence, that is a finding and it stops here.**

### 6c — the `035` collision

**Two different files share the number.** **The addressing gate globs `handoff/inbox/NNN-*.md`, so
both match and the gate cannot tell them apart** — B-027.

**Report both filenames and what each contains. Do not renumber either.** Renumbering is an
allocation, and allocation is read from the log, which does not exist until 6a.

---

## Then set the question ANSWERED

**`044-q1` moves to `ANSWERED` in `handoff/questions/`**, citing this task.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. **Then run the export, from the main checkout.**

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | Tests 1–4 **seen red first**, then green. **Tests 5 and 6 stay red and that is the correct outcome** — they are red about defects this task reports rather than fixes |
| **Refusal** | Claude Code | **An output declared in `config/outputs.yaml` but not covered by a sync pair fails test 1 loudly, never warns.** And **a reallocation that would change what an exported done-note appears to have said still stops and reports** |
| **UAT** | Christoph | None |

---

## Report

1. **Which ids `021`'s three rows received**, read from the ledger, with the read quoted.
2. **Where `verify-output.txt` now lands, and whether it appeared in the export manifest** — confirmed
   by reading the manifest.
3. **Whether the run records are reachable without a bridge.** Report only.
4. **What `config/outputs.yaml` lists, and whether anything else in it was already unexported.**
   **That list is the answer to *how many more of these are there.***
5. **Tests 1–4 red before, green after. Tests 5 and 6 red, with their contents named.**
6. **`ALLOCATIONS.md` as seeded**, and **every number appearing twice or not at all.**
7. **What differs between Drive and the tree for 040 and 043**, and which side is newer.
8. **Both `035` filenames and what each contains.**
9. **Which version of `052` you actually executed** — check whether the committed `SPEC.md` header
   says *"Start at SPEC-INDEX"* (v3.0) or *"Start at 01 SPEC-INDEX"* with numbering (v4.0).
10. **Your `bugs:` block.** At minimum: B-030 correction · the unexported `verify-output.txt` · the
    worktree guard blocking all writes · `mockup-06` missing from 052's mapping table · **the reissue
    defect itself.**
11. **What you could not do**, and why. Empty is suspicious.
