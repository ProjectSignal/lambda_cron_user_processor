"""Runtime configuration for the cron user processor Lambda."""

from __future__ import annotations

import os
from typing import Optional


class Config:
    """Unified configuration surface for the user processor Lambda."""

    def __init__(self) -> None:
        # API configuration
        self.BASE_API_URL = self._get_env("BASE_API_URL", required=True).rstrip("/")
        self.API_KEY = self._get_env("INSIGHTS_API_KEY", required=True)
        self.API_TIMEOUT_SECONDS = int(self._get_env("API_TIMEOUT_SECONDS", default="30"))
        self.API_MAX_RETRIES = int(self._get_env("API_MAX_RETRIES", default="3"))

        # Lambda runtime settings - hardcoded since these shouldn't be environment variables
        self.DELETE_AVATARS = False  # Hardcoded to false to match .env default

        # R2 storage configuration
        self.R2_ACCESS_KEY_ID = self._get_env("R2_ACCESS_KEY_ID", required=True)
        self.R2_SECRET_ACCESS_KEY = self._get_env("R2_SECRET_ACCESS_KEY", required=True)
        self.R2_BUCKET_NAME = self._get_env("R2_BUCKET_NAME", required=True)
        self.R2_ENDPOINT_URL = self._get_env("R2_ENDPOINT_URL", required=True)
        self.R2_REGION = self._get_env("R2_REGION", default="auto")

        # Cloudflare Images configuration
        self.CLOUDFLARE_ACCOUNT_ID = self._get_env("CLOUDFLARE_ACCOUNT_ID", required=True)
        self.CLOUDFLARE_API_TOKEN = self._get_env("CLOUDFLARE_API_TOKEN", required=True)

    def _get_env(self, key: str, default: Optional[str] = None, required: bool = False) -> str:
        """Retrieve an environment variable with optional requirement enforcement."""
        value = os.getenv(key, default)
        if required and not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

    def validate(self) -> None:
        """Ensure critical configuration values are present."""
        required_vars = [
            "BASE_API_URL",
            "API_KEY",
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_BUCKET_NAME",
            "R2_ENDPOINT_URL",
            "CLOUDFLARE_ACCOUNT_ID",
            "CLOUDFLARE_API_TOKEN",
        ]
        missing = [var for var in required_vars if not getattr(self, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


__all__ = ["Config"]
