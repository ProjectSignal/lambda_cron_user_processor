"""Configuration package exposing a singleton Config instance."""

from __future__ import annotations

from dotenv import load_dotenv

from .settings import Config

# Load environment variables for local execution scenarios
load_dotenv()

# Export a singleton to mirror existing import style (``from config import config``)
config = Config()

__all__ = ["Config", "config"]
