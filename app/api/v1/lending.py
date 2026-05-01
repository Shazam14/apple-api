from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_role
from app.models.activity import ActivityEntry, ActivityType
from app.models.borrower import Borrower, BorrowerStatus, LoanTranche
from app.models.settings import LendingSettings
from app.schemas.lending import (
    ActivityIn,
    ActivityOut,
    ActivityPatch,
    BorrowerIn,
    BorrowerOut,
    BorrowerPatch,
    SettingsIn,
    SettingsSummary,
    TrancheIn,
    TrancheOut,
)


router = APIRouter(prefix="/lending", tags=["lending"])
admin_only = require_role("admin")


def _get_settings(db: Session, owner: str) -> LendingSettings:
    s = db.query(LendingSettings).filter_by(owner_username=owner).first()
    if not s:
        s = LendingSettings(owner_username=owner)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def _tranche_days(t: LoanTranche) -> int:
    today = datetime.now(timezone.utc).date()
    released = t.released_at.date() if t.released_at.tzinfo else t.released_at.date()
    return max(1, (today - released).days + 1)


def _than_actual(b: Borrower) -> Decimal:
    total = Decimal("0")
    for t in b.tranches:
        days = _tranche_days(t)
        total += t.principal * (b.rate_snapshot / Decimal("100")) * Decimal(days)
    return total.quantize(Decimal("0.01"))


def _serialise(b: Borrower) -> dict:
    computed = _than_actual(b)
    effective = b.than_override if b.than_override is not None else computed
    total_principal = sum((t.principal for t in b.tranches), Decimal("0"))
    return {
        "id": b.id,
        "name": b.name,
        "principal": total_principal,
        "balance": b.balance,
        "rate_snapshot": b.rate_snapshot,
        "than_nakulha": b.than_nakulha,
        "than_override": b.than_override,
        "status": b.status,
        "than_actual": effective,
        "than_computed": computed,
        "than_unrealised": (effective - b.than_nakulha).quantize(Decimal("0.01")),
        "tranches": [TrancheOut.model_validate(t) for t in b.tranches],
        "activity": [ActivityOut.model_validate(a) for a in b.activity],
        "created_at": b.created_at,
        "updated_at": b.updated_at,
    }


def _re_evaluate_status(b: Borrower) -> None:
    if b.status == BorrowerStatus.OVERDUE:
        return
    effective = b.than_override if b.than_override is not None else _than_actual(b)
    if effective > 0 and b.than_nakulha >= effective:
        b.status = BorrowerStatus.PAID
    elif b.than_nakulha > 0:
        b.status = BorrowerStatus.ACTIVE


# ── Settings ────────────────────────────────────────────────────────────

@router.get("/settings/summary", response_model=SettingsSummary)
def settings_summary(
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    s = _get_settings(db, user["sub"])
    borrowers = db.query(Borrower).filter_by(owner_username=user["sub"]).all()

    sum_actual = sum((_than_actual(b) for b in borrowers), Decimal("0"))
    sum_nakulha = sum((b.than_nakulha for b in borrowers), Decimal("0"))
    sum_unreal = sum_actual - sum_nakulha
    lent_out = sum(
        (sum((t.principal for t in b.tranches), Decimal("0")) for b in borrowers),
        Decimal("0"),
    )
    than_day = (lent_out * s.daily_rate / Decimal("100")).quantize(Decimal("0.01"))

    return SettingsSummary(
        total_capital=s.total_capital,
        cash_on_hand=s.cash_on_hand,
        lent_out=lent_out,
        daily_rate=s.daily_rate,
        weekly_rate=(s.daily_rate * 7).quantize(Decimal("0.0001")),
        monthly_rate=(s.daily_rate * 30).quantize(Decimal("0.0001")),
        than_day=than_day,
        than_month=(than_day * 30).quantize(Decimal("0.01")),
        total_borrowers=len(borrowers),
        active_count=sum(1 for b in borrowers if b.status == BorrowerStatus.ACTIVE),
        overdue_count=sum(1 for b in borrowers if b.status == BorrowerStatus.OVERDUE),
        sum_than_actual=sum_actual.quantize(Decimal("0.01")),
        sum_than_unrealised=sum_unreal.quantize(Decimal("0.01")),
        sum_than_nakulha=sum_nakulha.quantize(Decimal("0.01")),
    )


@router.put("/settings", response_model=SettingsSummary)
def update_settings(
    body: SettingsIn,
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    s = _get_settings(db, user["sub"])
    s.total_capital = body.total_capital
    s.cash_on_hand = body.cash_on_hand
    s.daily_rate = body.daily_rate
    db.commit()
    return settings_summary(db=db, user=user)


# ── Borrowers ───────────────────────────────────────────────────────────

@router.get("/borrowers", response_model=list[BorrowerOut])
def list_borrowers(
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    borrowers = (
        db.query(Borrower)
        .filter_by(owner_username=user["sub"])
        .order_by(Borrower.created_at.desc())
        .all()
    )
    return [_serialise(b) for b in borrowers]


@router.post("/borrowers", response_model=BorrowerOut, status_code=status.HTTP_201_CREATED)
def create_borrower(
    body: BorrowerIn,
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    s = _get_settings(db, user["sub"])
    b = Borrower(
        owner_username=user["sub"],
        name=body.name,
        balance=body.principal + body.than,
        rate_snapshot=s.daily_rate,
        status=BorrowerStatus.ACTIVE,
    )
    db.add(b)
    db.flush()
    db.add(LoanTranche(borrower_id=b.id, principal=body.principal, than=body.than))
    db.add(
        ActivityEntry(
            borrower_id=b.id,
            activity_type=ActivityType.LOAN_RELEASED,
            detail=f"₱{body.principal} principal",
            amount=body.principal,
            destination="From cash on hand",
        )
    )
    db.commit()
    db.refresh(b)
    return _serialise(b)


@router.post(
    "/borrowers/{borrower_id}/tranches",
    response_model=BorrowerOut,
    status_code=status.HTTP_201_CREATED,
)
def add_tranche(
    borrower_id: int,
    body: TrancheIn,
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    b = (
        db.query(Borrower)
        .filter_by(id=borrower_id, owner_username=user["sub"])
        .first()
    )
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Borrower not found")

    db.add(LoanTranche(borrower_id=b.id, principal=body.principal, than=body.than))
    db.add(
        ActivityEntry(
            borrower_id=b.id,
            activity_type=ActivityType.ADDITIONAL_LOAN,
            detail=f"Additional release ₱{body.principal}",
            amount=body.principal,
            destination="From cash on hand",
        )
    )
    b.balance = b.balance + body.principal + body.than
    if b.status == BorrowerStatus.PAID:
        b.status = BorrowerStatus.ACTIVE
    db.commit()
    db.refresh(b)
    return _serialise(b)


@router.patch("/borrowers/{borrower_id}", response_model=BorrowerOut)
def patch_borrower(
    borrower_id: int,
    body: BorrowerPatch,
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    b = (
        db.query(Borrower)
        .filter_by(id=borrower_id, owner_username=user["sub"])
        .first()
    )
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Borrower not found")

    nakulha_changed = body.than_nakulha is not None
    status_explicit = body.status is not None

    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(b, field, val)

    if nakulha_changed and not status_explicit:
        _re_evaluate_status(b)

    db.commit()
    db.refresh(b)
    return _serialise(b)


@router.delete("/borrowers/{borrower_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_borrower(
    borrower_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    b = (
        db.query(Borrower)
        .filter_by(id=borrower_id, owner_username=user["sub"])
        .first()
    )
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Borrower not found")
    db.delete(b)
    db.commit()


# ── Activity ────────────────────────────────────────────────────────────

@router.get("/borrowers/{borrower_id}/activity", response_model=list[ActivityOut])
def list_activity(
    borrower_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    b = (
        db.query(Borrower)
        .filter_by(id=borrower_id, owner_username=user["sub"])
        .first()
    )
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Borrower not found")
    return [ActivityOut.model_validate(a) for a in b.activity]


@router.post(
    "/borrowers/{borrower_id}/activity",
    response_model=ActivityOut,
    status_code=status.HTTP_201_CREATED,
)
def add_activity(
    borrower_id: int,
    body: ActivityIn,
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    b = (
        db.query(Borrower)
        .filter_by(id=borrower_id, owner_username=user["sub"])
        .first()
    )
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Borrower not found")

    entry = ActivityEntry(
        borrower_id=b.id,
        activity_type=body.activity_type,
        detail=body.detail,
        amount=body.amount,
        payment_method=body.payment_method,
        destination=body.destination,
    )
    db.add(entry)

    if body.activity_type == ActivityType.MISSED_COLLECTION:
        b.status = BorrowerStatus.OVERDUE
    elif body.activity_type == ActivityType.PAYMENT_RECEIVED and body.amount:
        b.balance = b.balance - body.amount
        b.than_nakulha = b.than_nakulha + body.amount
        _re_evaluate_status(b)
    elif body.activity_type == ActivityType.LATE_INTEREST and body.amount:
        b.balance = b.balance + body.amount

    db.commit()
    db.refresh(entry)
    return ActivityOut.model_validate(entry)


def _get_activity(borrower_id: int, activity_id: int, owner: str, db: Session) -> tuple[ActivityEntry, Borrower]:
    b = db.query(Borrower).filter_by(id=borrower_id, owner_username=owner).first()
    if not b:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Borrower not found")
    a = db.query(ActivityEntry).filter_by(id=activity_id, borrower_id=borrower_id).first()
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Activity not found")
    return a, b


@router.patch("/borrowers/{borrower_id}/activity/{activity_id}", response_model=ActivityOut)
def edit_activity(
    borrower_id: int,
    activity_id: int,
    body: ActivityPatch,
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    a, b = _get_activity(borrower_id, activity_id, user["sub"], db)

    if body.amount is not None and a.amount is not None:
        delta = body.amount - a.amount
        if a.activity_type == ActivityType.LATE_INTEREST:
            b.balance = b.balance + delta
        elif a.activity_type == ActivityType.PAYMENT_RECEIVED:
            b.balance = b.balance - delta
            b.than_nakulha = b.than_nakulha + delta
        a.amount = body.amount

    if body.detail is not None:
        a.detail = body.detail

    db.commit()
    db.refresh(a)
    return ActivityOut.model_validate(a)


@router.delete("/borrowers/{borrower_id}/activity/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    borrower_id: int,
    activity_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(admin_only),
):
    a, b = _get_activity(borrower_id, activity_id, user["sub"], db)

    if a.amount is not None:
        if a.activity_type == ActivityType.LATE_INTEREST:
            b.balance = b.balance - a.amount
        elif a.activity_type == ActivityType.PAYMENT_RECEIVED:
            b.balance = b.balance + a.amount
            b.than_nakulha = max(Decimal("0"), b.than_nakulha - a.amount)

    db.delete(a)
    db.commit()
