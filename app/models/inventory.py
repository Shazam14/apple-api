import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class InventoryCategory(str, enum.Enum):
    EXPENSE = "expense"
    THAN_EXTRA = "than_extra"


class InventoryEntry(Base):
    __tablename__ = "inventory_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_username: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[InventoryCategory] = mapped_column(
        Enum(InventoryCategory, name="inventory_category")
    )
    description: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
