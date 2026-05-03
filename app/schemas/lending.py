from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.activity import ActivityType, PaymentMethod
from app.models.borrower import BorrowerStatus


class SettingsIn(BaseModel):
    total_capital: Decimal
    cash_on_hand: Decimal
    daily_rate: Decimal


class SettingsSummary(BaseModel):
    total_capital: Decimal
    cash_on_hand: Decimal
    lent_out: Decimal
    daily_rate: Decimal
    weekly_rate: Decimal
    monthly_rate: Decimal
    than_day: Decimal
    than_month: Decimal
    total_borrowers: int
    active_count: int
    overdue_count: int
    sum_than_actual: Decimal
    sum_than_unrealised: Decimal
    sum_than_nakulha: Decimal
    total_balance: Decimal


class ActivityIn(BaseModel):
    activity_type: ActivityType
    detail: str
    amount: Optional[Decimal] = None
    payment_method: Optional[PaymentMethod] = None
    destination: Optional[str] = None


class ActivityPatch(BaseModel):
    amount: Optional[Decimal] = None
    detail: Optional[str] = None


class ActivityOut(BaseModel):
    id: int
    borrower_id: int
    activity_type: ActivityType
    detail: str
    amount: Optional[Decimal]
    payment_method: Optional[PaymentMethod]
    destination: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrancheOut(BaseModel):
    id: int
    principal: Decimal
    than: Decimal
    label: Optional[str] = None
    tenor_days: Optional[int] = None
    rate_pct: Optional[Decimal] = None
    late_fee_period_days: Optional[int] = None
    released_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrancheIn(BaseModel):
    principal: Decimal
    than: Decimal = Decimal("0")
    label: Optional[str] = None
    tenor_days: Optional[int] = None
    rate_pct: Optional[Decimal] = None
    late_fee_period_days: Optional[int] = None


class BorrowerIn(BaseModel):
    name: str
    principal: Decimal
    than: Decimal = Decimal("0")
    label: Optional[str] = None
    tenor_days: Optional[int] = None
    rate_pct: Optional[Decimal] = None
    late_fee_period_days: Optional[int] = None


class TranchePatch(BaseModel):
    principal: Optional[Decimal] = None
    than: Optional[Decimal] = None
    label: Optional[str] = None
    tenor_days: Optional[int] = None
    rate_pct: Optional[Decimal] = None
    late_fee_period_days: Optional[int] = None


class BorrowerPatch(BaseModel):
    name: Optional[str] = None
    balance: Optional[Decimal] = None
    status: Optional[BorrowerStatus] = None
    than_nakulha: Optional[Decimal] = None
    than_override: Optional[Decimal] = None


class BorrowerOut(BaseModel):
    id: int
    name: str
    principal: Decimal
    balance: Decimal
    rate_snapshot: Decimal
    than_nakulha: Decimal
    than_override: Optional[Decimal]
    status: BorrowerStatus
    than_actual: Decimal
    than_computed: Decimal
    than_unrealised: Decimal
    tranches: list[TrancheOut]
    activity: list[ActivityOut]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
