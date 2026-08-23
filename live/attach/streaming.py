"""**080 — the shared streaming primitive.** One small type, used by the
`MarketData` Protocol, `IBKRMarketData` and every test fixture alike: a
handle to something ongoing that can be told to stop.

**Not broker-specific.** Nothing here knows about `ib_async` or a broker
loop — that lives in `live/attach/ibkr.py`, which is the only module that
touches a broker. This module exists so `attach.py` and `app.py` can name
the type without importing anything IBKR-specific.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class StreamHandle:
    """What `open_price_stream` (and any future ongoing subscription)
    returns. **`cancel()` is idempotent** — a second call is a no-op, not an
    error, because the caller that owns the handle (`app.py`, on a symbol
    switch) and the stream's own error path can both reach for it, and
    neither should have to check which one got there first.

    **Suppresses FUTURE callbacks; does not claim the wire request was
    aborted.** A one-shot request already in flight when `cancel()` runs may
    still complete on the wire — the underlying close/cancel call is made,
    but a caller relying on "no data arrives after cancel" also needs its
    own generation guard (`app.py`'s `_attach_generation`), which is the
    belt-and-braces this task's cancel-on-switch requirement is built on.
    """

    _cancel_fn: Callable[[], None] = field(repr=False)
    _cancelled: bool = field(default=False, repr=False)

    def cancel(self) -> None:
        if self._cancelled:
            return
        self._cancelled = True
        self._cancel_fn()

    @property
    def cancelled(self) -> bool:
        return self._cancelled
