from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ProfileBase(BaseModel):
    name: str
    latency_ms: int = 0
    jitter_ms: int = 0
    loss_percent: float = 0.0
    bandwidth_kbps: int = 0  # 0 = unlimited

    @field_validator("latency_ms", "jitter_ms", "bandwidth_kbps")
    @classmethod
    def non_negative_int_fields(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Value must be >= 0")
        return value

    @field_validator("loss_percent")
    @classmethod
    def loss_percent_in_range(cls, value: float) -> float:
        if value < 0 or value > 100:
            raise ValueError("loss_percent must be between 0 and 100")
        return value


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    latency_ms: Optional[int] = None
    jitter_ms: Optional[int] = None
    loss_percent: Optional[float] = None
    bandwidth_kbps: Optional[int] = None

    @field_validator("latency_ms", "jitter_ms", "bandwidth_kbps")
    @classmethod
    def non_negative_optional_int_fields(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 0:
            raise ValueError("Value must be >= 0")
        return value

    @field_validator("loss_percent")
    @classmethod
    def optional_loss_percent_in_range(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and (value < 0 or value > 100):
            raise ValueError("loss_percent must be between 0 and 100")
        return value


class ProfileOut(ProfileBase):
    id: int
    is_builtin: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
