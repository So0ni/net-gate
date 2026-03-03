from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from db import Base


class Device(Base):
    __tablename__ = "devices"

    mac_address = Column(String, primary_key=True)   # aa:bb:cc:dd:ee:ff
    alias = Column(String, nullable=False, default="")
    ip_address = Column(String, nullable=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=True)
    mark_id = Column(Integer, nullable=False, unique=True)  # nfmark value, 1-based
    created_at = Column(DateTime, server_default=func.now())
