import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INTERFACE_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    port: int = 8080
    interface: str = "eth0"
    db_path: str = "/data/gate.db"
    log_level: str = "info"

    @field_validator("interface")
    @classmethod
    def validate_interface(cls, value: str) -> str:
        normalized = value.strip()
        if not _INTERFACE_RE.fullmatch(normalized):
            raise ValueError("Invalid interface name")
        return normalized


settings = Settings()
