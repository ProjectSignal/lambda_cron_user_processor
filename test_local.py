#!/usr/bin/env python3
"""Local testing harness for the cron user processor Lambda."""

from __future__ import annotations

import json
import os
import sys
from typing import Dict

from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_handler import lambda_handler


def setup_test_environment() -> None:
    """Set required environment variables for local testing."""
    os.environ.setdefault("BASE_API_URL", "http://127.0.0.1:5000")
    os.environ.setdefault("INSIGHTS_API_KEY", "local-test-key")
    os.environ.setdefault("R2_ACCESS_KEY_ID", "test-access-key")
    os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-secret-key")
    os.environ.setdefault("R2_BUCKET_NAME", "test-bucket")
    os.environ.setdefault("R2_ENDPOINT_URL", "https://example.com")
    os.environ.setdefault("R2_REGION", "auto")
    os.environ.setdefault("CLOUDFLARE_ACCOUNT_ID", "test-account")
    os.environ.setdefault("CLOUDFLARE_API_TOKEN", "test-token")
    os.environ.setdefault("DELETE_AVATARS", "false")
    os.environ.setdefault("AWS_LAMBDA_FUNCTION_NAME", "test-user-processor")


def create_mock_event(user_id: str) -> Dict[str, str]:
    """Create a direct invocation event payload."""
    return {"body": json.dumps({"userId": user_id})}


def create_mock_context() -> Mock:
    """Create a mock Lambda context object."""
    context = Mock()
    context.function_name = "test-user-processor"
    context.function_version = "$LATEST"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-user-processor"
    context.memory_limit_in_mb = 512
    context.get_remaining_time_in_millis = lambda: 30000
    context.aws_request_id = "test-request-id"
    return context


def get_test_user_ids() -> list[str] | None:
    """Return test user IDs from the TEST_USER_IDS environment variable."""
    env_user_ids = os.getenv("TEST_USER_IDS")
    if not env_user_ids:
        print("❌ TEST_USER_IDS environment variable not set")
        print("   Example: export TEST_USER_IDS='[\"user_id_1\", \"user_id_2\"]'")
        return None

    try:
        user_ids = json.loads(env_user_ids)
        print(f"✓ Using test user IDs from environment: {user_ids}")
        return user_ids
    except json.JSONDecodeError:
        print("❌ Invalid JSON in TEST_USER_IDS environment variable")
        return None


def test_end_to_end() -> None:
    """Invoke the Lambda handler for each configured test user ID."""
    print("")
    print("=" * 50)
    print("Testing Lambda handler end-to-end")
    print("=" * 50)

    test_user_ids = get_test_user_ids()
    if not test_user_ids:
        return

    for user_id in test_user_ids:
        print("")
        print(f"--- Testing user: {user_id} ---")
        event = create_mock_event(user_id)
        context = create_mock_context()

        try:
            response = lambda_handler(event, context)
            print("📊 Response:")
            print(json.dumps(response, indent=2))
        except Exception as exc:
            print(f"❌ Handler raised exception for user {user_id}: {exc}")
            import traceback
            traceback.print_exc()


def main() -> None:
    """Entry point when running this script directly."""
    print("🚀 Starting Lambda User Processor End-to-End Test")
    print("=" * 60)

    setup_test_environment()
    test_end_to_end()

    print("")
    print("=" * 60)
    print("🏁 Testing complete!")
    print("Usage:")
    print("1. Start a local mock for the REST API defined by BASE_API_URL")
    print("2. Export TEST_USER_IDS with one or more user IDs")
    print("3. Run this script to invoke the Lambda handler")


if __name__ == "__main__":
    main()
