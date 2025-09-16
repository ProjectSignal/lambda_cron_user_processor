"""Shared logging helpers for the cron user processor Lambda."""

from __future__ import annotations

import logging
import sys

_ROOT_CONFIGURED = False


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configure and return a module-specific logger."""
    global _ROOT_CONFIGURED

    if not _ROOT_CONFIGURED:
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove pre-existing handlers to avoid duplicate logs in Lambda/container runs
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(level)
        stdout_handler.setFormatter(formatter)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.WARNING)
        stderr_handler.setFormatter(formatter)

        root_logger.addHandler(stdout_handler)
        root_logger.addHandler(stderr_handler)
        _ROOT_CONFIGURED = True

    return logging.getLogger(name)


__all__ = ["setup_logger"]
