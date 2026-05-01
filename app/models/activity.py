import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ActivityType(str, enum.Enum):
    LOAN_RELEASED = "Loan released"
    PAYMENT_RECEIVED = "Payment received"
    PARTIAL_PAYMENT = "Partial payment"
    ADDITIONAL_LOAN = "Additional loan"
    MISSED_COLLECTION = "Missed collection"
    LATE_INTEREST = "Late interest"


class PaymentMethod(str, enum.Enum):
    CASH = "Cash"
    GCASH = "GCash"
    BANK_TRANSFER = "Bank transfer"


class ActivityEntry(Base):
    __tablename__ = "activity_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    borrower_id: Mapped[int] = mapped_column(
        ForeignKey("borrowers.id", ondelete="CASCADE"), index=True
    )
    activity_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType, name="activity_type"))
    detail: Mapped[str] = mapped_column(String(500))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        Enum(PaymentMethod, name="payment_method"), nullable=True
    )
    destination: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    borrower: Mapped["Borrower"] = relationship(back_populates="activity")
