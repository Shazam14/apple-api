"""Regression tests for _than_actual() — the per-tranche interest calc.

Origin: Helen Yap report 2026-05-14 (tranche #102, ₱60k, rate zeroed in UI but
phantom ₱900 interest applied). Root cause was on the frontend, but these tests
lock the API contract: rate_pct=0 must mean zero, rate_pct=None must inherit.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.api.v1.lending import _than_actual

PH_TZ = ZoneInfo("Asia/Manila")


def _mk_tranche(*, id_=1, principal="60000", rate_pct, days_ago=0):
    return SimpleNamespace(
        id=id_,
        principal=Decimal(principal),
        than=Decimal("0"),
        rate_pct=Decimal(rate_pct) if rate_pct is not None else None,
        tenor_days=None,
        late_fee_period_days=None,
        released_at=datetime.now(PH_TZ) - timedelta(days=days_ago),
    )


def _mk_borrower(*, rate_snapshot="1.5", tranches=()):
    return SimpleNamespace(
        id=1,
        rate_snapshot=Decimal(rate_snapshot),
        than_nakulha=Decimal("0"),
        than_override=None,
        balance=Decimal("0"),
        tranches=list(tranches),
        activity=[],
    )


def test_rate_pct_zero_means_no_interest():
    t = _mk_tranche(principal="60000", rate_pct="0", days_ago=0)
    b = _mk_borrower(rate_snapshot="1.5", tranches=[t])
    assert _than_actual(b) == Decimal("0.00")


def test_rate_pct_null_inherits_settings_rate():
    t = _mk_tranche(principal="60000", rate_pct=None, days_ago=0)
    b = _mk_borrower(rate_snapshot="1.5", tranches=[t])
    assert _than_actual(b) == Decimal("900.00")


def test_rate_pct_explicit_overrides_settings():
    t = _mk_tranche(principal="10000", rate_pct="2", days_ago=0)
    b = _mk_borrower(rate_snapshot="5", tranches=[t])
    assert _than_actual(b) == Decimal("200.00")
