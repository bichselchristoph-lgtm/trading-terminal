"""Link colour — `SPEC.md` §4.1a, ruled by Christoph 2026-08-15 under `044`.

**A link colour ties a value to the line that explains it. It says these two are
the same thing. It says nothing about whether either is good.**

----

**Why this survives §4.1's no-verdict conviction.** §4.1 binds each colour to a
*kind* — blue a parameter, amber a failed rule or a refusal, green and red
fitted signals. **A level state and a distance are none of those**, so the rule
offered them zero colours rather than one, and `042` correctly stopped rather
than taking one.

**A verdict is a claim about ONE thing. A link is a claim about TWO**, and it
cannot be read as a judgment because **it never appears alone**. That is not a
convention — it is the invariant this module exists to enforce.

Three constraints, and they are the whole rule:

1. **The link colour carries no meaning on its own.** Seeing it tells you only
   that there is more below.
2. **It is always used in pairs or groups. A linked token with no partner on
   screen is a defect** — `orphan_links` finds them and the render refuses.
3. **It never replaces a kind colour.** A refusing row stays amber; the link
   colours only the token that names *which* row the explanation belongs to.

**What it replaces: footnote marks, everywhere.** No `*`, no dagger, no numbered
footnotes, in any panel. **The shared token is the legend.**

----

**Nothing renders a link yet**, and that is deliberate — `044` puts panel layout
out of scope and leaves it to `S012`. What lands here is the primitive and its
guard, so that the first panel to emit a linked token is already held to the
rule rather than establishing a precedent that has to be corrected afterwards.

**The tests exercise `orphan_links` against constructed lines**, because a guard
that has only ever run against zero linked tokens has not been shown to fire —
`OBS-037`'s shape, and this project's most repeated defect.
"""
from __future__ import annotations

import re
from typing import Iterable

#: **Violet. Christoph's ruling, 2026-08-15.** Unused by §4.1's four-colour
#: grammar, so it cannot be confused with a kind.
#:
#: **One hue for all pairs on a panel.** Four linked pairs share it. **If that
#: proves too many to read, the fix is fewer notes, not more colours** — a
#: second link hue would immediately mean something, and meaning is the thing a
#: link is forbidden to carry.
#:
#: `c024` confirms it is legible at 209x54 in Christoph's palette. **If violet is
#: not legible that is a finding and a question, not a licence to reuse green.**
LINK_HUE = "violet"

#: How a linked token is marked in a rendered line, and **it is deliberately NOT
#: square brackets.**
#:
#: `SPEC.md` §4.1a illustrates links as `[PML]` and says outright that *the
#: brackets stand for the link colour; they are not rendered.* Taking that
#: notation literally as the marker collides with a convention already in the
#: tree: `Cell.not_built` renders `[ NOT BUILT ]`, and the first run of
#: `test_the_live_panels_emit_no_orphaned_links_today` duly reported
#: `{' NOT BUILT ': 1}` — **the grammar's own refusal marker read as an orphaned
#: link.**
#:
#: Banning spaces in the token would have hidden that one case and broken
#: §4.1a's own `[at level]` example. So the marker is `U+27E6`/`U+27E7`, which
#: appears nowhere in the tree, and the illustration in the spec stays an
#: illustration. **A terminal back end substitutes the hue; this is how the
#: layer below names the intent.**
_OPEN, _CLOSE = "⟦", "⟧"
_LINKED = re.compile(_OPEN + r"([^⟦⟧]{1,24})" + _CLOSE)


def link(token: str) -> str:
    """Mark `token` as linked. **Never call this on a token you do not also
    explain somewhere on the same panel.**"""
    if not token or not token.strip():
        raise ValueError(
            "a linked token must have text. An empty link is a colour with "
            "nothing to pair against, which is the defect orphan_links exists "
            "to catch.")
    if _OPEN in token or _CLOSE in token:
        raise ValueError(f"token {token!r} is already marked")
    return f"{_OPEN}{token}{_CLOSE}"


def linked_tokens(line: str) -> list[str]:
    """Every linked token in one rendered line, in order."""
    return _LINKED.findall(line)


def orphan_links(lines: Iterable[str]) -> dict[str, int]:
    """`{token: count}` for every linked token appearing **fewer than twice**.

    **Fewer than twice, not exactly once.** A token could in principle be marked
    zero times and still be wrong, but that state is unrepresentable — it is not
    in the text at all. What this catches is the real failure: somebody colours
    a value, means to write the note, and does not.

    Returns a mapping rather than a bool so the caller can name the offenders.
    An empty mapping means every link has a partner.
    """
    counts: dict[str, int] = {}
    for line in lines:
        for token in linked_tokens(line):
            counts[token] = counts.get(token, 0) + 1
    return {t: n for t, n in counts.items() if n < 2}


def check_links(lines: Iterable[str]) -> None:
    """**Refuse a panel that emits an orphaned link.** `044`'s exit test.

    Loud rather than silent, because the failure mode is a colour that means
    nothing — and a link colour that appears alone will be read as *important*,
    which is a verdict wearing a hat. **That is exactly what §4.1 forbids**, so a
    quiet fallback here would reintroduce verdict colour through the one channel
    added on the promise that it could not.
    """
    orphans = orphan_links(lines)
    if orphans:
        named = ", ".join(f"{t!r} x{n}" for t, n in sorted(orphans.items()))
        raise ValueError(
            f"linked tokens with no partner on screen: {named}. "
            "A link is a claim about TWO things and never appears alone "
            "(SPEC.md §4.1a). Either write the note or drop the link.")
