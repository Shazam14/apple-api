import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class BorrowerStatus(str, enum.Enum):
    ACTIVE = "active"
    PAID = "paid"
    OVERDUE = "overdue"


class LoanTranche(Base):
    __tablename__ = "loan_tranches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    borrower_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("borrowers.id", ondelete="CASCADE"), index=True
    )
    principal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    than: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    label: Mapped[str | None] = mapped_column(String(120), nullable=True, default=None)
    released_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    borrower: Mapped["Borrower"] = relationship(back_populates="tranches")


class Borrower(Base):
    __tablename__ = "borrowers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_username: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(120))
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"))
    than_nakulha: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    than_override: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True, default=None)
    status: Mapped[BorrowerStatus] = mapped_column(
        Enum(BorrowerStatus, name="borrower_status"),
        default=BorrowerStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tranches: Mapped[list["LoanTranche"]] = relationship(
        back_populates="borrower",
        cascade="all, delete-orphan",
        order_by="LoanTranche.released_at.asc()",
    )
    activity: Mapped[list["ActivityEntry"]] = relationship(
        back_populates="borrower",
        cascade="all, delete-orphan",
        order_by="ActivityEntry.created_at.desc()",
    )
