# momentum-regime-snapshots-from scheduled

Copies of the 05:00 ET daily regime read, published by the scheduled task.

- Source of truth: **the stored prompt of the scheduled task** (decision, Christoph, 2026-08-13). `docs/specs/REGIME-PROMPT.md` in `D:\Dev\momentum` is a copy of it, not an authority over it.
- Files here are **copies**. The canonical write location for a scheduled cloud run is the Claude project at `claude/regime-snapshots/YYYY-MM-DD.{md,yaml}` — that run has no repo access, permanently.
- Two files per session: `.md` is the read, `.yaml` is the locked snapshot. `frozen_at` is written once and never updated.
- Nothing here is edited in place. A correction is a new session's file, never a rewrite of an old one.

Publishing to this folder starts with REGIME-PROMPT v1.7.
