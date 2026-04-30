from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, String, DateTime, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LendingSettings(Base):
    __tablename__ = "lending_settings"
    __table_args__ = (UniqueConstraint("owner_username", name="uq_lending_settings_owner"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_username: Mapped[str] = mapped_column(String(64), index=True)
    total_capital: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    cash_on_hand: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
