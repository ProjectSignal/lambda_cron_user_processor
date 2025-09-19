#!/usr/bin/env python3

import os
import json
import sys
from lambda_handler import lambda_handler

# Load environment variables from both local and parent .env files
import sys
sys.path.append('..')
from dotenv import load_dotenv

# Load from local .env first (higher priority)
load_dotenv('.env')
# Load from parent .env as fallback
load_dotenv('../.env')

# Override with any hardcoded values if needed (for testing only)
# os.environ["BASE_API_URL"] = "https://your-base-api-url.com"  # Uncomment to override
# os.environ["INSIGHTS_API_KEY"] = "your-api-key-here"  # Uncomment to override

print(f"🔧 API Configuration:")
print(f"   - BASE_API_URL: {'✅ ' + os.getenv('BASE_API_URL', 'Not Set') if os.getenv('BASE_API_URL') else '❌ Missing'}")
print(f"   - INSIGHTS_API_KEY: {'✅ Available' if os.getenv('INSIGHTS_API_KEY') else '❌ Missing'}")
print(f"   - Full API Endpoint: {os.getenv('BASE_API_URL', 'NOT_SET')}/api/users")
print()
print(f"🗄️ Storage Configuration:")
print(f"   - R2_BUCKET_NAME: {'✅ ' + os.getenv('R2_BUCKET_NAME', 'Not Set') if os.getenv('R2_BUCKET_NAME') else '❌ Missing'}")
print(f"   - R2_ENDPOINT_URL: {'✅ Available' if os.getenv('R2_ENDPOINT_URL') else '❌ Missing'}")
print()
print(f"☁️ Cloudflare Configuration:")
print(f"   - CLOUDFLARE_ACCOUNT_ID: {'✅ Available' if os.getenv('CLOUDFLARE_ACCOUNT_ID') else '❌ Missing'}")
print(f"   - CLOUDFLARE_API_TOKEN: {'✅ Available' if os.getenv('CLOUDFLARE_API_TOKEN') else '❌ Missing'}")
print("-" * 50)

# Mock AWS Lambda context
class MockContext:
    def __init__(self):
        self.function_name = "user_processor_test"
        self.function_version = "$LATEST"
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:user_processor_test"
        self.memory_limit_in_mb = 512
        self.remaining_time_in_millis = lambda: 300000

def test_lambda():
    """Test the Lambda function with the provided userId"""

    # Load test event
    with open('test_event.json', 'r') as f:
        event = json.load(f)

    print(f"🚀 Testing Lambda with event: {event}")
    print("-" * 50)

    # Create mock context
    context = MockContext()

    try:
        # Call the Lambda handler
        result = lambda_handler(event, context)

        print(f"✅ Lambda execution completed!")
        print(f"Status Code: {result['statusCode']}")

        # Parse and display the response
        response_body = result.get('body', {})
        if isinstance(response_body, str):
            response_body = json.loads(response_body)

        if result['statusCode'] == 200 and response_body.get('success'):
            print(f"🎉 SUCCESS!")
            print(f"📊 User Processing Complete:")
            print(f"   - User ID: {response_body.get('userId')}")
            print(f"   - Status: {response_body.get('message')}")
            print(f"   - Profile fields updated: {response_body.get('profileFieldsUpdated', [])}")
            print(f"   - Avatar changed: {response_body.get('avatarChanged')}")
            print(f"   - ✅ User profile has been processed and updated via API")
            print()
            print("📝 Note: User profile data is now stored via API call")
            print("    Profile data includes scraped information and avatar processing")

        else:
            print(f"❌ FAILED!")
            print(f"Error: {response_body.get('error', 'Unknown error')}")
            print(f"Message: {response_body.get('message', 'No message provided')}")

    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lambda()
