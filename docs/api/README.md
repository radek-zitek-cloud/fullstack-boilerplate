# API Reference

Complete reference for the Full-Stack Boilerplate REST API.

## Base URL

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://your-domain.com/api/v1`

## Authentication

Most endpoints require authentication via Bearer token:

```http
Authorization: Bearer <access_token>
```

See [Authentication Guide](../authentication.md) for details on obtaining tokens.

## API Sections

- [Authentication](./auth.md) - Login, register, password reset
- [Users](./users.md) - User management and profiles
- [Tasks](./tasks.md) - Task CRUD operations
- [Uploads](./uploads.md) - File upload handling

## Common Response Formats

### Success Response

```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response

```json
{
  "detail": "Error message here"
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Request successful, no response body |
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Input validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Authentication endpoints**: 5 requests/minute
- **Password reset**: 3 requests/hour
- **Token refresh**: 10 requests/minute
- **Other endpoints**: 100 requests/minute

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1640995200
```

## Interactive Documentation

When the backend is running, you can explore the API interactively:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
