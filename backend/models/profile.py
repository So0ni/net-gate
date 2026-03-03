from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jitter_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    loss_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    bandwidth_kbps: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # 0 = unlimited
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
