# Users API

Endpoints for user profile management. All endpoints require authentication.

## Base URL

```
GET /api/v1/users
```

## Endpoints

### GET /users/me

Get the current authenticated user's profile.

**Authentication:** Required (Bearer token)

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "note": "Personal note",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Errors:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: User not found

---

### PATCH /users/me

Update the current user's profile.

**Authentication:** Required (Bearer token)

**Request Body:** (All fields optional)
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "note": "Updated personal note"
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "note": "Updated personal note",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-15T12:30:00"
}
```

**Input Sanitization:**
- `first_name` and `last_name`: HTML tags are stripped
- `note`: HTML is sanitized (safe HTML allowed)

**Errors:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: User not found
- `422 Validation Error`: Invalid data format

---

### GET /users/{user_id}

Get a specific user by ID.

**Authentication:** Required (Bearer token)

**Authorization:** 
- Users can only access their own profile
- Admins can access any profile

**Parameters:**
- `user_id` (path): ID of the user to retrieve

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "note": "Personal note",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Errors:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Trying to access another user's profile (non-admin)
- `404 Not Found`: User not found

---

### GET /users

List all users (Admin only).

**Authentication:** Required (Bearer token)

**Authorization:** Admin only

**Query Parameters:**
- `skip` (optional): Number of users to skip (default: 0)
- `limit` (optional): Maximum users to return (default: 100, max: 1000)

**Response (200):**
```json
[
  {
    "id": 1,
    "email": "user1@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_admin": false,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  },
  {
    "id": 2,
    "email": "user2@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "is_active": true,
    "is_admin": false,
    "created_at": "2024-01-02T00:00:00",
    "updated_at": "2024-01-02T00:00:00"
  }
]
```

**Errors:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required

---

## User Schema

### UserResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | User ID |
| `email` | string | User email address |
| `first_name` | string \| null | User's first name |
| `last_name` | string \| null | User's last name |
| `note` | string \| null | Personal note |
| `is_active` | boolean | Whether account is active |
| `is_admin` | boolean | Whether user has admin privileges |
| `created_at` | datetime | Account creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### ProfileUpdate

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `first_name` | string | No | User's first name (max 255 chars) |
| `last_name` | string | No | User's last name (max 255 chars) |
| `note` | string | No | Personal note (max 5000 chars) |

---

## Permissions

| Endpoint | Regular User | Admin |
|----------|--------------|-------|
| `GET /users/me` | ✅ Own profile | ✅ Any profile |
| `PATCH /users/me` | ✅ Own profile | ✅ Own profile |
| `GET /users/{id}` | ✅ Own only | ✅ Any |
| `GET /users` | ❌ | ✅ |

---

## Input Sanitization

All user input is sanitized to prevent XSS attacks:

- **HTML tags** in `first_name` and `last_name` are stripped
- **HTML in `note`** is sanitized using bleach library
- **Maximum lengths** are enforced by Pydantic validators
