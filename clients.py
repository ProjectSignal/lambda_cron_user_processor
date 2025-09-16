"""Service client factories for the cron user processor Lambda."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import config
from logging_config import setup_logger
from utils import setup_r2_client

logger = setup_logger(__name__)


class ApiClient:
    """Lightweight HTTP client that injects authentication headers and retries."""

    def __init__(self, base_url: str, api_key: str, timeout: int, max_retries: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._session: Session = Session()

        retry = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=(408, 429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST", "PATCH", "PUT", "DELETE"),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
        }

    def _url(self, route: str) -> str:
        route = route.lstrip("/")
        if not route.startswith("api/"):
            route = f"api/{route}"
        return f"{self._base_url}/{route}"

    def request(self, method: str, route: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute an HTTP request and return the parsed JSON body."""
        url = self._url(route)
        logger.debug("API %s %s", method.upper(), url)
        response = self._session.request(
            method=method.upper(),
            url=url,
            headers=self._headers(),
            data=json.dumps(payload or {}),
            timeout=self._timeout,
        )

        if response.status_code >= 400:
            logger.error(
                "API request failed: %s %s -> %s %s",
                method.upper(),
                url,
                response.status_code,
                response.text,
            )
            raise RuntimeError(f"API request failed with status {response.status_code}: {response.text}")

        if not response.text:
            return {}
        return response.json()

    def get(self, route: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform a GET request with optional query parameters."""
        url = self._url(route)
        logger.debug("API GET %s", url)
        response = self._session.get(
            url,
            headers=self._headers(),
            params=params,
            timeout=self._timeout,
        )

        if response.status_code >= 400:
            logger.error("API GET failed: %s -> %s %s", url, response.status_code, response.text)
            raise RuntimeError(f"API GET failed with status {response.status_code}: {response.text}")

        if not response.text:
            return {}
        return response.json()


class ServiceClients:
    """Aggregates external service clients for reuse inside the Lambda container."""

    def __init__(self) -> None:
        self.api = ApiClient(
            base_url=config.BASE_API_URL,
            api_key=config.API_KEY,
            timeout=config.API_TIMEOUT_SECONDS,
            max_retries=config.API_MAX_RETRIES,
        )
        self.r2_client = setup_r2_client()


_clients: Optional[ServiceClients] = None


def get_clients() -> ServiceClients:
    """Return a singleton ``ServiceClients`` instance."""
    global _clients
    if _clients is None:
        _clients = ServiceClients()
    return _clients


__all__ = ["ApiClient", "ServiceClients", "get_clients"]
