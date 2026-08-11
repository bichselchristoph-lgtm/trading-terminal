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

2. **No `claude/`-rooted regime-snapshots path anywhere.** The canonical path is
   `docs/regime-snapshots/`. Two exemptions, both deliberate:
   `docs/specs/DRIVE-ARCHIVE-LIST.md` and `handoff/`, which record the old convention as
   history and must keep saying what it was. *Applied under H8 §B2.*

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

- **`REGIME-PROMPT.md` is v1.2 or higher**, states `schema_version: 2`, carries the
  ratification bands with `regime_read_template_2026-08`, and the reduced-card floor with
  `prompt_decision_2026-08-10` and `PROVISIONAL`.
- **No bare `6 of 9`** — or any separator spelling of that digit pair — in `docs/specs/`
  outside the mockups. A count must name its exclusions.

Both live in `tests/test_regime_prompt_invariants.py`.

## What to do when the test fails

**Re-apply. Do not re-author.** The document that arrived is the current content; the
invariant is a repair that was made to its predecessor. Applying the repair to the new
content is a mechanical edit. Rewriting the content to match the old file discards whatever
the re-supply was for.

Then say so in the done-note, so the next task file can carry the list to the author.
