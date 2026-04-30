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


class ActivityIn(BaseModel):
    activity_type: ActivityType
    detail: str
    amount: Optional[Decimal] = None
    payment_method: Optional[PaymentMethod] = None
    destination: Optional[str] = None


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


class BorrowerIn(BaseModel):
    name: str
    principal: Decimal


class BorrowerPatch(BaseModel):
    name: Optional[str] = None
    principal: Optional[Decimal] = None
    balance: Optional[Decimal] = None
    days_elapsed: Optional[int] = None
    status: Optional[BorrowerStatus] = None
    than_nakulha: Optional[Decimal] = None


class BorrowerOut(BaseModel):
    id: int
    name: str
    principal: Decimal
    balance: Decimal
    rate_snapshot: Decimal
    days_elapsed: int
    than_nakulha: Decimal
    status: BorrowerStatus
    than_actual: Decimal
    than_unrealised: Decimal
    activity: list[ActivityOut]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
