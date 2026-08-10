# H8 — Freeze the regime snapshot path, and get the snapshots onto disk

**Status** OPEN · **Date** 2026-08-10 · **Type** housekeeping · **Depends on** H9
**Two halves.** §A is Christoph's, outside the repo, and **must be done first**. §B is Claude Code's.

> Read this cold. The session that wrote it cannot answer questions and cannot see the repo.

---

## The defect

Two separate faults that look like one.

**1. Five naming conventions for one artifact.** `DRIVE-ARCHIVE-LIST.md` lists them: `regime_snapshot_YYYY-MM-DD.md`, `Daily Market Regime Read — DATE`, `Regime Snapshot Month DD YYYY`, `regime_read_YYYY-MM-DD`, `Regime Read — YYYY-MM-DD`. This is the original H8.

**2. The frozen convention points at a folder that does not exist.** `SPEC.md` §3.2 and §5.1 and `REGIME-PROMPT.md` all name `claude/regime-snapshots/YYYY-MM-DD.{md,yaml}`. Verified against `D:\Dev\momentum-harness` on 2026-08-10: **there is no `claude\` directory.** The scheduled task runs as a cloud session and writes to that session's own filesystem, not to D:. Every snapshot written so far is off-disk.

**Why it matters beyond tidiness.** `SPEC.md` §5.1 has the terminal link to today's file and render `[ NOT BUILT ]` when absent. Against this disk it renders `[ NOT BUILT ]` every single day — a refusal state firing correctly, for a reason nobody would guess from the screen. And §5.5a's whole argument for shipping YAML from day one is the eventual join to the trade log on `session_date`. **A snapshot that never reaches the machine holding the trade log cannot be joined to it**, so the capture that "began this morning" (`BUILD-PLAN.md` §2) is currently capturing into a place with no consumer.

**Why not `claude/`.** It sorts adjacent to `.claude/`, differs by one character, and one of the two is untracked config holding a plaintext Databento key (`SPEC.md` §9, H1). Two directories that look identical in a listing, with opposite tracking rules, is a trap worth three path edits to avoid.

**Frozen convention, final:**

```
docs/regime-snapshots/YYYY-MM-DD.md
docs/regime-snapshots/YYYY-MM-DD.yaml
```

---

## §A — Christoph, before §B

**A1. Determine whether a local Claude Code Desktop scheduled task can reach the IBKR connector.** Everything quoted in `REGIME-PROMPT.md` PART A–D comes from it: `get_price_snapshot`, `get_price_history`, `search_contracts`.

- **If yes** — move the task from cloud to a local Desktop scheduled task with the folder set to `D:\Dev\momentum-harness`. The relative path then resolves against the repo and the files land on disk. The reliability cost of local tasks (machine awake, app open) is small here: **05:00 ET is 11:00 in Cape Town.**
- **If no** — the task stays in the cloud and **§B still ships**, but the snapshots do not arrive on their own. Say so in the reply; the fallback (manual save, or a sync path) is a separate decision and is not in this task file. Do not let §B's green tests imply the pipeline works end to end.

**A2. Paste the v1.1 prompt** into whichever task ends up running, with the two paths updated to `docs/regime-snapshots/`.

**A3. Run it once with "Run now" and confirm the response body opens with the one-paragraph read**, not a confirmation line. That is the Amendment 3 (E0) acceptance and it is independent of everything in §B.

---

## §B — Claude Code

### B1. Create the directory

```
docs/regime-snapshots/.gitkeep
```

Tracked. **The `.md` and `.yaml` snapshots are also tracked** — they are the record that makes the §5.5a join possible, and an untracked record is not a record. Do not add them to `.gitignore`.

### B2. Repoint every reference

Replace `claude/regime-snapshots/` with `docs/regime-snapshots/` in:

- `docs/specs/SPEC.md` — §3.2, §5.1, §5.5a
- `docs/specs/REGIME-PROMPT.md` — the header line, the three-outputs block in §1, and E1/E2 in PART E
- `docs/specs/BUILD-PLAN.md` — any occurrence
- `CLAUDE.md` — any occurrence

**Path substitution only.** Do not reword surrounding prose, do not renumber sections, and **do not touch any threshold, row count, denominator or YAML field.** `REGIME-PROMPT.md` PART A–D and the `schema_version: 1` schema are out of scope in their entirety. A diff here that changes anything other than a path string is wrong.

### B3. Add the grep test

`tests/test_regime_snapshot_path.py`:

```python
CANONICAL = "docs/regime-snapshots/"
FORBIDDEN = "claude/regime-snapshots/"

def test_no_legacy_regime_snapshot_path() -> None: ...
def test_snapshot_directory_exists() -> None: ...
```

- `test_no_legacy_regime_snapshot_path` — walk tracked text files (`*.md`, `*.py`, `*.yaml`, `*.yml`, `*.ps1`, `*.json`) and assert `FORBIDDEN` appears nowhere. **Exempt `docs/specs/DRIVE-ARCHIVE-LIST.md` and `handoff/`**, which record the old convention as history and must keep saying what it was. Failure message names file and line.
- `test_snapshot_directory_exists` — `docs/regime-snapshots/` exists and is a directory.

**No config key, no loader entry, no reader.** `config/` is stood up in slice 008 and does not exist yet; adding a key here would create a second place the path lives. The constant lives in the test until 008, and 008 moves it into config as a required key with no default.

### B4. Do not

- Do not write a snapshot parser. `SPEC.md` §3.2: the terminal reads a pointer and renders nothing from the snapshot.
- Do not backfill. Snapshots written before this change are in a cloud session, not on disk, and inventing local copies of them would put fabricated records into the store that §5.5a's join will later read as findings.
- Do not create `claude/` as a symlink or alias "for compatibility". One path.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | `pytest` passes including both new tests, and `test_spec_pointers.py` from H9 is no worse than it was — record its status before and after. |
| **Refusal** | Claude Code | Write `claude/regime-snapshots/2026-01-01.md` into a scratch `.md` file in the tree and confirm `test_no_legacy_regime_snapshot_path` fails naming that file and line. Remove it. |
| **UAT** | Christoph | After the next firing, confirm `docs\regime-snapshots\` on D: contains today's `.md` **and** `.yaml`, that `frozen_at` is identical in both, and that the `.md` body matches what was printed in chat. **Commit to whether you expect them to match before opening the files.** If §A1 came back "no", this test is expected to fail with an empty directory — record that as the result rather than marking the slice incomplete. |

## Done-note must state

- Every file changed and the number of path substitutions in each.
- The status of `test_spec_pointers.py` before and after.
- Whether §A1 resolved yes or no, as reported by Christoph, and therefore whether the directory is expected to fill on the next firing.
- Anything in the specs that referenced the old path in a way a plain substitution would have broken.
