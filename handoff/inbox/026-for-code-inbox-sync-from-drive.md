
026-for-code-inbox-sync-from-drive.md

Page
1
/
1
100%
---
id: 026
title: Copy task files from the Drive sync folder into handoff/inbox
status: READY
blocks: []
type: pipeline
owner: claude-code
depends: 025
---

# 026 — The inbox arrives through Drive

**This is the last task file that needs placing by hand.** After it runs, the design session
writes into a Google Drive folder, Drive syncs it to disk, and this task copies it into
`handoff/inbox/`. **The download-and-copy step disappears.**

| Location | Role |
|---|---|
| The design session | **Authors.** Writes to Google Drive `momentum-inbox-handoff` |
| `D:\claude-googledrive-sync\momentum-inbox-handoff\` | **Lands.** Written by Drive sync |
| `D:\Dev\momentum\handoff\inbox\` | **Consumes.** This task's destination |

---

## Build it as a second configured pair, not a second script

**Task `025` builds this exact copier for the regime snapshots.** Do not write it twice.
**One copier, two configured pairs:**

```yaml
# config/sync.yaml
pairs:
  - id:   regime_snapshots
    from: 'D:\claude-googledrive-sync\momentum-regime-snapshots-from scheduled'
    to:   'D:\Dev\momentum\docs\regime-snapshots'
  - id:   handoff_inbox
    from: 'D:\claude-googledrive-sync\momentum-inbox-handoff'
    to:   'D:\Dev\momentum\handoff\inbox'
```

**Two copies of this logic will diverge**, and the rule below is subtle enough that having it
implemented twice is exactly how one copy loses it. **If `025` has already shipped a
single-purpose script, generalise it here rather than adding a sibling.**

**Note the space in the regime folder name** and quote both paths. An unquoted path fails in
a way that looks like an empty folder rather than an error.

---

## The rule is the same as `025`, and for the same reason

| Case | Action |
|---|---|
| Not in the inbox | **Copy it.** Report the filename — this is actionable |
| In the inbox, byte-identical | **Do nothing.** The normal case |
| In the inbox, **differs** | **Do not overwrite. Report and stop.** |

**Why immutability matters here as much as it does for a snapshot.** `Do inbox 012` resolves
a path by name, and done-notes cite paths. **A task file that changes after it was handed off
breaks a reference another party already holds** — and worse, Claude Code may have already
read the old one. **Silently replacing it would mean two parties acting on two different
documents while both believed they had the same one.**

**Compare on content, not on modification time.** Drive sync rewrites mtimes on files whose
bytes never changed — a re-sync or a client reinstall is enough. **An mtime comparison would
report a change every time Drive touched the folder**, and real changes would drown in it.

**One way. Never write to, delete from, or rename in the sync folder.** It is the design
session's channel. A file appearing there because this task put it there would be
indistinguishable from one the design session authored.

---

## Two checks that belong here and not in `025`

**1. Filename convention.** Files arriving for the inbox should match `NNN-for-code-*.md`.
**Copy anything that does not, but name it in the report** — the convention exists so the
audience is visible before the file is opened, and a file that breaks it is more likely a
mistake than a deliberate exception. **Do not refuse it**; the design session may have had a
reason, and a refused task file is a task nobody sees.

**2. Number collision.** If an arriving file's `NNN` matches an existing inbox file with a
different name, **report it prominently and copy neither into place.** Numbers have collided
three times in this project. **The design session reads the folder before assigning, but it
reads it at a moment, and Drive sync introduces a gap between reading and landing.**

---

## Reporting — silence must be meaningful

Three outcomes, and they must not read alike:

- `2 new · 021, 022 · 0 differing` — **name what arrived.** This is the line that tells
  Christoph what he can now run
- `0 new · up to date` — the healthy no-op
- `0 new · source folder empty or unreachable` — **a different fact**, and the one meaning the
  pipeline is broken rather than idle

**A task that prints nothing when it succeeds prints nothing when it fails.**

---

## Done when

- A file placed in the Drive folder appears in `handoff/inbox/` after a run, and is named in
  the report.
- A re-run copies nothing and says so.
- **A deliberately-modified inbox copy causes a report and no overwrite** — demonstrate it.
- A file whose name breaks the convention is copied **and** flagged.
- The sync folder is byte-for-byte unchanged after a run.

---

## Deliverable

`handoff/done/026-for-code-inbox-sync-from-drive.md`:

1. Whether `025`'s copier was generalised or a second one written, and why.
2. The differing-file case demonstrated — modify an inbox copy, run, quote the report,
   confirm nothing was overwritten.
3. The convention-flag case demonstrated.
4. **What you could not do**, and why. Empty is suspicious.
5. `verify.ps1` run at `<time>`.
Displaying 026-for-code-inbox-sync-from-drive.md.