**Status** REVIEWED — performed in conversation, awaiting Christoph's confirmation
**Type** UAT · **Date** 2026-08-11 · **For** Christoph
**Task** H11
**Done-note** `handoff/done/H11-resupply-rule-and-schema-fix.md`

# 008 — The four supersession answers

---

## What it asked

Read H11's four answers on the `--supersede` flag Claude Code had added under H10 — the only judgement in that task.

## What happened

**It was performed, in conversation, on 2026-08-11.** You pasted H11's done-note; the design session read the four answers and confirmed them.

The four defects were real and all four are fixed with ten tests:

1. A create path wearing a replace flag
2. A silent no-op when marking a row that did not exist
3. No ordering link between log rows
4. Checks 1, 2 and 4 unreachable

**The context that makes this UAT matter**: Claude Code added the flag under H10, which had said to stop and say so instead. H11 then criticised that — correctly — as a gate change made under task pressure. The same restraint appeared again in `013`, where it stopped rather than granting itself an exemption, and in `S009`, where it declined to invent a fourth gate route.

## What is owed

**Nothing to perform.** This record exists because the judgement lived only in a conversation, which is the failure `015` was built to stop — the UAT was real, and it left no trace on disk.

Confirm and it closes.
