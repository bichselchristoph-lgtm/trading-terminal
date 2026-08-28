"""092 — the two account keys and the startup assert that makes `--paper`
mean something stronger than a flag someone typed.

RISK §8 already said `--paper` is a launch flag with no runtime switch, "so
no order can reach an account other than the one on screen when the
terminal started." **That sentence described an intention, not a
mechanism.** Nothing read the account number back from the broker and
compared it to anything. This module is the comparison — **rule 17: an
instruction names a condition the terminal can check about itself.**
`--paper` is a flag someone typed; the connected account number is a fact
the terminal can read. This is where the second one governs.

**Christoph's own values, never a task's, and never in a file that pushes
to GitHub.** `config/ibkr.yaml` — the file that owns broker connection — is
TRACKED (checked directly: `git ls-files -- config/ibkr.yaml` returns it,
`git check-ignore` refuses it). An account number committed there is a
leak, and it is the kind that is invisible until it is not. So the real
values live in `config/secrets.yaml` — matching the `secrets.yaml`
`.gitignore` rule that already existed, unused, before this task
(`git check-ignore -v config/secrets.yaml` confirms it; `config/ibkr.local.yaml`,
the other name this could have had, is NOT covered by any existing rule) —
and `config/ibkr.yaml` carries only the two key NAMES, as a pointer, so a
reader of the file that owns broker connection can see these two settings
exist without discovering them by reading this loader's source.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import yaml

REPO = Path(__file__).resolve().parents[2]
ACCOUNTS_CONFIG_PATH = REPO / "config" / "secrets.yaml"


class AccountAssertionError(Exception):
    """092's startup refusal. Raised by `ibkr.connect()` once a broker
    handshake succeeds, never folded into a `BrokerConnection` — **this is
    a safety refusal, not a connectivity state.** `SPEC.md`'s "surfaced,
    not refused" governs TWS being unreachable (an existing, safe state:
    no connection exists, so no order path exists either, and the terminal
    still starts and says why). A CONFIRMED WRONG ACCOUNT is a new and
    different kind of failure — 092's own text is explicit that it is a
    *startup* refusal, not a runtime display state, so this must crash the
    launcher before Textual takes the screen, the same way a malformed
    `config/ibkr.yaml` already does.
    """


@dataclass(frozen=True)
class AccountConfig:
    """`account_live`/`account_paper`, or `None` for either that is not
    set. Both null is a legitimate, expected state on a fresh checkout —
    Christoph has not written `config/secrets.yaml` yet — and is NOT an
    error here; `assert_connected_account` is where an unset key becomes a
    refusal, at the point a launch mode is actually known."""

    account_live: Optional[str]
    account_paper: Optional[str]


def load_account_config(path: Optional[Path] = None) -> AccountConfig:
    """`config/secrets.yaml`, gitignored. A missing file and a present-but-
    null key resolve to the SAME `None` here, deliberately — so "Christoph
    has not created the file yet" and "the file exists with `account_paper:
    null`" produce the identical, mode-specific refusal downstream, rather
    than two different messages for what is functionally the same unset
    state. **Never raises** — `IbkrConfig.load()`/`Layout.load()` raise
    because a malformed *tracked* file is this repository's own bug; a
    missing *local* secrets file is the expected state on every machine
    until Christoph fills it in, and is refused by name once a mode is
    known, not by a bare `FileNotFoundError` three frames deep.
    """
    p = path or ACCOUNTS_CONFIG_PATH
    if not p.is_file():
        return AccountConfig(account_live=None, account_paper=None)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    live = data.get("account_live")
    paper = data.get("account_paper")
    return AccountConfig(
        account_live=str(live) if live else None,
        account_paper=str(paper) if paper else None,
    )


def assert_connected_account(broker_accounts: Sequence[str], accounts: AccountConfig,
                             *, paper: bool) -> None:
    """The comparison itself. Called ONLY after a broker handshake has
    already succeeded (`ibkr.connect()`'s own job) — TWS being unreachable
    never reaches this function at all, and stays the existing, safe,
    surfaced-not-refused state.

    **Three refusals, three distinguishable messages** — `SPEC.md`'s own
    absence-is-not-zero, applied to an account number instead of a price.
    Checked in this order: the config key needed for THIS launch mode
    (independent of what the broker said), then whether the broker said
    anything at all, then whether what it said matches.
    """
    key = "account_paper" if paper else "account_live"
    expected = accounts.account_paper if paper else accounts.account_live
    mode = "paper" if paper else "live"

    if not expected:
        raise AccountAssertionError(
            f"{key} is not set in config/secrets.yaml -- refusing to start. "
            "Christoph sets this himself; nothing here defaults it.")
    if not broker_accounts:
        raise AccountAssertionError(
            "the connected account number could not be read from the broker "
            "-- refusing to start. Absence is not a match.")
    if expected not in broker_accounts:
        raise AccountAssertionError(
            f"connected account(s) {list(broker_accounts)} do not match the "
            f"configured {mode} account {expected!r} (requested mode: "
            f"{mode}) -- refusing to start.")
