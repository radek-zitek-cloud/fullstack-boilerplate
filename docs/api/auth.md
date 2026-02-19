# Authentication API

Endpoints for user authentication, registration, and password management.

## Endpoints

### POST /auth/login

Authenticate a user and obtain JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `401 Unauthorized`: Invalid email or password
- `400 Bad Request`: User account is inactive
- `429 Too Many Requests`: Rate limit exceeded (5/minute)

**Rate Limit:** 5 requests per minute

---

### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Errors:**
- `400 Bad Request`: Email already registered
- `422 Validation Error`: Password too short or invalid email format
- `429 Too Many Requests`: Rate limit exceeded (5/minute)

**Rate Limit:** 5 requests per minute

---

### POST /auth/refresh

Refresh access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `401 Unauthorized`: Invalid or expired refresh token
- `429 Too Many Requests`: Rate limit exceeded (10/minute)

**Rate Limit:** 10 requests per minute

---

### POST /auth/change-password

Change the current user's password (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword123"
}
```

**Response:** `204 No Content`

**Errors:**
- `400 Bad Request`: Current password is incorrect
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: User not found

---

### POST /auth/forgot-password

Request a password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `204 No Content`

**Note:** Always returns 204, even if email doesn't exist (prevents email enumeration).

**Rate Limit:** 3 requests per hour

---

### POST /auth/reset-password

Reset password using a token from email.

**Request Body:**
```json
{
  "token": "abc123...",
  "new_password": "newpassword123"
}
```

**Response:** `204 No Content`

**Errors:**
- `400 Bad Request`: Invalid or expired token

**Note:** Token is valid for 24 hours and can only be used once.

---

## Token Types

### Access Token
- **Valid for:** 30 days (configurable)
- **Usage:** Authenticate API requests
- **Format:** JWT

### Refresh Token
- **Valid for:** 7 days (configurable)
- **Usage:** Obtain new access tokens
- **Format:** JWT

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/login` | 5/minute |
| `/register` | 5/minute |
| `/refresh` | 10/minute |
| `/forgot-password` | 3/hour |
