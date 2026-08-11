# 013c — Resolution D, protocol amendments, and two new trees

**Status** DONE · **Date** 2026-08-11 · **Type** decisions applied + adoption + writes
**Runs in** `D:\Dev\momentum`. No TWS, no network, nothing under `records/`. **Safe alongside the capture.**

> Read this cold. The session that wrote it cannot answer questions.
> **This task writes.** Unlike `013a` and `013b`, it is expected to change the tree, and it **must** end with a done-note at `handoff/done/013c-*.md`. That is not in tension with any exit test here.
> **This file supersedes two earlier drafts** — `013c-resolution-d-and-christoph-tree.md` and `013c-resolution-d-and-two-trees.md`. Neither was ever started. If either is on disk, delete it; this is the only `013c`.

---

## Why

`013` stopped, correctly, on a decision it should not grant itself. That decision and five others are now made. This task applies them, adopts one new document, creates two trees, and writes four files that currently exist only in conversation.

**One instruction governs everything below.** `HANDOFF-PROTOCOL.md` is already adopted and in-tree. **Apply the amendments as edits to the file on disk. Do not re-author it, and do not accept a replacement from outside the tree.** Re-supplying a spec from the design session is the defect `RE-SUPPLY.md` exists to catch, and this task would be a textbook instance of it.

---

## Part 1 — Resolution D, the evidence-header collision

`013` offered A, B, C. **The answer is D**, which it did not consider.

**A is rejected.** Backfilling the 19 carried files means asserting a handoff state for tasks completed in another repo under a convention that did not yet exist. Those values would be inferred, and **a fabricated state is exactly what the test exists to catch.** The manifest would record a reasoned change, but the headers themselves would record a guess.

**D: a file recorded in `EVIDENCE-CARRY.md` is carried evidence, not a live handoff, and is exempt from the state-header test.**

This is not B. B scopes by authorship, which is arbitrary and would exempt the files most likely to go stale. **D scopes by a property already recorded and hash-enforced.** Absence of a header on a pre-convention file is not a defect — it is a true statement about when the file was written.

### How to implement it

**Derive the exemption from `EVIDENCE-CARRY.md` at test time. Never a hardcoded list.** A literal list is a hiding place that grows; a derived rule is not.

Add **two guard assertions**, so the exemption cannot quietly widen:

1. **Every exempted path must appear in `EVIDENCE-CARRY.md`.** If the test skips a file not in the manifest, it fails.
2. **No natively-authored file may be exempt.** A file authored in this tree can never qualify, because it was written after the convention existed. If one is found in the manifest and skipped, fail loudly with its path.

Both tests go red for the right reason if someone later adds a live task file to the manifest to silence the header test.

**Amend `HANDOFF-PROTOCOL.md` in place** to state the exemption and its two guards, so the rule does not live only in a test file.

---

## Part 2 — Five amendments to `HANDOFF-PROTOCOL.md`

Edits to the file on disk. **The wording is yours to write; the substance below is fixed.**

**2a — Rule 4 is wrong about the mechanical facts.** It says *"what the note says"* is Christoph's. It is not — once he pastes it, the design session reads the same text. **What is uniquely his is: inbox placement, whether it ran, whether a note exists on disk, and whether what reached the design session was all of it.** Not the contents.

This was proved on 2026-08-11: `012a` and `013` both wrote done-notes to `handoff/done/`, neither reached the design session, and it held a stale `RUNNING` for both. **Only Christoph could see that gap.** Record the incident as the reason.

**2b — `RUNNING` needs a definition.** `013b` flagged that `HANDED OFF` and `RUNNING` are indistinguishable on disk, and `013` asked whether a part-run task is `RUNNING` or `HANDED OFF`.

**The five states describe the handoff, not the work's internal progress. `RUNNING` means Claude Code has picked the task up and has not yet reported.** A scheduled window inside a task — a capture that starts at 09:00 ET — does not create a sixth state. `012` was correctly `RUNNING` while its capture had not begun.

**2c — The copy-and-keep convention, which nobody wrote down.** `013a` established from git history that **no file has ever been moved from `inbox/` to `done/`.** A done-note is *created* in `handoff/done/` as a new file; the inbox task file stays. Both copies exist for every completed task by design.

**State also that a done-note is a file at `handoff/done/NNN-*.md`.** `CLAUDE.md:133` is currently the only line in the repo that says so, and `HANDOFF-PROTOCOL.md` — the document adopted as the authority on handoffs — never mentions it.

**2d — States apply to done-notes too.** `013`'s own done-note declares `BLOCKED ON ONE DECISION` in its frontmatter, which is not one of the five. The test reads only the first 20 lines and did not catch it.

**Decide and record which is true:** either done-note frontmatter is outside the five-state vocabulary and may say what it likes, or it is inside and `BLOCKED` is invalid. **State it explicitly either way.** Do not extend the test's reach in this task; note what a future test would need to cover.

**2e — `handoff/done/` does not mean the task is closed.** It means **Claude Code has finished and reported.** Whether anything is still owed is a separate judgment made by Christoph and the design session together, after the note is read.

Those two facts have shared one folder until now. **Add `handoff/accepted/NNN-*.md`**: an acceptance record written only when both parties agree nothing further is owed — no open follow-ups, no unresolved issues.

- **The five states do not change.** `accepted/` is what `DONE` leaves on disk. Until today, `DONE` existed only in conversation, which is how four notes were lost on 2026-08-11.
- **Copy-and-keep applies.** Nothing moves. The inbox file, the done-note, and the acceptance record all coexist.
- **The design session authors the acceptance record; Christoph saves it.** No Claude Code round trip — the judgment is theirs, not the executor's.
- **Claude Code never writes to `handoff/accepted/`** and never infers acceptance from a note it wrote itself.

Create `handoff/accepted/` with a `.gitkeep`. **Backfill nothing** — no past task has an acceptance record, and inventing one asserts an agreement that was never made.

---

## Part 3 — Adopt `CHRISTOPH-TASKS.md`

Two files are in `D:\Dev\_adopt\`:

```
CHRISTOPH-TASKS.md
CHRISTOPH-TASKS.md.provenance.md
```

**Both design-session defects `013` found are fixed at source**: the companion uses the gate's filename convention, and carries `origin`, `source`, `reason`, `depends` as parsed fields with the prose preserved beneath.

Standard gate. A create, not a supersede. Then **create `christoph/open/` and `christoph/done/`**, empty, with `.gitkeep`.

If it lands needing a `**STATUS**` repair as `HANDOFF-PROTOCOL.md` did, **re-apply, do not re-author** — it already carries the header, but check rather than assume.

---

## Part 4 — Four files that exist only in conversation

**4a — `handoff/done/013a-handoff-tree-inventory.md`.** `013a`'s exit test forbade writing it, so its findings live only in chat. **Reconstruct it from your own `013a` report** — the five items, the unchanged-tree proof, the hashes. Do not re-derive the findings by re-running anything.

Add one finding settled afterwards: **H9a's task file never existed, and its instructions are unrecoverable.** `docs/PROVENANCE.md` and H9a's own done-note survive, but what H9a actually asked for is gone from both repos and from project artifacts. **If anyone later asks whether the 183-file inventory answered the question it was set, there is no way to check.** A closed gap, recorded because it cannot be reopened.

Also correct `handoff/inbox/013a-*.md`'s header, which still says `WRITTEN`. It is `DONE`.

**4b — `handoff/done/013b-state-reconciliation.md`.** Same defect, same cause: `013b`'s task file said *report in chat, write nothing including no done-note*, so its findings are also chat-only. **That instruction was a design-session error** — it removed a contradiction by removing the artifact, and it is why two of the four notes lost today were lost.

**Reconstruct from your own `013b` report**: the per-row reconciliation, the 21 omitted items, the four contradicting headers, the `git cat-file -e HEAD:` correction to your own method, the unchanged-tree proof, and the observation-versus-inference split. Do not re-run anything to re-derive it.

**4c — `christoph/open/001-ibkr-totalview-api-entitlement.md`.** Type `EXTERNAL`. The question: **why does an account holding NASDAQ TotalView-OpenView receive code 10089 — "requires additional subscription for API" — on `NASDAQ.NMS/DEEP`?** Both `ISLAND` and `NASDAQ` return byte-identical messages naming the same feed, so they are one route rather than two. The API-vs-TWS entitlement distinction that the "for API" wording points at is the place to look. **Quote `012a`'s literal message.** Not blocking; it matters only if QQQ's primary book is wanted for a later capture.

**4d — `christoph/done/002-handoff-protocol-rule-4-uat.md`.** Type `UAT`, already answered. Christoph read rule 4 and confirmed it matches what he meant, **with one correction — the mechanical-facts list, applied in part 2a.** Record the question, the answer, and the correction it produced.

---

## Part 5 — Two corrections and one read

**5a — `013`'s depth-budget premise is wrong, and it came from this design session.** `013` frames depth as "the expensive line" for tomorrow's multi-ticker run. Christoph pays the full North America subscription set monthly, **so depth costs nothing at the margin and does not scale with ticker count. The constraint is line count, not money.** Correct it wherever it appears in `handoff/`, and state the correction in the done-note so tomorrow's task is not written against it.

**5b — companion naming, the design session's defect.** `013` found the design session uses `X.provenance.md` while the gate expects `X.md.provenance.md`, and that the four parsed fields were missing. **Fixed at source from this task onward.** Nothing to change in-tree; note it as closed.

**5c — read the two non-task files and report.** `handoff/inbox/condition-codes-config-is-unverified.md` and `handoff/inbox/separation-guard-inactive-on-official-venues.md`. Neither Christoph nor the design session has read them; they are two filenames in a listing.

**Report what each says and whether it names anything unresolved.** `condition-codes-config-is-unverified` matters most: `condition_codes.yaml` is authored, `docs/PROVENANCE.md` established its vocabulary was invented by this codebase, and it was flagged for rewriting.

**Do not move, edit, or re-file them** — they are carried evidence and inside the manifest. **Do not act on anything they contain.** Report only; Christoph decides with the contents in front of him.

---

## Do not

- Do not re-author `HANDOFF-PROTOCOL.md` or accept a replacement from outside the tree.
- Do not weaken `test_handoff_state_declared` or hardcode any exemption list.
- Do not modify any file recorded in `EVIDENCE-CARRY.md`, or re-record any hash.
- Do not write anything into `handoff/accepted/` beyond `.gitkeep`, and do not backfill it.
- Do not touch `records/`, the capture, `tools/capture_tape.py`, or open a TWS connection.
- Do not modify `SPEC.md`, `REGIME-PROMPT.md`, or `BUILD-PLAN.md`.
- Do not add a sixth state.
- Do not act on anything found in the two files read under 5c.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full `pytest`. **The tree was `65 passed, 0 failed` before `013`** — that is the baseline, not the figure of 8 this design session wrongly carried over from `momentum-harness`. `test_handoff_state_declared` passes with the 19 carried files exempt and both guards green. |
| **Refusal A** | Claude Code | Add a path to `EVIDENCE-CARRY.md` that is a natively-authored live task file. Confirm guard 2 fails and names it. Revert. |
| **Refusal B** | Claude Code | Make the test skip a file absent from the manifest. Confirm guard 1 fails. Revert. |
| **Refusal C** | Claude Code | Confirm a temp task file with no header still fails, and that resolution D did not widen into a general escape. |
| **UAT** | Christoph | Read `christoph/open/001` and confirm the IBKR question is one you can actually put to them as written. |

## Done-note must state

- The exemption rule, quoted from the test, and both guard assertions.
- What changed in `HANDOFF-PROTOCOL.md`, per amendment, quoted.
- **Your ruling on 2d**, and what a future test would need to cover it.
- The `ADOPTION-LOG.md` row for `CHRISTOPH-TASKS.md`, and whether a `**STATUS**` repair was needed.
- **The contents of both files read under 5c, and whether either names unresolved work.**
- Every file created, with its path, including both new trees.
- **Anything in this task that diverged from what was on disk** — `013` found four such divergences and every one mattered.
