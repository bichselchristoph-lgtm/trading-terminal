# RE-SUPPLY — what a document loses when it comes back from outside

> **STATUS** CURRENT · **date** 2026-08-10

## The rule

**A re-supplied document is re-repaired on landing. It is not authoritative over tree-side
edits.**

Specs are authored in the design session, which is outside this tree and cannot see it. Every
repair made here — a path substitution, a status header, a defect fix — is invisible to the
author, and the next supply of that document arrives without it.

**The failure is silent, which is why it needs a checklist rather than care.** The file is
well-formed. The adoption gate compares bytes and passes it. The regression is visible only to
someone who remembers making the edit. H10 caught it because the same session had made the
edits hours earlier; that will not hold across sessions, and it is the only reason it was
caught at all.

**This is not a reason to refuse re-supplies.** The design session is where specs are written
and that does not change. `tests/test_resupplied_docs_are_repaired.py` fails loudly instead,
and names re-supply as the likely cause so the reader does not have to work it out.

## The invariants

Every one of these was applied in the tree and would be dropped by a plain re-supply. **Quote
this list into task files that supply a document, so the author can apply them at source
instead.**

1. **Every `.md` under `docs/specs/` carries a `**STATUS**` header** — `CURRENT`,
   `SUPERSEDED` or `HISTORICAL` — as its first non-heading block, within the first 10 lines.
   A `SUPERSEDED` header additionally carries a `**by**` naming a file that exists.
   *Applied under H9 v3 §2.*

2. **No `claude/`-rooted regime-snapshots path in anything this tree READS.**
   *Applied under H8 §B2; **re-scoped to the consumer 2026-08-13**.*

   **This was "no such path anywhere", and that was wrong.** `REGIME-PROMPT.md` v1.8 uses
   `claude/regime-snapshots/` six times and is correct to: it instructs a scheduled cloud run
   which **has no repo access, permanently**, so that is genuinely where it writes. Re-applying
   the old rule would have rewritten a live task's instructions to write somewhere it cannot
   reach — a behaviour change to a running system, dressed as a mechanical repair.

   **The test is positional, not lexical: it asks who reads the path.** A consumer is a file
   this tree executes or parses — `.py`, `.ps1`, `.yaml`, `.yml`, `.json`. **Inside that set
   there are no exemptions**, because a live pointer in code is a live pointer. **Prose is
   never a consumer**: it records history, or it instructs a party that cannot see this repo.
   `tests/test_regime_snapshot_path.py::test_no_consumer_reads_the_legacy_snapshot_path`.

   The canonical path for anything **in this tree** is `docs/regime-snapshots/`.

3. **`SPEC.md` §13's heading carries the human-reachable-only qualification.** The heading
   itself, not only a note beside each citation — the Drive and OneDrive entries resolve for
   Christoph and for nothing automated, and the pointer test deliberately excludes external
   paths so it will never flag them. *Applied under H9 v3 §5.*

4. **The mockups keep their repairs.** No `tradesignals` path in any sheet — the paths are
   `D:\Dev\momentum\`. And sheets **02**, **04** and **05** each carry their
   `NOT THE CURRENT DESIGN` banner as the **first element inside `<body>`**, because each
   still renders a panel `SPEC.md` §3.1 resolves by deletion. *Applied under H9 v3 §3d.*

## Adjacent invariants, enforced elsewhere

Named here so a re-supply of `REGIME-PROMPT.md` is checked against all of them, not only the
four above:

**Amended 2026-08-13 when v1.8 landed.** Three of these asserted that v1.2's text was
*present*. v1.8 superseded all three on purpose. **They were flipped, not deleted** — the risk
was never that a new supply lacks the old text, it is that a **later** supply restores it, and
the design session cannot see what was superseded here.

- **`REGIME-PROMPT.md` is v1.8 or higher.**
- **`schema_version: 2` must NOT appear** — v1.7 bumped it to 3 because row 2 was retired and
  `layer_i` row 1 replaced. Reinstating 2 makes a v2 and a v3 snapshot indistinguishable to any
  consumer joining them. A `schema_version:` line must still be present.
- **The heading `PART E — the three outputs` must NOT appear** — v1.8 renamed it to
  `PART E — the outputs` and states the count at line 36. `PART E` and `E0` must still exist.
  `the two outputs` remains forbidden: that is v1.0.
- **Fewer than three `regime_read_template_2026-08` occurrences** — row 2 was cut in v1.7 and
  its band block went with it. A third is the retired block returning, and **`row 2` is a
  retired identifier that must never be reused.** The three bands and the reduced-card floor
  (`prompt_decision_2026-08-10`, `PROVISIONAL`) are still asserted positively.
- **No bare `6 of 9`** — or any separator spelling of that digit pair — in `docs/specs/`
  outside the mockups. A count must name its exclusions.
  **This is RED as of 2026-08-13 and is meant to be.** v1.8 reintroduced it at
  `health: "6/9 fresh"`. Ruled a real defect in the delivered text, to be fixed **at source in
  v1.9**, where the field stops being a string and becomes
  `health_fresh` / `health_total` / `health_not_fresh: [...]`. **Do not fix it tree-side** —
  that is re-authoring, and the next supply discards it.

All live in `tests/test_regime_prompt_invariants.py`.

## What to do when the test fails

**Re-apply. Do not re-author.** The document that arrived is the current content; the
invariant is a repair that was made to its predecessor. Applying the repair to the new
content is a mechanical edit. Rewriting the content to match the old file discards whatever
the re-supply was for.

Then say so in the done-note, so the next task file can carry the list to the author.
