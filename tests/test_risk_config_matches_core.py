"""`config/risk.yaml` and `core/risk/classify.py` must not drift — `039`.

**A config file nothing reads is a config file that goes wrong quietly.** `039`
does no panel work and builds no limit enforcement, so `config/risk.yaml` is a
declaration ahead of its consumer: today nothing in the tree loads it. That is
the state in which a value gets edited, has no effect, and is later read as the
one in force.

This test is the stand-in reader. It pins the two classification thresholds and
the commission basis against the constants in `core`, so editing one without the
other is red.

**Scoped positionally to two paths** — `config/risk.yaml` and the `core.risk`
constants. It does not scan the tree for numbers; a repo-wide search for `0.05`
would match its own source, which is the self-reference trap `038` and `039`
both warn about.

**It deliberately does NOT pin the limits** (`trades_max_day` and the rest).
Those have no code counterpart yet, and asserting them against a second copy of
the same literals in a test would be a test of nothing — it would pass whatever
the value, as long as somebody updated both. The classification thresholds are
different: `core` has real defaults that real code branches on.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from core.risk.classify import COMMISSION_BASIS, DEFAULT_THRESHOLDS

REPO = Path(__file__).resolve().parents[1]
RISK_YAML = REPO / "config" / "risk.yaml"


@pytest.fixture(scope="module")
def declared() -> dict:
    assert RISK_YAML.exists(), (
        f"{RISK_YAML.name} is missing. 039 Part 1 declares 1R there and nowhere else."
    )
    return yaml.safe_load(RISK_YAML.read_text(encoding="utf-8"))


def test_one_r_is_declared_as_a_fixed_dollar_amount(declared: dict) -> None:
    """`039` Part 1, Christoph's ruling of 2026-08-14 stated twice: **1R is a
    fixed dollar amount declared in config. It does not move with NLV.**"""
    assert "risk_usd_per_trade" in declared, (
        "risk_usd_per_trade is THE declaration of 1R and it is absent"
    )
    assert isinstance(declared["risk_usd_per_trade"], (int, float))
    assert declared["risk_usd_per_trade"] > 0


def test_the_percentage_keys_are_gone_from_the_sizing_path(declared: dict) -> None:
    """`risk_pct_default` and `risk_pct_cap` are removed. **Absent, not present
    and ignored** — a key read by nothing that still sits in config is a key
    somebody sets, watches do nothing, and then distrusts the whole file over.

    This is about `momentum`'s config only. `tws_order/` keeps percentage-of-NLV
    sizing and must not lose it; that repo is out of scope by standing decision.
    """
    for gone in ("risk_pct_default", "risk_pct_cap", "risk_pct"):
        assert gone not in declared, (
            f"{gone} is back in config/risk.yaml. 039 Part 1 removed it from the "
            "sizing path; if a percentage-of-NLV sanity check is wanted it warns "
            "and never sizes."
        )


def test_no_cap_on_winning_trades_or_on_gains(declared: dict) -> None:
    """`039` Part 3, and `039`'s report item 4 asks this be checked across the
    tree. v1.0 of `039` carried `winners_max_day: 2`; a later draft proposed
    `r_gain_stop_day`. **Both are removed and neither may come back here.**

    A count cap cannot tell a 15R morning from a lucky scratch, and a gain cap
    would stop trading after +15R by 09:35 — firing on the best morning of the
    quarter. Every remaining limit stops Christoph when it is going badly and
    never when it is going well.
    """
    for forbidden in ("winners_max_day", "winners_max_month", "r_gain_stop_day",
                      "r_gain_stop_month", "gains_max_day"):
        assert forbidden not in declared, (
            f"{forbidden} is a cap on winning. 039 Part 3 removed it deliberately "
            "and records why — read that before adding it back."
        )


def test_the_r_limits_are_losses_and_are_negative(declared: dict) -> None:
    """Sign is the basis here. `r_max_loss_day: 2.0` and `-2.0` are the same
    intention written two ways, and a limit compared with the wrong sign never
    fires — a silent absence, which is the class of defect `037` was about."""
    for key in ("r_max_loss_day", "r_max_loss_month",
                "daily_loss_usd", "monthly_loss_usd"):
        assert key in declared, f"{key} is missing from config/risk.yaml"
        assert declared[key] < 0, (
            f"{key} is {declared[key]}. Loss limits are declared negative so the "
            "comparison cannot be written the wrong way round and silently never fire."
        )


def test_the_classification_thresholds_match_core(declared: dict) -> None:
    """The drift pin. Editing the yaml without editing `core` is red."""
    assert declared["breakeven_band_r"] == DEFAULT_THRESHOLDS.breakeven_band_r
    assert declared["winner_min_r"] == DEFAULT_THRESHOLDS.winner_min_r
    assert declared["commissions"] == COMMISSION_BASIS


def test_the_thresholds_are_still_unfitted() -> None:
    """`039` Part 5: ship the values, render them `unfitted`, answer them from
    the record. If one is ever fitted, that is a decision with a basis, and this
    going red is the prompt to record where the basis came from."""
    assert DEFAULT_THRESHOLDS.fitted is False


def test_the_reset_is_the_open_not_midnight(declared: dict) -> None:
    """`039` Part 3: reset is 09:30h ET. **A trade at 20:00h belongs to the day
    that is ending**, so a midnight boundary would split an evening's trades
    across two days' counters."""
    assert declared["session_reset_et"] == "09:30"
