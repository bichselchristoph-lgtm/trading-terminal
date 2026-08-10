H9 — Commit the specs into the repo, with a test behind the pointers
Status OPEN · Date 2026-08-10 · Type housekeeping · Blocks H8 Run this before H8. H8 edits SPEC.md; if SPEC.md is not in the tree there is nothing to edit.

Read this cold. The session that wrote it cannot answer questions and cannot see the repo.


The defect
SPEC.md, BUILD-PLAN.md and REGIME-PROMPT.md exist only in Google Drive and in a Claude project. They are not in the tree. This was discovered on 2026-08-10 when a path named in SPEC.md §5.1 — claude/regime-snapshots/ — was checked against D:\Dev\momentum-harness and found not to exist. The folder had never existed. Nobody had looked.

Why this is the expensive kind of missing. BUILD-PLAN.md §2a states the asymmetry: Claude Code sees the repo and sees "only what the task file quotes" of the spec. A spec that is not in the tree is invisible to the side that builds. Layer 0 is the priced instance of exactly this — fully specified, never built, because the spec lived only in Drive (SPEC.md §5.1). REGIME-PROMPT.md was on the same path.

This is the third application of "the read is the implementation" after CLAUDE.md's handoff convention. A pointer that lives in prose depends on someone remembering. A pointer with a test behind it does not.


Build
1. Create docs/specs/ if absent and add the four documents
docs/specs/SPEC.md

docs/specs/BUILD-PLAN.md

docs/specs/REGIME-PROMPT.md

docs/specs/DRIVE-ARCHIVE-LIST.md

Christoph supplies the file contents — they are not reachable from the repo. Do not reconstruct, paraphrase, or regenerate any of them from memory or from quotations in handoff files. If a file has not been supplied, create nothing for it, and name it in the done-note as not delivered. A plausible reconstruction of a spec is worse than an absent one: it will be read as the record.

REGIME-PROMPT.md is at v1.1 — it must contain a ### PART E — the three outputs heading and an #### E0 — the chat body subsection. If the supplied copy says "the two outputs", it is v1.0; stop and say so rather than committing it.
2. Add the pointer test
tests/test_spec_pointers.py. Two tests, no fixtures, no network.

CANONICAL_SPECS = [

    "docs/specs/SPEC.md",

    "docs/specs/BUILD-PLAN.md",

    "docs/specs/REGIME-PROMPT.md",

]

def test_canonical_specs_present() -> None: ...

def test_claude_md_pointers_resolve() -> None: ...

test_canonical_specs_present — every path in CANONICAL_SPECS exists relative to the repo root and is non-empty. Failure message names the missing path.
test_claude_md_pointers_resolve — extract every repo-relative path-shaped token from CLAUDE.md (backtick-quoted strings containing / or \ and ending in a file extension or a trailing separator) and assert each resolves on disk. Skip tokens that are explicitly marked in CLAUDE.md as obsolete, deleted, or external — D:\-absolute paths, URLs, and anything on a line containing obsolete, deleted, archived, or do not use. Failure message lists every unresolved token with its line number.

The second test is the one that matters and it is expected to go red on first run. CLAUDE.md currently marks push_all.ps1 obsolete (H2) and the root README.md names data/, signals/ and config/ trees that no longer exist (H3). Do not fix those here. Record every red pointer in the done-note with its line number; H2 and H3 own the repairs. If the exclusion rule above cannot be made to pass on legitimately-obsolete entries without also hiding real breakage, leave the test red and say so rather than widening the exclusions until it goes green.
3. Update CLAUDE.md
Add one section naming docs/specs/ as the location of record for the four documents, and stating that Drive is archive. One line that matters: a spec quoted into a task file is a copy, and the copy is authoritative for that slice only — the tree is authoritative for everything else.
4. Do not
Do not touch docs/observations/.
Do not resolve H8's path change here. SPEC.md and REGIME-PROMPT.md go in as supplied, still naming claude/regime-snapshots/. H8 changes them in the next slice, and a diff that does two things is a diff nobody reviews.
Do not archive anything in Drive. DRIVE-ARCHIVE-LIST.md §"I could not archive these for you" stands; H7 owns it.


Exit tests
Test
Who
What
Green
Claude Code
pytest passes, or test_claude_md_pointers_resolve is red with every unresolved pointer listed in the done-note. A red pointer test is an acceptable exit here; a silently-widened exclusion list is not.
Refusal
Claude Code
Rename one canonical spec in a temp copy of the tree and confirm test_canonical_specs_present fails naming that exact path — not a generic assertion error. The test must say which pointer broke.
UAT
Christoph
Open docs/specs/REGIME-PROMPT.md in the repo, confirm it reads PART E — the three outputs, and confirm git log shows the four files tracked. Then delete one and run pytest tests/test_spec_pointers.py — it should name the file you deleted. Restore it.

Done-note must state
Which of the four documents were supplied and which were not.
The version line of each supplied document.
Every unresolved CLAUDE.md pointer, with line number, and which housekeeping item owns it.
Any path-shaped token the extractor could not classify. An empty list here is suspicious — say so if the list is empty.

