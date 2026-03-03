from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Device(Base):
    __tablename__ = "devices"

    mac_address: Mapped[str] = mapped_column(
        String, primary_key=True
    )  # aa:bb:cc:dd:ee:ff
    alias: Mapped[str] = mapped_column(String, nullable=False, default="")
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("profiles.id"), nullable=True
    )
    mark_id: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True
    )  # nfmark value, 1-based
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
