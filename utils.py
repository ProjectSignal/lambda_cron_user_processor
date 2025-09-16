"""Utility helpers for storage interactions used by the user processor."""

from __future__ import annotations

import gzip
import logging
import time
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from config import config

logger = logging.getLogger(__name__)


def setup_r2_client():
    """Create an R2 client with Lambda-optimised settings."""
    return boto3.client(
        "s3",
        region_name=config.R2_REGION,
        aws_access_key_id=config.R2_ACCESS_KEY_ID,
        aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
        endpoint_url=config.R2_ENDPOINT_URL,
        config=boto3.session.Config(retries={"max_attempts": 3}, max_pool_connections=5),
    )


def download_file_from_r2(r2_client, html_path: str, max_retries: int = 3, initial_backoff: float = 0.5) -> Optional[str]:
    """Download a file from R2 with retry logic suitable for Lambda."""
    bucket_name = config.R2_BUCKET_NAME
    retry_count = 0
    last_exception: Exception | None = None

    while retry_count < max_retries:
        try:
            logger.info("Downloading file: %s/%s", bucket_name, html_path)

            try:
                r2_client.head_object(Bucket=bucket_name, Key=html_path)
            except ClientError as err:
                if err.response["Error"].get("Code") == "404":
                    logger.warning("File does not exist: %s", html_path)
                    return None
                raise

            response = r2_client.get_object(Bucket=bucket_name, Key=html_path)

            if html_path.endswith(".html.gz"):
                with gzip.GzipFile(fileobj=response["Body"]) as gz:
                    return gz.read().decode("utf-8")
            return response["Body"].read().decode("utf-8")

        except Exception as exc:  # pragma: no cover - defensive logging only
            last_exception = exc
            retry_count += 1

            if retry_count < max_retries:
                wait_time = initial_backoff * (2 ** (retry_count - 1))
                logger.warning(
                    "Attempt %s failed. Retrying in %.2fs. Error: %s",
                    retry_count,
                    wait_time,
                    exc,
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    "Error downloading file %s after %s attempts. Last error: %s",
                    html_path,
                    max_retries,
                    exc,
                )
                if isinstance(exc, ClientError):
                    logger.error("Error response: %s", exc.response)
                return None

    if last_exception:
        logger.error("Failed to download %s: %s", html_path, last_exception)
    return None


__all__ = ["setup_r2_client", "download_file_from_r2"]
