# Parked observations

Findings noticed but not acted on.

**The convention lives in `CLAUDE.md`, under "Handoff convention". That file
governs; this one does not.** What an observation must say, the three routes
out of this folder, and the prohibition-first rule for gated findings are all
stated there and are not restated here — a summary drifts, and a drifted
summary beside a governing file is worse than no summary. A fresh session reads
`CLAUDE.md` whether or not anyone points at it; this README is read only if
someone opens the folder and thinks to look.

Unlike `handoff/README.md`, which keeps one line of its own, there is nothing
here that `CLAUDE.md` does not hold better. So this file is a pointer and a
record of its own correction, and nothing else.

## What was removed, 2026-08-09

This README carried an *Awaiting content* section stating that `gap-off-lows`
was "referenced as a parked observation but not present in this tree or
anywhere under `D:\Dev`", and warning that it "exists only in a chat log and
will be lost".

It was committed as `docs/observations/gap-off-lows.md` in `46a35f6` at 15:12
on 2026-08-07. This README was written in `21d5a09` at 15:08 the same day.
**The claim was false four minutes after it was written, and stayed in the tree
for two days.**

The same section pointed promotions at `config/preregistration.yaml`. The only
such file is `harness/config/preregistration.yaml`; the top-level `config/`
directory is empty. A reader following that path finds nothing and has no way
to tell whether the file or the instruction is wrong.

Both are recorded rather than quietly deleted, because a README that was wrong
about its own folder for two days is evidence about how this class of file
decays — and because `handoff/README.md` failed in the identical way in the
same week. The rule that catches it is stated in that file: **an artifact
states the state it assumes, and the reader verifies that state before acting.**
