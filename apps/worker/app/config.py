import os
from typing import Optional
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    backend_url: str = Field(
        default="http://localhost:8000",
        validation_alias=AliasChoices("BACKEND_URL"),
        description="Backend API base URL",
    )
    host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("HOST"))
    port: int = Field(default=8001, validation_alias=AliasChoices("PORT"))

    # Policy Defaults
    max_extra_fare: float = Field(default=5000.0, validation_alias=AliasChoices("MAX_EXTRA_FARE"))
    max_stops: int = Field(default=1, validation_alias=AliasChoices("MAX_STOPS"))
    cabin_class: str = Field(default="Economy", validation_alias=AliasChoices("CABIN_CLASS"))
    min_layover_minutes: int = Field(default=60, validation_alias=AliasChoices("MIN_LAYOVER_MINUTES"))
    max_layover_minutes: int = Field(default=360, validation_alias=AliasChoices("MAX_LAYOVER_MINUTES"))

    # Optional LLM Key
    openai_api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("OPENAI_API_KEY"))

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = WorkerSettings()
