from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    port: int = 8080
    interface: str = "eth0"
    db_path: str = "/data/gate.db"
    log_level: str = "info"


settings = Settings()
