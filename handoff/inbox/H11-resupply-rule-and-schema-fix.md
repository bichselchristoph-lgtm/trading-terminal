# H11 — The re-supply rule, `SPEC.md` §5.5a, and a review of the gate change

**Status** DONE · **Date** 2026-08-10 · **Type** spec + test
**Runs in** `D:\Dev\momentum`. Follows H10.

> Read this cold. The session that wrote it cannot answer questions.

---

## 1. The re-supply rule — the finding H10 surfaced

H10's done-note records it plainly: v1.2 *"was authored before two decisions landed: 5 legacy `claude/regime-snapshots/` paths and no status header. Both re-applied. Worth treating as a pattern — any document re-supplied from outside arrives pre-repair and silently undoes work done here."*

**This is structural and it will recur on every spec revision.** The design session authors documents outside the tree and cannot see it. Every tree-side repair — path substitutions, status headers, defect fixes — is invisible to the author and gets overwritten on the next supply. **It is silent: the file arrives well-formed, the gate passes it on bytes, and the regression is only visible to whoever remembers making the edit.** H10 caught it because the same session had made the edits hours earlier. That will not hold across sessions.

### Build

**`tests/test_respupplied_docs_are_repaired.py`** — for every `.md` under `docs/specs/`, assert the tree-side invariants that a re-supply would drop:

1. A `**STATUS**` header with a valid value. *(Already covered by `test_every_spec_declares_status`; assert here too so a single test names the re-supply cause in its failure message.)*
2. No `claude/regime-snapshots/` outside the two exemptions. *(Covered by `test_no_legacy_regime_snapshot_path`; same reasoning.)*
3. For `SPEC.md`: §13's heading carries the human-reachable-only qualification.
4. For the mockups: no `tradesignals` path, and the three bannered sheets still carry their banner as the first element inside `<body>`.

**Failure message must name the likely cause**, in these words or close: *this invariant was applied in the tree and is absent — the file was probably re-supplied from outside and arrived pre-repair. Re-apply, do not re-author.*

**Add `docs/specs/RE-SUPPLY.md`**, status `CURRENT`: the list of invariants above, and the instruction that a re-supplied document is **re-repaired on landing, not treated as authoritative over tree-side edits.** Cite it from `CLAUDE.md`. **The design session must be told which invariants exist** — record in the done-note the exact list, so it can be quoted back into future task files rather than rediscovered.

**Do not solve this by refusing re-supplies.** The design session is where specs are written and that does not change. The repair is a checklist that fails loudly, not a closed door.

---

## 2. `SPEC.md` §5.5a — the spec rejects its own example

H10 found and correctly did not fix it: §5.5a's worked YAML reads `schema_version: 1` while `REGIME-PROMPT.md` v1.2 emits `2`, and the same section says a version mismatch means refuse to parse. **The spec's own example describes a snapshot the spec would reject.** It also omits the `ratification` keys v1.2 now writes.

### Build

1. §5.5a's example block → `schema_version: 2`.
2. Add the `ratification` keys v1.2 emits: `rows_available`, `floor_fired`, `bands`, `bands_source`, `floor_source`.
3. **Add one line stating why the version moved**, naming v1.2's reduced-card floor. A bump with no recorded cause is one nobody can evaluate later.
4. §3.2's `regime_snapshot: {ref, frozen_at, schema_version}` pointer is unchanged — check it, do not edit it.

**Do not change §5.5a's four properties, the frozen-`frozen_at` rule, or the refuse-on-mismatch rule.** The mismatch rule is correct; the example was stale against it.

**One thing to check while in there.** §5.5a's example predates v1.2 by more than the version field — compare it key-for-key against v1.2's PART E2 block and report every difference, not only the two named above. A spec example that drifts from the producer is how a consumer gets written against a shape that was never emitted.

---

## 3. The `6 of 9` test — the spelling gap

H10's fix is right: the string necessarily appears in v1.2 in the passage forbidding it, so the test allows a citation and catches a bare count, with a test proving the allowance is not taken on trust. Scope was widened past one file, correctly — the figure made three document hops and a per-file check would have caught none of them.

**The gap H10 named: `mockup-02` renders `6 / 9`, a different spelling the test does not catch.**

### Build

Normalise before matching: collapse whitespace, treat `/`, ` / `, ` of `, and `of` as the same separator, and match the digit pair rather than the literal string. **Then re-run against the whole tree and report every hit**, including ones the current test passes.

**This is the fourth hop being prevented, so state the general form in the failure message**: a count that does not name its exclusions cannot be checked, whatever separator it is spelled with.

**Do not repair `mockup-02`.** It is bannered `HISTORICAL` and the redraw owns it. **The test should therefore exempt `docs/specs/mockups/` and say so with a reason** — the mockups are frozen historical artifacts, not live specification. Record in the done-note that the exemption is what stands between `6 / 9` and a fourth hop, so the redraw inherits that as a named obligation rather than finding it later.

---

## 4. Review the supersession flag — by something other than the session that wanted it

H10 added `--as` and `--supersede` to the adoption tool after refusal 3 blocked a legitimate version replacement. H10's instruction was to **stop and say so** if no supersession path existed. That instruction was not followed, and the reason it existed is that the session needing the exemption is not the one that should grant it.

**The change may well be right.** It requires an explicit flag, a `supersedes:` line in the companion, and agreement between them — three conditions, not a bypass. Both log rows survive and v1.1 is marked `SUPERSEDED`. This task does not ask for a revert.

### Build

**Read the nine lines fresh, as though reviewing someone else's change, and answer four questions in the done-note:**

1. Can `--supersede` land a file at a path that has **no** existing adoption? If yes, it is a create path wearing a replace flag.
2. Does it verify the superseded row exists and is not already superseded? A chain of supersessions with a gap in it is unreadable.
3. Does `ADOPTION-LOG.md` record enough to reconstruct the order? Two rows are not a sequence unless one points at the other.
4. Would refusals 1, 2 and 4 still fire on a `--supersede` adoption, or does the flag shortcut any of them?

**Add a test for whichever of the four has no test.** The tool now has a path that was added under pressure to complete a task, which is exactly the kind of code that needs a test written when nobody is in a hurry.

**Also fix the `ADOPTED ->` message bug** H10 found — it printed the candidate name while writing the landed one. H10 was right that a lying message is the worse of the two failures: a wrong copy is visible in the tree, a wrong message is believed.

---

## Do not

- Do not revert `--supersede`. Review it.
- Do not repair the mockups.
- Do not re-author any spec content. Every edit here is a repair to an existing document.
- Do not push either repo. `momentum-harness` stays at `1afcecf`.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | `pytest` passes. Report before and after. |
| **Refusal** | Claude Code | Two. (a) Overwrite `docs/specs/SPEC.md` with a copy that has no §13 qualification; confirm the re-supply test fails **naming re-supply as the likely cause**, not just the missing string. Restore. (b) Write a scratch file containing `6 / 9` with slash spacing; confirm the normalised test catches it. Remove. |
| **UAT** | Christoph | Read the four supersession answers. **They are the only part of this that is a judgement rather than a repair.** |

## Done-note must state

- The full invariant list from `RE-SUPPLY.md`, verbatim, so it can be quoted into future task files.
- Every key-for-key difference between §5.5a's example and v1.2's PART E2, not only the two named.
- Every `6 of 9` / `6 / 9` hit under normalisation, with the mockup exemption named as an obligation on the redraw.
- The four supersession answers, and which of them gained a test.
- Whether anything else in the tree was authored outside it and could arrive pre-repair on a future supply.
