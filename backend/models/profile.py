from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, func

from db import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    latency_ms = Column(Integer, nullable=False, default=0)
    jitter_ms = Column(Integer, nullable=False, default=0)
    loss_percent = Column(Float, nullable=False, default=0.0)
    bandwidth_kbps = Column(Integer, nullable=False, default=0)   # 0 = unlimited
    is_builtin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
