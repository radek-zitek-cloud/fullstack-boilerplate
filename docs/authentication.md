# Authentication Guide

Complete guide to authentication and authorization in the Full-Stack Boilerplate.

## Overview

The application uses **JWT (JSON Web Tokens)** for stateless authentication with the following features:

- **Access tokens** for API authentication
- **Refresh tokens** for session continuity
- **Role-based access control** (user/admin)
- **Account status checking** (active/inactive)

## Authentication Flow

### 1. Registration

New users can register with email and password:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 2. Login

Authenticate and receive tokens:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Making Authenticated Requests

Include the access token in the Authorization header:

```bash
curl "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Token Refresh

When the access token expires, use the refresh token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Token Types

### Access Token

- **Purpose**: Authenticate API requests
- **Expiry**: 30 days (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Storage**: localStorage (frontend)
- **Type claim**: `"type": "access"`

### Refresh Token

- **Purpose**: Obtain new access tokens
- **Expiry**: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_MINUTES`)
- **Storage**: localStorage (frontend)
- **Type claim**: `"type": "refresh"`

## Token Storage

### Current Implementation (localStorage)

```typescript
// Storage
localStorage.setItem("access_token", access_token);
localStorage.setItem("refresh_token", refresh_token);

// Retrieval
const token = localStorage.getItem("access_token");
```

**Pros:**
- Simple implementation
- Works across subdomains
- Easy to debug

**Cons:**
- Vulnerable to XSS attacks
- Accessible by JavaScript

### Recommended (httpOnly Cookies)

For production, consider switching to httpOnly cookies:

```python
# Backend response
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=True,
    samesite="lax",
    max_age=1800  # 30 minutes
)
```

**Pros:**
- Protected from XSS
- Automatic browser handling
- Better security

**Cons:**
- More complex implementation
- CSRF protection needed
- Requires cookie handling on frontend

## Password Reset Flow

### 1. Request Reset

```bash
curl -X POST "http://localhost:8000/api/v1/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Response:** `204 No Content`

**Note:** Always returns 204, even if email doesn't exist (prevents email enumeration).

### 2. Email Sent

User receives email with reset link:
```
http://localhost:5173/reset-password?token=abc123...
```

### 3. Reset Password

```bash
curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123...",
    "new_password": "newsecurepassword123"
  }'
```

**Response:** `204 No Content`

**Token Details:**
- Valid for 24 hours
- Single-use only
- Cryptographically secure random token

## Authorization

### Role-Based Access Control

#### Regular User

Can access:
- Own profile (`GET /users/me`)
- Own tasks (`/tasks/*`)
- File uploads (`/uploads/*`)

Cannot access:
- Other users' profiles
- User listing endpoint

#### Admin User

Can access:
- All regular user endpoints
- Any user's profile (`GET /users/{id}`)
- User listing (`GET /users`)

### Checking Permissions

```python
# Check if user is admin
if current_user.get("is_admin"):
    # Admin-only functionality

# Check if user owns resource
if current_user["id"] != resource.user_id and not current_user.get("is_admin"):
    raise HTTPException(403, "Not enough permissions")
```

## Account Status

### Active Account

- Can log in
- Can access all authorized endpoints
- Default status for new accounts

### Inactive Account

- Cannot log in
- Returns `400 Inactive user` on login attempt
- Can be set by admin

## Security Considerations

### Password Requirements

- Minimum 8 characters
- No complexity requirements (can add if needed)
- Hashed with bcrypt before storage

### Rate Limiting

| Endpoint | Limit |
|----------|-------|
| Login | 5/minute |
| Register | 5/minute |
| Forgot Password | 3/hour |
| Refresh Token | 10/minute |

### Best Practices

1. **Use HTTPS**: Always in production
2. **Strong SECRET_KEY**: Change default in production
3. **Short token expiry**: Consider shorter access tokens (15-30 minutes)
4. **Token rotation**: Refresh tokens should be single-use (can be implemented)
5. **Logout**: Clear tokens on logout
6. **Monitor**: Log authentication events

## Frontend Integration

### Axios Interceptor

The frontend uses an Axios interceptor for automatic token refresh:

```typescript
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem("refresh_token");
      const response = await axios.post("/auth/refresh", {
        refresh_token: refreshToken,
      });
      
      // Store new tokens
      localStorage.setItem("access_token", response.data.access_token);
      localStorage.setItem("refresh_token", response.data.refresh_token);
      
      // Retry original request
      error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
      return api(error.config);
    }
    return Promise.reject(error);
  }
);
```

### Auth Context

```typescript
const AuthContext = createContext({
  user: null,
  isAuthenticated: false,
  login: async (email, password) => {},
  logout: () => {},
});
```

## Configuration

### Environment Variables

```bash
# Token expiry (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=43200    # 30 days
REFRESH_TOKEN_EXPIRE_MINUTES=10080   # 7 days

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
```

## Troubleshooting

### "Invalid token" Error

- Token may be expired
- Token may be malformed
- Wrong token type (using refresh as access)

### "Not authenticated" Error

- Missing Authorization header
- Header format incorrect (should be "Bearer {token}")
- Token is empty or null

### "Inactive user" Error

- Account has been deactivated
- Contact administrator

### Token Refresh Loop

- Check if refresh token is also expired
- May need to re-login
- Check for race conditions in token refresh

---

For API details, see [Authentication API](./api/auth.md).
