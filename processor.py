"""User profile processing orchestration for the cron user processor Lambda."""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from bs.scrape import scrape_profile_data
from cloudflare_handler import CloudflareImageHandler
from clients import ServiceClients, get_clients
from config import config
from logging_config import setup_logger
from utils import download_file_from_r2


class UserProcessor:
    """Coordinate user profile scraping and persistence via REST APIs."""

    def __init__(self, *, config_obj=config, clients: Optional[ServiceClients] = None) -> None:
        self.config = config_obj
        self.logger = setup_logger(__name__)
        self.clients = clients or get_clients()
        self.api = self.clients.api
        self.r2_client = self.clients.r2_client
        self.cloudflare_handler = CloudflareImageHandler()

    def process_user(self, user_id: str) -> Dict[str, Any]:
        """Process a single user and return a structured result payload."""
        self.logger.info("Processing user %s", user_id)

        try:
            user = self._fetch_user(user_id)
        except Exception as exc:  # pragma: no cover - API failures logged below
            self.logger.error("Failed to load user %s: %s", user_id, exc)
            return {
                "success": False,
                "statusCode": 404,
                "message": f"User {user_id} not found",
            }

        if not user:
            self.logger.warning("User %s responded with empty payload", user_id)
            return {
                "success": False,
                "statusCode": 404,
                "message": "User not found",
            }

        if user.get("descriptionGenerated"):
            self.logger.info("User %s already processed; skipping", user_id)
            return {
                "success": True,
                "statusCode": 200,
                "message": "User already processed",
            }

        html_path = user.get("htmlPath")
        if not html_path:
            return self._handle_error(user_id, "No htmlPath found on user document")

        if not user.get("scrapped"):
            return self._handle_error(user_id, "User not marked as scrapped")

        html_content = download_file_from_r2(self.r2_client, html_path)
        if not html_content:
            return self._handle_error(user_id, "Failed to download HTML content from storage")

        try:
            profile_data = scrape_profile_data(html_content)
        except Exception as exc:  # pragma: no cover - defensive logging
            return self._handle_error(user_id, f"Error extracting profile data: {exc}")

        if not profile_data:
            return self._handle_error(user_id, "Failed to extract profile data from HTML")

        existing_avatar = user.get("avatarURL")
        new_avatar_url = self._sync_avatar(user_id, profile_data, existing_avatar)

        try:
            self._persist_profile(user_id, profile_data, new_avatar_url)
        except Exception as exc:  # pragma: no cover - API failures logged inside helper
            return self._handle_error(user_id, f"Failed to update user via API: {exc}")

        self.logger.info("Successfully processed user %s", user_id)
        return {
            "success": True,
            "statusCode": 200,
            "message": "User processed successfully",
        }

    def _fetch_user(self, user_id: str) -> Dict[str, Any]:
        """Retrieve the user payload from the REST API."""
        # API Route: users.getById, Input: {"userId": user_id}, Output: {"data": {...}}
        response = self.api.get(f"users/{user_id}")
        return response.get("data", response)

    def _persist_profile(self, user_id: str, profile_data: Dict[str, Any], avatar_url: Optional[str]) -> None:
        """Persist scraped profile data back through the REST API."""
        payload = {
            "userId": user_id,
            "profileData": profile_data,
            "descriptionGenerated": True,
            "descriptionGeneratedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        if avatar_url:
            payload["avatarURL"] = avatar_url

        # API Route: users.updateProfile, Input: payload, Output: {"success": bool}
        result = self.api.request("PATCH", f"users/{user_id}", payload)
        if not result.get("success", True):
            raise RuntimeError(f"Profile update failed for user {user_id}: {result}")

    def _sync_avatar(
        self,
        user_id: str,
        profile_data: Dict[str, Any],
        existing_avatar: Optional[str],
    ) -> Optional[str]:
        """Upload or reuse the user's avatar and return the resulting URL."""
        if not profile_data.get("avatarURL"):
            return existing_avatar

        incoming_avatar = profile_data.pop("avatarURL")
        if existing_avatar and existing_avatar == incoming_avatar:
            self.logger.info("Avatar URL unchanged for user %s; reusing existing asset", user_id)
            return existing_avatar

        if existing_avatar and self.config.DELETE_AVATARS:
            self.cloudflare_handler.delete_image(existing_avatar)

        new_avatar_response = self.cloudflare_handler.upload_image(incoming_avatar)
        if new_avatar_response and new_avatar_response.get("success"):
            variants = new_avatar_response.get("result", {}).get("variants", [])
            if variants:
                self.logger.info("Uploaded new avatar for user %s", user_id)
                return variants[0]

        self.logger.warning("Failed to upload avatar for user %s; proceeding without change", user_id)
        return existing_avatar

    def _handle_error(self, user_id: str, error_message: str) -> Dict[str, Any]:
        """Mark the user as errored and return a standard error payload."""
        self.logger.error("User %s: %s", user_id, error_message)
        try:
            payload = {
                "userId": user_id,
                "errorMessage": error_message,
            }
            # API Route: users.markError, Input: payload, Output: {"success": bool}
            self.api.request("POST", "users/mark-error", payload)
        except Exception as exc:  # pragma: no cover - secondary failure logging
            self.logger.error("Failed to mark user %s as error: %s", user_id, exc)

        return {
            "success": False,
            "statusCode": 500,
            "message": error_message,
        }


__all__ = ["UserProcessor"]
