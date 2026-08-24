"""087 — B-143. How long a value row may sit `pending` before it becomes a
named refusal, read once per attach.

**The bound is a threshold, and it is Christoph's** — this task's own text:
"it is not ruled." So it is configured, not hardcoded, following the exact
discipline `live/attach/rvol_config.py` already established for `rvol_basis`:
every setting required, none defaulted, a `note:` mandatory so the number
carries its own reasoning rather than sitting bare in a YAML file.

**Deliberately not in `live/attach/`.** `pending_timeout_s` is a rendering
concern — it governs when a row STOPS SAYING `pending` and starts naming a
refusal — not an input to `compute_context_and_rail`'s own arithmetic the
way `rvol_basis` is. It lives beside `app.py`, the layer that renders.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO / "config" / "pending.yaml"


def load_pending_timeout_s(path: Optional[Path] = None) -> float:
    """`config/pending.yaml`, loaded. **Every setting required, none
    defaulted** — the same discipline `load_rvol_basis`/`IbkrConfig.load`
    already hold.
    """
    p = path or CONFIG_PATH
    if not p.is_file():
        raise FileNotFoundError(
            f"{p} does not exist. The pending bound is configured, never "
            "defaulted — there is no built-in ceiling to fall back to, "
            "deliberately.")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    settings = data.get("settings")
    if not isinstance(settings, dict) or "pending_timeout_s" not in settings:
        raise ValueError(f"{p}: no `settings: pending_timeout_s:` mapping.")
    entry = settings["pending_timeout_s"]
    if not isinstance(entry, dict) or "value" not in entry:
        raise ValueError(
            f"{p}: `pending_timeout_s` must be a mapping carrying `value` "
            f"and `note`, got {entry!r}.")
    note = str(entry.get("note") or "").strip()
    if not note:
        raise ValueError(
            f"{p}: `pending_timeout_s` has no `note`. Every setting says "
            "why it is what it is.")
    try:
        value = float(entry["value"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{p}: `pending_timeout_s.value` must be a number, got "
            f"{entry['value']!r}.") from exc
    if value <= 0:
        raise ValueError(
            f"{p}: `pending_timeout_s.value` must be positive, got {value}.")
    return value
