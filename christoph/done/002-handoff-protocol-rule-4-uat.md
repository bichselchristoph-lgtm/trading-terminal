# 002 — UAT: does rule 4 match what you meant by shared judgment?

**Status** DONE · **Type** UAT · **Date** 2026-08-11
**Raised by** `013` exit tests · **Answered** 2026-08-11 · **Produced** amendment 2a

---

## The question

`013` adopted `docs/specs/HANDOFF-PROTOCOL.md` and set one UAT:

> Open `docs/specs/HANDOFF-PROTOCOL.md` and read rule 4. Confirm it matches what you meant by
> shared judgment. **If it does not, that is a spec defect and a new task, not an edit.**

Rule 4 as adopted:

> **4. Judgment is shared, and which of us holds it depends on the call.**
>
> - The mechanical facts are Christoph's: inbox placement, whether it ran, **what the note
>   says**. He is the only one who can see them.
> - The reading is the design session's to *propose*: whether the note shows the task did what
>   it set out to do, what remains open, whether anything is owed.
> - The proposal is not a verdict. Christoph weighs it and may call something the design
>   session missed or misread.

## The answer

**Confirmed — with one correction.** The shape of rule 4 is right: judgment is shared, and
which party holds it depends on whether the call is a mechanical fact or a reading.

**The correction: "what the note says" does not belong in the mechanical-facts list.** Once
Christoph pastes the note, the design session reads the same text and can read it as well or
as badly as anyone. Nothing about the contents is uniquely his.

**What *is* uniquely his:**

- inbox placement
- whether it ran
- **whether a done-note exists on disk**
- **whether what reached the design session was all of it**

## The evidence that settled it, from the same day

`012a` and `013` both wrote done-notes into `handoff/done/`. **Neither reached the design
session**, which went on holding a stale `RUNNING` for both.

Nothing in either repository detected this, and nothing could: the file was real on one side
of the channel and absent on the other. **Only Christoph stood where both sides are visible.**

That is exactly why *whether a note exists* belongs on his side of the list and *what it says*
does not — and the incident is now recorded in the rule itself as the reason.

## Applied

`013c` amendment **2a**, as an in-place edit to `docs/specs/HANDOFF-PROTOCOL.md`. The
mechanical-facts list is corrected and the 2026-08-11 incident is recorded beneath it as the
reason the distinction exists.

**Not re-authored, and no replacement accepted from outside the tree** — that would have been
the defect `RE-SUPPLY.md` exists to catch.

## Nothing further owed

The UAT is answered, the correction is applied, and the reason is on the record.
