"""Runtime settings for the eventing service.

This module defines the `Settings` class that loads configuration from
environment variables. It extends reusable base configurations from the
toolkit (e.g., database, FastAPI) and adds eventing-specific variables
like Kafka broker settings.

See Also
--------
- messaging.main : Where settings are used during app creation
- fastapi_config_patterns : The toolkit base settings classes
"""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from fastapi_config_patterns import BaseDatabaseSettings, BaseFastAPISettings


class Settings(BaseFastAPISettings, BaseDatabaseSettings):  # pylint: disable=too-many-ancestors
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="EVENTING_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(default="eventing", description="Public service identifier.")
    api_prefix: str = Field(default="/api/v1", description="Prefix applied to the HTTP API.")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/eventing",
        description="Async SQLAlchemy database URL.",
    )
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers for the event broker.",
    )
    kafka_client_id: str = Field(default="eventing", description="Kafka client identifier.")


settings = Settings()
