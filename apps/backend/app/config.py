import os
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("MONGODB_URI", "MONGO_URI"),
        description="MongoDB Atlas connection string",
    )
    mongodb_database: str = Field(
        default="travel_concierge",
        validation_alias=AliasChoices("MONGODB_DATABASE", "MONGO_DATABASE"),
        description="MongoDB database name",
    )
    worker_url: str = Field(
        default="http://localhost:8001",
        validation_alias=AliasChoices("WORKER_URL"),
        description="Worker service URL",
    )
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        validation_alias=AliasChoices("CORS_ORIGINS"),
        description="Allowed CORS origins (comma-separated)",
    )

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
