---
raised: 2026-08-05
consumed: 2026-08-08
raised_in: core/identify.py module docstring
status: DONE
---

# NOII should supersede the clock anchor

The original note, written when `identify.py` was built:

> "NOII remains the better source for *type and window* and should supersede
> the anchor logic here when wired; this rule then becomes the fallback for
> sessions where imbalance is missing."

**Correct, and sat unread for three days** while a QQQ-derived 5-second clock
window dropped 30% of the phase-3 training sample on NYSE's staggered open.

Consumed 2026-08-08. `identify_auctions` now takes an optional `imbalance`
frame and anchors on the last record of the matching `auction_type`; the clock
window is the fallback, exactly as the note said it should be. Recovered 479 of
581 skipped symbol-days.

**Why this is in handoff/ and not a comment.** It was a comment, and being a
comment is why nothing happened. A note saying "X should supersede this when
wired" is a message to a future session, not documentation of present
behaviour — and messages need somewhere that gets read.
