---
id: H9
title: Commit the specs into the repo, with a test behind the pointers
status: DONE — exiting with test_claude_md_pointers_resolve RED, which H9 permits
type: housekeeping
owner: claude-code
ran: 2026-08-10
tree: D:\Dev\momentum
---

# H9 — Commit the specs into the repo

**All four canonical documents are in the tree.** Thirteen files adopted through the gate,
each with a provenance companion and an `ADOPTION-LOG.md` row. Tree is at **52 tracked
files**.

```
1 failed, 28 passed in 0.50s
```

The one failure is `test_claude_md_pointers_resolve`, red on four pointers. **H9 names this
as an acceptable exit** — *"A red pointer test is an acceptable exit here; a silently-widened
exclusion list is not."* Every red pointer is listed below.

## §1 — The four documents, and the version of each

| document | version line | supplied |
|---|---|---|
| `SPEC.md` | **Version 1.1 · 2026-08-09 · Status DRAFT FOR APPROVAL** | yes |
| `BUILD-PLAN.md` | **Version 1.1 · 2026-08-09 · Companion to `SPEC.md`** | yes |
| `REGIME-PROMPT.md` | **Version 1.1 · 2026-08-10 · Companion to `SPEC.md` §3.2, §5.5a** | yes |
| `DRIVE-ARCHIVE-LIST.md` | **no version line** | yes |

**All four were supplied. None was reconstructed.** Three more arrived alongside them, and
none of those carries a version line either: `REPO_CONSOLIDATION_PLAN.md`, `USE_GUIDE.md`,
`layer0-amendment-2-frozen-vs-live.md`.

### The `REGIME-PROMPT.md` version gate passed

H9 says to stop rather than commit a v1.0 copy. Checked before adopting anything:

- `### PART E — the three outputs` present at **line 164**
- `#### E0 — the chat body` present at **line 166**
- the string "the two outputs" appears **nowhere** in the file

It is v1.1. `tests/test_spec_pointers.py::test_regime_prompt_is_v1_1_not_v1_0` now pins all
three conditions, so a later re-supply cannot silently downgrade it.

## Adoption — thirteen files, not seven

You named **seven items** in `D:\Dev\_adopt\`. There were seven `.md` files plus a
`mockups/` **directory** holding six files, so the gate ran **thirteen times** — one
companion and one log row per file, because refusal 1 is per-candidate and a directory has no
provenance of its own.

**Two populations, cited differently, and the difference is the whole point.**

**Four canonical specs have no `PROVENANCE.md` row**, and that absence *is* the citation.
They have never existed in `momentum-harness`; H9a inventoried that repository at 77 commits,
so it has no row for them. They came from Drive, supplied directly. Each companion says so in
those words. **Inventing a row would have been worse than the absence** — it would have made
a fabricated provenance look inventoried.

**Nine files carried forward do have rows** — all `authored`, and every one **byte-identical**
to the old repo's copy, verified by sha256 before adoption:

| file | PROVENANCE row | identical |
|---|---|---|
| `REPO_CONSOLIDATION_PLAN.md` | authored, refs=3 | yes |
| `USE_GUIDE.md` | authored, **refs=0** | yes |
| `layer0-amendment-2-frozen-vs-live.md` | authored, refs=1 | yes |
| `mockups/mockup-01-ingest.html` | authored, refs=3 | yes |
| `mockups/mockup-02-regime.html` | authored, refs=5 | yes |
| `mockups/mockup-03-watchlist.html` | authored, refs=4 | yes |
| `mockups/mockup-04-size-stage.html` | authored, refs=2 | yes |
| `mockups/mockup-05-live-context.html` | authored, refs=1 | yes |
| `mockups/mockup-README.md` | authored, refs=1 | yes |

`USE_GUIDE.md` is adopted **with its caveat on the record**: `refs=0` means nothing in the old
tree referenced it. It is adopted as documentation of record, not as a dependency.

All thirteen were dry-run with `--check` first; all thirteen reported `PASSES all four
refusals` before any file moved. No candidate was refused.

## §2 — The pointer test

`tests/test_spec_pointers.py`, four tests, no fixtures, no network.

`test_canonical_specs_present` — **Refusal exit test passed.** Renaming
`docs/specs/BUILD-PLAN.md` produced:

```
AssertionError: canonical spec missing: docs/specs/BUILD-PLAN.md. It is not in
the tree, which means it is invisible to the side that builds.
```

It names the exact path, not a generic assertion error. Restored afterwards.

### Every unresolved pointer, with line number and owner

```
CLAUDE.md:38  `core/`
CLAUDE.md:38  `live/`
CLAUDE.md:38  `harness/`
CLAUDE.md:71  `live/tests/`
```

**All four are forward references, and all four are correct prose.** Line 38 is refusal 2's
row — "nothing enters `core/`, `live/`, `harness/` or `tools/` without a behavioural test" —
naming directories that **do not exist yet because nothing has been adopted into them**. Line
71 explains why `pytest.ini` lists `live/tests/`.

**Owner: the first adoption into each tree clears it.** There is no repair to make now; the
pointers are right and the directories are pending. Note that `tools/` resolves — `adopt.py`
lives there — which is why only three of the four names on line 38 are red. That asymmetry is
the test working: it distinguishes a directory that exists from one that does not, which is
exactly the distinction that would catch a genuinely wrong pointer later.

**I did not widen the exclusion list to reach green.**

### Two red pointers I did repair, because they were real defects

The test caught two genuine errors in the `CLAUDE.md` I wrote for M001:

1. **`CLAUDE.md:107` claimed chat "sees only the Drive sync of `docs/`, `notes/` and
   `handoff/`".** **Drive sync was removed 2026-08-09.** That sentence was stale on the day it
   was written and asserted a channel that no longer exists. Rewritten: chat has no file sync
   of any kind, and **Christoph is the only channel between the two halves** — which makes
   writing things down more important, not less, because a file is what he can carry. The
   same stale claim appeared again lower down and was also fixed.
2. **`CLAUDE.md:120` wrote `done/` as a bare fragment** where it meant `handoff/done/`.

Neither was found by reading. Both were found by the test, on its first run.

### Path-shaped tokens the extractor could not classify

H9 requires this list and warns that an empty one is suspicious. **It is not empty — six:**

```
CLAUDE.md:116  `handoff/inbox/NNN-*.md`
CLAUDE.md:117  `handoff/done/NNN-*.md`
CLAUDE.md:118  `handoff/questions/*.md`
CLAUDE.md:119  `docs/observations/*.md`
CLAUDE.md:120  `handoff/*.md`
CLAUDE.md:126  `handoff/done/NNN-*.md`
```

All six contain a wildcard. **A glob is a naming convention, not a pointer** — no single path
can satisfy `NNN-*.md`, so "does it resolve" is not a question it can answer. They are
reported rather than dropped, because an unexamined "could not classify" pile is exactly
where real breakage goes to hide. The test prints this bucket on every run.

This is a classification, not an exclusion: the test is **still red** on the four genuine
pointers, so nothing was silenced to reach green.

## §3 — CLAUDE.md updated

`docs/specs/` is named as the location of record for the four documents, with the line that
matters: **a spec quoted into a task file is a copy, authoritative for that slice only; the
tree is authoritative for everything else.** Drive is archive — the sync is gone, so its
copies cannot drift back in.

## §4 — Do-not list honoured

| prohibition | status |
|---|---|
| Do not touch `docs/observations/` | not touched — it does not exist in this tree yet |
| Do not resolve H8's path change | not resolved. `SPEC.md` and `REGIME-PROMPT.md` went in **as supplied**, still naming `claude/regime-snapshots/`. H8 owns it; a diff that does two things is a diff nobody reviews |
| Do not archive anything in Drive | nothing archived. H7 owns it |
| Do not reconstruct any document | none reconstructed. All four supplied |

## One tightening, unprompted

**`docs/specs/` has been removed from `NATIVE_PREFIXES`** in
`tests/test_adoption_log_complete.py`. I added that carve-out during M001 assuming specs
would be authored in this tree. They turned out to be **adopted**, and all thirteen carry log
rows — so the carve-out was buying nothing while costing the gate its reach over the
directory that now holds the system's most load-bearing documents.

**The gate immediately caught me with it.** Removing the carve-out turned
`test_adoption_log_complete` red on `tests/test_spec_pointers.py` — the file I had just
written by hand. It is now in `BOOTSTRAP_ALLOWLIST` with a comment saying why. The failure
message says adding an entry there "should feel like a decision", and it did.

`handoff/` and `docs/observations/` keep the carve-out: they hold prose authored here, and
`test_no_code_tree_is_native` still fails if it ever reaches a code tree.

## What this unblocks, and what it does not

**Unblocked.** `SPEC.md` is readable from the repo for the first time. Three things that were
previously blocked on it:

- **Task `005`** can now be triaged properly — its supersession premise is `SPEC.md` §3.2,
  which I could not read during M001 and therefore refused to act on.
- **The `BUILD-PLAN.md` §3 slice-008 collision** can now be reported from the document rather
  than relayed from M001's claim about it.
- **H8** has something to edit. H9 blocks H8, and that block is lifted.

**Not done, deliberately.** H8's change to `claude/regime-snapshots/` is untouched.

**Still open, unchanged.** The 41 adoption decisions from H9a — 37 `imported`, 4 `unknown`
— remain yours. Nothing in H9 touched them; all thirteen files here were `authored`, which is
why none needed a `decision:` line.
