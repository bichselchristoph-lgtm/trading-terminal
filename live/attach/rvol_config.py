"""083 — RVOL's basis becomes a configured choice, read once per attach.

**`core/indicators/context.py` is deliberately pure — "nothing here fetches,
caches, writes, or knows what a terminal is."** Config is a file, so the read
lives here, in `live`, the one layer allowed to touch a filesystem — and
hands `core` the same `SessionBasis` shape every fixed-constant basis
already is. `core` stays exactly as pure as it was; only the SOURCE of one
particular `SessionBasis` value changed, from a module-level constant to a
file read.

**One key, one loader, one object per attach — never two.** `app.py` calls
`load_rvol_basis()` exactly once when it builds a `Stage2Inputs`, and stores
the RESULT — both the numerator-filtering code and the curve-request code
then read `inp.rvol_basis`, the same instance, not two independent lookups
that merely happen to agree.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from core.indicators.context import SessionBasis

REPO = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO / "config" / "rvol.yaml"

#: The two windows every other fixed `SessionBasis` in `core` already
#: labels this way — `ADR_BASIS`/`PRIOR_DAY_BASIS` for RTH,
#: `ATR_BASIS`/`INTRADAY_BASIS` for ETH. Reused verbatim, not re-typed.
_LABEL = {True: "09:30-16:00 ET", False: "04:00-20:00 ET"}

#: The closed vocabulary `rvol_anchor` accepts. An unknown word is a
#: refusal, never a silent default — the same discipline `IbkrConfig.load`
#: already holds every setting to.
_ANCHOR_WORDS = {"rth": True, "eth": False}

#: **The short word a rendered row uses** — `"rth"`/`"eth"` — derived from
#: `SessionBasis.use_rth` at render time (`anchor_word(basis)`, below),
#: never stored as a literal anywhere a row could drift from the value it
#: names. `SessionBasis` itself gains no new field: every OTHER fixed basis
#: has no use for a short word, and adding one to the shared type for one
#: indicator's rendering need would be the type learning about a caller.


def anchor_word(basis: SessionBasis) -> str:
    """`"rth"` or `"eth"`, derived from `basis.use_rth` — never typed at a
    call site. The one function every renderer of RVOL's anchor must call,
    so there is exactly one place that decides what the word is."""
    return "rth" if basis.use_rth else "eth"


def load_rvol_basis(path: Optional[Path] = None) -> SessionBasis:
    """`config/rvol.yaml`, loaded. **Every setting required, none defaulted**
    — the same discipline `IbkrConfig.load`/`load_formats` already hold.

    Returns a real `SessionBasis` — not a bespoke config type — so both the
    numerator-filtering code and the curve-request-building code consume
    the identical shape every other fixed basis already is; RVOL's basis
    being chosen rather than fixed changes WHERE the value comes from, not
    WHAT it is once loaded.
    """
    p = path or CONFIG_PATH
    if not p.is_file():
        raise FileNotFoundError(
            f"{p} does not exist. RVOL's basis is configured, never "
            "defaulted — there is no built-in anchor to fall back to, "
            "deliberately.")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    settings = data.get("settings")
    if not isinstance(settings, dict) or "rvol_anchor" not in settings:
        raise ValueError(f"{p}: no `settings: rvol_anchor:` mapping.")
    entry = settings["rvol_anchor"]
    if not isinstance(entry, dict) or "value" not in entry:
        raise ValueError(
            f"{p}: `rvol_anchor` must be a mapping carrying `value` and "
            f"`note`, got {entry!r}.")
    note = str(entry.get("note") or "").strip()
    if not note:
        raise ValueError(
            f"{p}: `rvol_anchor` has no `note`. Every setting says why it "
            "is what it is.")
    raw = str(entry["value"]).strip().lower()
    if raw not in _ANCHOR_WORDS:
        raise ValueError(
            f"{p}: `rvol_anchor` must be one of {sorted(_ANCHOR_WORDS)}, "
            f"got {raw!r}.")
    use_rth = _ANCHOR_WORDS[raw]
    return SessionBasis(use_rth=use_rth, label=_LABEL[use_rth], why=note)
