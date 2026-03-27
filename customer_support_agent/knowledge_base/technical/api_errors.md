# API Errors

## Overview

The CloudSync Pro REST API uses standard HTTP status codes. This guide covers common error responses and how to resolve them. All API responses include an `error_code` field and a human-readable `message`.

## Common Error Codes

### 401 Unauthorized -- `AUTH_INVALID_TOKEN`

**Cause**: Your API key is missing, expired, or invalid.

**Troubleshooting**:
1. Verify your API key in **Settings > API > Keys**
2. Check that the `Authorization` header is formatted correctly: `Authorization: Bearer sk_live_xxxxxxxxxxxx`
3. Ensure the key has not been revoked or rotated
4. API keys expire after 365 days. Regenerate at **Settings > API > Keys > Rotate**

### 403 Forbidden -- `AUTH_INSUFFICIENT_PERMISSIONS`

**Cause**: Your API key does not have the required scope for this endpoint.

**Troubleshooting**:
1. Check the key's scopes at **Settings > API > Keys > [Key Name] > Permissions**
2. Common required scopes: `projects:read`, `projects:write`, `tasks:read`, `tasks:write`, `users:read`
3. Create a new key with the appropriate scopes if needed

### 429 Too Many Requests -- `RATE_LIMIT_EXCEEDED`

**Cause**: You have exceeded the rate limit for your plan.

**Rate limits by plan**:
- Free: 100 requests/day
- Pro: 10,000 requests/day (approximately 7 requests/minute sustained)
- Enterprise: 100,000 requests/day

**Troubleshooting**:
1. Check the `X-RateLimit-Remaining` and `X-RateLimit-Reset` response headers
2. Implement exponential backoff in your integration
3. Cache responses where possible to reduce API calls
4. Consider upgrading your plan for higher limits

### 500 Internal Server Error -- `INTERNAL_ERROR`

**Cause**: An unexpected error occurred on CloudSync Pro servers.

**Troubleshooting**:
1. Retry the request after 30 seconds
2. Check our status page at status.cloudsyncpro.com for ongoing incidents
3. If the error persists, contact support with the `X-Request-Id` header value from the response
4. Include the full request payload (redact sensitive data) in your support ticket

### 422 Unprocessable Entity -- `VALIDATION_ERROR`

**Cause**: The request body contains invalid data.

**Troubleshooting**:
1. Check the `details` array in the response for specific field errors
2. Verify required fields are present: refer to the API docs at docs.cloudsyncpro.com/api
3. Ensure date fields use ISO 8601 format (`YYYY-MM-DDTHH:mm:ssZ`)
4. Check string length limits (task titles: 255 chars, descriptions: 10,000 chars)
