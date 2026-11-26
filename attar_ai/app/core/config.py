"""
core/config.py
--------------
Centralized application configuration using Pydantic Settings.
All environment variables are loaded and validated here.
"""

import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Provider Selection
    llm_provider: Literal["openai", "cloudflare", "groq"] = Field(
        default="cloudflare",
        description="LLM provider to use: openai, cloudflare, or groq",
    )

    # OpenAI Settings
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    openai_timeout: float = Field(default=30.0, description="OpenAI request timeout in seconds")

    # Cloudflare Workers AI Settings
    cloudflare_account_id: str = Field(default="", description="Cloudflare account ID")
    cloudflare_api_token: str = Field(default="", description="Cloudflare API token")
    cloudflare_model: str = Field(
        default="@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        description="Cloudflare model name",
    )
    cloudflare_timeout: float = Field(default=60.0, description="Cloudflare request timeout in seconds")

    # Groq Settings
    groq_api_key: str = Field(default="", description="Groq API key")
    groq_model: str = Field(default="openai/gpt-oss-20b", description="Groq model name")
    groq_timeout: float = Field(default=30.0, description="Groq request timeout in seconds")

    # API Hardening
    allowed_origins: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000,https://attar-ai-automatic-agent-1.onrender.com",
        description="Comma-separated list of allowed CORS origins",
    )
    rate_limit_per_minute: int = Field(default=30, description="Max requests per client IP per minute")
    max_message_length: int = Field(default=2000, description="Maximum characters per chat message")

    # Google Sheets Inventory
    google_sheet_id: str = Field(default="", description="Google Sheet ID from the sheet URL")
    google_sheet_name: str = Field(default="Products", description="Worksheet tab name")
    google_http_timeout: float = Field(default=30.0, description="Google Sheets request timeout in seconds")
    google_sheets_max_retries: int = Field(default=3, description="Max retries for transient Google Sheets failures")
    google_sheets_backoff_base: float = Field(default=1.5, description="Backoff base for Google Sheets retries")
    google_service_account_json: str = Field(default="", description="Service account JSON content or file path")

    # Conversation
    max_history_turns: int = Field(default=20, description="Maximum history turns to send to the model")

    # System Prompt
    system_prompt_path: str = Field(
        default="prompts/system_prompt.txt",
        description="Path to the system prompt file",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    def get_allowed_origins_list(self) -> list[str]:
        """Parse comma-separated allowed origins into a list."""
        origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        return origins or ["*"]

    def get_active_model(self) -> str:
        """Get the model name for the currently active provider."""
        if self.llm_provider == "openai":
            return self.openai_model
        elif self.llm_provider == "cloudflare":
            return self.cloudflare_model
        elif self.llm_provider == "groq":
            return self.groq_model
        return self.openai_model

    def get_active_timeout(self) -> float:
        """Get the timeout for the currently active provider."""
        if self.llm_provider == "openai":
            return self.openai_timeout
        elif self.llm_provider == "cloudflare":
            return self.cloudflare_timeout
        elif self.llm_provider == "groq":
            return self.groq_timeout
        return self.openai_timeout

    def validate_provider_config(self) -> None:
        """Validate that the active provider has required configuration."""
        if self.llm_provider == "cloudflare":
            if not self.cloudflare_account_id or not self.cloudflare_api_token:
                raise RuntimeError(
                    "LLM_PROVIDER=cloudflare requires CLOUDFLARE_ACCOUNT_ID and "
                    "CLOUDFLARE_API_TOKEN in .env."
                )
        elif self.llm_provider == "groq":
            if not self.groq_api_key:
                raise RuntimeError(
                    "LLM_PROVIDER=groq requires GROQ_API_KEY in .env."
                )
        elif self.llm_provider == "openai":
            if not self.openai_api_key:
                raise RuntimeError(
                    "LLM_PROVIDER=openai requires OPENAI_API_KEY in .env."
                )


# Global settings instance
settings = Settings()
settings.validate_provider_config()