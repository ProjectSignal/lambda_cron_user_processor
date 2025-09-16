"""AWS Lambda entrypoint for the cron user processor."""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from config import config
from logging_config import setup_logger
from processor import UserProcessor

logger = setup_logger(__name__)
_processor: UserProcessor | None = None


def _get_processor() -> UserProcessor:
    """Return a singleton ``UserProcessor`` instance."""
    global _processor
    if _processor is None:
        logger.info("Initialising user processor")
        config.validate()
        _processor = UserProcessor()
    return _processor


def _extract_user_id(event: Dict[str, Any]) -> Tuple[str | None, Dict[str, Any]]:
    """Extract the ``userId`` from the Lambda event payload."""
    body = event.get("body")
    if isinstance(body, str):
        try:
            body = json.loads(body or "{}")
        except json.JSONDecodeError:
            logger.warning("Unable to decode event body as JSON; falling back to top-level keys")
            body = {}

    if isinstance(body, dict) and body:
        user_id = body.get("userId")
        if user_id:
            return user_id, body

    return event.get("userId"), body if isinstance(body, dict) else {}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Standard Lambda handler accepting JSON payloads with ``userId``."""
    user_id, request_body = _extract_user_id(event)
    if not user_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "userId required",
            }),
        }

    processor = _get_processor()

    try:
        result = processor.process_user(user_id)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Unhandled error while processing user %s", user_id)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "userId": user_id,
                "error": str(exc),
            }),
        }

    success = bool(result.get("success"))
    status_code = 200 if success else result.get("statusCode", 500)

    response_body: Dict[str, Any] = {
        "userId": user_id,
        "success": success,
        "message": result.get(
            "message",
            "User processed successfully" if success else "User processing failed",
        ),
    }
    if request_body:
        response_body["requestBody"] = request_body

    return {
        "statusCode": status_code,
        "body": json.dumps(response_body),
    }


__all__ = ["lambda_handler"]
