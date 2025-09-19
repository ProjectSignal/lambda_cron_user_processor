# CI/CD Pipeline Test: Wed Sep 17 16:24:33 IST 2025

## Invocation Response

The Lambda now returns a structured body (not a JSON string) so Step Functions can read fields directly:

```json
{
  "statusCode": 200,
  "body": {
    "userId": "...",
    "success": true,
    "message": "User processed successfully",
    "profileFieldsUpdated": ["about", "bio", "workExperience"],
    "avatarChanged": false,
    "skipped": false
  }
}
```
