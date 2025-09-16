# Lambda Cron User Processor – Migration Summary

## Highlights
- ✅ Replaced direct MongoDB usage with REST integrations via `clients.ApiClient`
- ✅ Standardised Lambda entry point (`lambda_handler.py`) to accept JSON payloads with `userId`
- ✅ Consolidated configuration (`config/settings.py`) and logging (`logging_config.py`) with shared platform patterns
- ✅ Preserved scraping, avatar management, and R2 download behaviour from the legacy processor

## Key Changes

### Handler & Orchestration
- `lambda_handler.py` exposes `_extract_user_id` mirroring other Lambdas (body JSON → fallback to top-level keys).
- Singleton `UserProcessor` initialises after `config.validate()` to reuse HTTP/R2 clients across invocations.
- Responses follow the standard `{statusCode, body}` contract with success/error messaging.

### Service Clients & Persistence
- `clients.py` introduces an authenticated, retry-aware REST client plus shared R2 bootstrap.
- `processor.UserProcessor` routes persistence through the following API surfaces:
  - `users.getById` → fetch source profile document
  - `users.updateProfile` → write processed profile data and avatar URL
  - `users.markError` → stamp processing errors
  - Each route includes inline `# API Route:` annotations describing payloads.

### Business Logic
- Scraping pipeline (`bs/scrape.py`) now consumes the shared logger helper.
- Avatar uploads reuse/deletes only when necessary; Cloudflare flows unchanged aside from logging alignment.
- Profile updates set `descriptionGeneratedAt` using ISO UTC timestamps for API transmission.

### Tooling & Scripts
- `validate_structure.py` and `test_local.py` refreshed for the REST-first architecture.
- `Dockerfile` packages the new layout (`lambda_handler.py`, `clients.py`, `config/`, etc.).
- Requirements trimmed to remove Mongo dependencies and add explicit `urllib3` for retry support.

## Environment Variables
```
BASE_API_URL=https://api.example.com
INSIGHTS_API_KEY=***
R2_ACCESS_KEY_ID=***
R2_SECRET_ACCESS_KEY=***
R2_BUCKET_NAME=***
R2_ENDPOINT_URL=***
R2_REGION=auto
CLOUDFLARE_ACCOUNT_ID=***
CLOUDFLARE_API_TOKEN=***
DELETE_AVATARS=true
PROCESSING_TIMEOUT=30
WORKER_ID=lambda-cron-user-processor
```

## Testing Aids
1. `python3 validate_structure.py`
2. `python3 test_local.py` (requires mock REST endpoints or stubs)
3. `docker build -t user-processor .`

The cron user processor now mirrors the Brace Lambda conventions and is ready for API-backed end-to-end validation.
