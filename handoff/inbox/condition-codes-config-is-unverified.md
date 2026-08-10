---
raised: 2026-08-05
raised_in: core/config/condition_codes.yaml banner
status: PARTIALLY_CONSUMED
---

# condition_codes.yaml is UNVERIFIED against a real delivery

Its own banner said so:

> "UNVERIFIED. Nothing in this file has been checked against a real delivery.
> The values below are ITCH *Cross Trade Message* cross-type codes, which is a
> statement about the Nasdaq protocol, not about how Databento's DBN trades
> schema surfaces them."

**Checked 2026-08-08 and the banner was understating it.** There is no
condition field in the delivery at all -- see
`preregistration.yaml -> fields_that_are_not_what_they_look_like`. The codes
are entirely derived by `identify_auctions`, so the file is not a mapping of
venue codes to meanings; it is a declaration of the vocabulary this codebase
invented.

## Still owed

The banner instructs deleting itself once verified. It must NOT simply be
deleted -- the file needs rewriting to say what it actually is, because a
reader today would take "ITCH cross-type codes" as provenance it does not have.

Also still owed, and separate: the `statistics` schema check the banner
suggested. Venue-published official open/high/low is the only source
INDEPENDENT of the trades delivery, so it is the only thing that can confirm
the identification rather than agree with itself.
