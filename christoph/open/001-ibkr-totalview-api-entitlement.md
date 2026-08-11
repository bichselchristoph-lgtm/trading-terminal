# 001 — Why does TotalView return 10089 for API access?

**Status** WRITTEN · **Type** EXTERNAL · **Date** 2026-08-11
**Blocking** nothing. Matters only if QQQ's primary book is wanted for a later capture.

---

## The question to put to IBKR

**An account holding NASDAQ TotalView-OpenView receives error 10089 — "requires additional
subscription for API" — when requesting market depth on `NASDAQ.NMS/DEEP`. Why, and what
enables it?**

The wording that points at the answer is **"for API"**. If TotalView is active for the TWS
display but a separate entitlement is needed for API access, that would explain the refusal
without contradicting the subscription being held — but that is a reading, not something the
probe established.

## What was observed, verbatim

Probed 2026-08-11 at 05:07 ET under task `012a`, read-only, `numRows=10`, each request
cancelled before the next:

```
ISLAND   0x0   Error 10089: Requested market data requires additional subscription for API.
                 See link in 'Market Data Connections' dialog for more details.
                 QQQ NASDAQ.NMS/DEEP
NASDAQ   0x0   Error 10089: (byte-identical message, same feed identifier)
ARCA     9x9   served — top of book 721.15 / 721.34
```

**`ISLAND` and `NASDAQ` return byte-identical messages naming the same feed,
`NASDAQ.NMS/DEEP`.** They are one route, not two. The hypothesis that IBKR serves TotalView
under `ISLAND` rather than `NASDAQ` was tested and is not borne out on this account.

## What is *not* being claimed

**Not that the account lacks TotalView.** Christoph confirmed from account management that he
holds NASDAQ TotalView-OpenView and pays for the full North America subscription set including
NYSE ArcaBook and Cboe BZX Depth.

An earlier phase-0 report *did* read the 10089 as "the account lacks TotalView", and that was
one of two misdiagnoses in a single session — both the same shape: **a specific refusal read
as a general absence.** This file records the code and its literal text, and stops there.

## Why it matters, and why it is not urgent

**QQQ is NASDAQ-listed, so TotalView is its deepest book.** Today's capture runs depth on
**ARCA**, which works and is genuinely useful, but is a single venue's view and not the
primary one.

It is not blocking: the 2026-08-11 capture proceeded on ARCA, and depth costs nothing at the
margin since the subscription set is already paid monthly. It becomes worth resolving if a
later capture wants the primary book.

## What a useful answer looks like

Any one of these closes it:

- TotalView requires a separate API-access entitlement, and here is how to enable it.
- The correct exchange string is neither `NASDAQ` nor `ISLAND`, and here is what it is.
- The subscription is active but had not propagated at the time of the probe.
- Something else — in which case the observation above is what to show them.
