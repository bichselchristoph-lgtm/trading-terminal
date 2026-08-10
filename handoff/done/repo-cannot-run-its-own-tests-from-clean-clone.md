---
raised: 2026-08-09
raised_by: chat, during local verification of 004
acted: 2026-08-09
decided: 2026-08-09
decided_by: user
status: RESOLVED
resolution: >
  Both filed items closed, and the decision underneath item 2 made: the floors
  ARE raised to the verified majors. requirements.txt now reads pandas>=3.0,<4.0
  and numpy>=2.0,<3.0, with pytest>=8.0,<10.0 added as a real entry and the
  verified resolution (pandas 3.0.3, numpy 2.5.1, pytest 9.1.1, Python 3.12.7)
  recorded at the top of the file. A lockfile was considered and deliberately
  deferred until a second machine exists, so <4.0 still admits an unrun 3.9.
---

**RESOLVED 2026-08-09.** The narrow decision underneath item 2 — whether to
RAISE the floors rather than merely cap them — was the user's, and it was made:
raise them.

The argument that carried it: nothing else under `D:\Dev` consumes pandas or
numpy (`tws_order` needs only `ib_async`, `PyYAML`, `colorama`), so `>=2.0`
bought no compatibility with anything real and cost a support claim that no run
had ever backed. A grep found no pandas-2-incompatible usage and zero
`inplace=True` across `core/`, `harness/` and `live/` — weak positive evidence
that 2.x would probably work, and "probably works" is precisely the claim this
repo refuses everywhere else.

An earlier session wrote `status: ACTED` here. That word is not in the
vocabulary `tests/test_open_questions.py` recognises, and inventing one is not
a way to answer a question.

## What was done, 2026-08-09

**Item 1 — closed.** `pytest>=8.0,<10.0` is a real entry in `requirements.txt`
now, not a comment telling the reader to install it. Kept in the same file
rather than split into `requirements-dev.txt`, so one install makes the repo
verifiable — the argument in the note (09:15, trading morning) is an argument
for fewer steps, and a second file is a step.

**Item 2 — the narrow question answered both ways: yes, and yes.**

Ceilings added at the next major above what is verified:

```
pandas>=2.0,<4.0
numpy>=1.24,<3.0
```

Verified versions recorded at the top of `requirements.txt`: pandas 3.0.3,
numpy 2.5.1, pytest 9.1.1, Python 3.12.7 — measured in `C:\venvs\trading`,
which is the interpreter that actually ran the suite. Note this differs from
the 3.0.5 in the note below: that was a *clean install* resolving on the same
day, and the gap between the two is the point being made, so both numbers are
left standing rather than reconciled.

**Left open on purpose:** the floors were NOT raised to the verified majors.
`pandas>=2.0` still admits a 2.x install that nothing has verified. Raising it
makes 2.x invalid rather than merely unverified, which is a real decision about
other machines and other checkouts, and the note explicitly did not ask for it.
That one is yours.

---

# The repo cannot run its own test suite from a clean clone

Found while verifying 004's 79 tests on the trading machine rather than in a
build sandbox. Both items below are about the same thing: the environment that
proves the code works is not itself recorded.

## 1. pytest is not in requirements.txt

A fresh clone installs pandas, numpy, databento, zstandard, ib_async and PyYAML
— and then `pytest` is not found. The suite is 2,500+ tests and none of them can
be run until someone independently knows to `pip install pytest`.

Nothing was wrong with the code. The 79 tests pass. But the path from "clone the
repo" to "see the tests pass" has an undocumented step in it, and the person
walking that path at 09:15 on a trading morning is the one who can least afford
to debug it.

Fix is one line in `requirements.txt`. Worth deciding at the same time whether
test-only dependencies belong in the same file or a separate
`requirements-dev.txt` — either is fine, but the current state (absent) is not.

## 2. pandas and numpy are unpinned across a major version

`requirements.txt` floors them:

```
pandas>=2.0
numpy>=1.24
```

No ceiling. A clean install on 2026-08-09 resolved to **pandas 3.0.5** and
**numpy 2.5.1** — a major version above the floor in both cases. The tests pass
on those versions on this machine, so this is not currently breaking anything.

The concern is that the versions the suite was written and verified against are
not recorded anywhere, so "the tests passed" does not identify what they passed
against. Two machines installing from the same file on different days can get
different majors, and a future failure would look like a code regression rather
than a dependency jump.

This is the Tenet 6 shape in a different domain: a result that holds on the
configuration it was derived from, carried across to one it was not.

Not asking for a full lockfile decision here — that is a bigger call. The
question is narrower: **should the floors carry ceilings, and should the
verified versions be recorded somewhere?**

## Note on scope

Both are small. Neither blocks the dashboard build. They are filed rather than
fixed because they are config decisions with a preference attached, not defects
with an obvious right answer.
