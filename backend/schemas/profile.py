from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ProfileBase(BaseModel):
    name: str
    latency_ms: int = 0
    jitter_ms: int = 0
    loss_percent: float = 0.0
    bandwidth_kbps: int = 0  # 0 = unlimited


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    latency_ms: Optional[int] = None
    jitter_ms: Optional[int] = None
    loss_percent: Optional[float] = None
    bandwidth_kbps: Optional[int] = None


class ProfileOut(ProfileBase):
    id: int
    is_builtin: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
