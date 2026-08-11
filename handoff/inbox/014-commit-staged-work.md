# 014 — Commit the staged work before the capture

**Status** WRITTEN · **Date** 2026-08-11 · **Type** version control
**Runs in** `D:\Dev\momentum`. No TWS, no network, no push. **Do this before 09:00 ET.** It is roughly five minutes and it must not delay the capture — if it is not finished by 08:55, **stop and start the capture; the commits can wait, the session cannot.**

> Read this cold. The session that wrote it cannot answer questions.

---

## Why

**58 staged paths, nothing committed, HEAD still at `aa8bb43`.** Every gate decision, both new trees, the protocol amendments and the whole of `S009` exist only in the index.

The index is not durable in the way a commit is. **One `git checkout`, one `git reset --hard`, one crash mid-write and a full day of work is gone** — including four accepted tasks and the first working panel this project has ever produced. That risk is carried for no benefit; the work is finished and tested at `99 passed, 0 failed`.

---

## Part 1 — Commit, split coherently

**Do not commit this as one lump.** The staged work spans three unrelated efforts, and a single commit makes `git bisect` worthless across all of them — which matters most for `S009`, the only part that is running code rather than documents.

Split at least three ways, and further if the shape of the work suggests it:

1. **M001-era gate work** — the adoption gate, allowlist and tooling changes.
2. **The `013` protocol series** — `HANDOFF-PROTOCOL.md`, `CHRISTOPH-TASKS.md`, resolution D and its two guards, the new trees, the reconstructed done-notes, `013d`'s §2e correction.
3. **`S009`** — the TUI frame, the refusal grammar, the thin day record, `config/layout.yaml`, and the snapshot suite.

**Each commit's message says what changed and why, not what file moved.** A message a cold reader can act on, in the same spirit as a done-note.

**If any staged path does not fit the three groups, say so rather than forcing it** into the nearest one. A file that belongs nowhere is usually a finding.

**Do not push.** Neither repo has a correct remote — the GitHub repo named `momentum` maps to the **archived** local tree, and pushing this one would put it in the wrong place. That decision is still open.

---

## Part 2 — Two stale headers

Christoph has confirmed both. **These are not inferences.**

- `handoff/inbox/013-adopt-handoff-protocol.md` → `**Status** DONE`
- `handoff/inbox/013c-resolution-d-protocol-and-trees.md` → `**Status** DONE`

Both are also in `handoff/accepted/`, so both are closed on both sides.

**Leave `H8`, `H9` and `M001` alone.** They declare `OPEN`, which is not one of the five states, and they are carried evidence under resolution D. Editing them breaks `EVIDENCE-CARRY.md`, and asserting a state for a file that predates the convention is the fabrication the test exists to prevent. **The exemption is working; do not tidy it.**

---

## Part 3 — Then the capture

At **09:00 ET**, start `012`'s QQQ tape capture and run it to the close, on the `012` configuration as amended by `012a`: `clientId 11`, depth on ARCA, `quote_basis` and per-line exchange attribution on every trade, three raw append-only streams, gap records, 60 s heartbeat, and the four live-verification assertions.

**Nothing in this task changes any part of that.**

---

## Do not

- Do not push either repository.
- Do not modify any file recorded in `EVIDENCE-CARRY.md`.
- Do not amend or rewrite any existing commit.
- Do not change `tools/capture_tape.py` or anything under `records/`.
- Do not let this task delay the 09:00 ET start.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full `pytest` after committing, unchanged at **99 passed, 0 failed**. `git status` clean, or with only deliberate exclusions named. |
| **Refusal** | Claude Code | Confirm `EVIDENCE-CARRY.md` hashes still verify after the commits — **prove it, do not assert it.** |
| **UAT** | Christoph | None. |

## Done-note must state

- Every commit hash, with its message and what it contains.
- Any staged path that fitted none of the three groups.
- The hash verification result.
- Confirmation that the capture started at 09:00 ET, or why it did not.
- **Anything in this task that diverged from what was on disk.**
