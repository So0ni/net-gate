from datetime import datetime
import re
from typing import Optional

from pydantic import BaseModel, field_validator

_MAC_RE = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")


class DeviceCreate(BaseModel):
    mac_address: str
    alias: str = ""
    ip_address: Optional[str] = None

    @field_validator("mac_address")
    @classmethod
    def normalize_mac(cls, v: str) -> str:
        normalized = v.lower().strip()
        if not _MAC_RE.fullmatch(normalized):
            raise ValueError("Invalid MAC address format, expected aa:bb:cc:dd:ee:ff")
        return normalized


class DeviceUpdate(BaseModel):
    alias: Optional[str] = None
    ip_address: Optional[str] = None
    profile_id: Optional[int] = None


class DeviceOut(BaseModel):
    mac_address: str
    alias: str
    ip_address: Optional[str]
    profile_id: Optional[int]
    online: bool = False
    mark_id: int
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
