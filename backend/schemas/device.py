from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from schemas.profile import ProfileOut


class DeviceCreate(BaseModel):
    mac_address: str
    alias: str = ""
    ip_address: Optional[str] = None

    @field_validator("mac_address")
    @classmethod
    def normalize_mac(cls, v: str) -> str:
        return v.lower().strip()


class DeviceUpdate(BaseModel):
    alias: Optional[str] = None
    ip_address: Optional[str] = None
    profile_id: Optional[int] = None


class DeviceOut(BaseModel):
    mac_address: str
    alias: str
    ip_address: Optional[str]
    profile_id: Optional[int]
    mark_id: int
    created_at: Optional[datetime]
    profile: Optional[ProfileOut] = None

    model_config = {"from_attributes": True}
