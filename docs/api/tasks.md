# Tasks API

Endpoints for task management. All endpoints require authentication.

## Base URL

```
/api/v1/tasks
```

## Endpoints

### GET /tasks

Get a paginated list of tasks for the current user.

**Authentication:** Required (Bearer token)

**Query Parameters:**
- `skip` (optional): Number of tasks to skip (default: 0)
- `limit` (optional): Maximum tasks to return (default: 100, max: 1000)

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Complete project documentation",
    "description": "Write comprehensive docs for the API",
    "completed": false,
    "user_id": 1,
    "created_at": "2024-01-01T10:00:00",
    "updated_at": "2024-01-01T10:00:00"
  },
  {
    "id": 2,
    "title": "Fix bug in authentication",
    "description": "Users reporting login issues",
    "completed": true,
    "user_id": 1,
    "created_at": "2024-01-02T14:30:00",
    "updated_at": "2024-01-03T09:15:00"
  }
]
```

**Errors:**
- `401 Unauthorized`: Not authenticated

---

### POST /tasks

Create a new task.

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "title": "New task title",
  "description": "Task description (optional)",
  "completed": false
}
```

**Response (201):**
```json
{
  "id": 3,
  "title": "New task title",
  "description": "Task description (optional)",
  "completed": false,
  "user_id": 1,
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:00"
}
```

**Errors:**
- `401 Unauthorized`: Not authenticated
- `422 Validation Error`: Title is required or too long

---

### GET /tasks/{task_id}

Get a specific task by ID.

**Authentication:** Required (Bearer token)

**Parameters:**
- `task_id` (path): ID of the task to retrieve

**Response (200):**
```json
{
  "id": 1,
  "title": "Complete project documentation",
  "description": "Write comprehensive docs for the API",
  "completed": false,
  "user_id": 1,
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

**Errors:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Task not found or doesn't belong to user

---

### PUT /tasks/{task_id}

Update a specific task.

**Authentication:** Required (Bearer token)

**Parameters:**
- `task_id` (path): ID of the task to update

**Request Body:** (All fields optional)
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "completed": true
}
```

**Response (200):**
```json
{
  "id": 1,
  "title": "Updated title",
  "description": "Updated description",
  "completed": true,
  "user_id": 1,
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-15T15:30:00"
}
```

**Errors:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Task not found
- `422 Validation Error`: Invalid data

---

### DELETE /tasks/{task_id}

Delete a specific task.

**Authentication:** Required (Bearer token)

**Parameters:**
- `task_id` (path): ID of the task to delete

**Response:** `204 No Content`

**Errors:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Task not found

**Note:** This action is permanent and cannot be undone.

---

## Task Schema

### TaskResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Task ID |
| `title` | string | Task title |
| `description` | string \| null | Task description |
| `completed` | boolean | Whether task is completed |
| `user_id` | integer | ID of task owner |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### TaskCreate

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Task title (1-255 chars) |
| `description` | string | No | Task description |
| `completed` | boolean | No | Initial completion status (default: false) |

### TaskUpdate

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | New title (1-255 chars) |
| `description` | string | No | New description |
| `completed` | boolean | No | New completion status |

---

## Permissions

All tasks are user-scoped:
- Users can only access their own tasks
- Users can only create tasks for themselves
- Users can only update/delete their own tasks
- Admin users do not have special access to other users' tasks

---

## Usage Examples

### Create a Task
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false
  }'
```

### List Tasks with Pagination
```bash
curl "http://localhost:8000/api/v1/tasks?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Mark Task as Complete
```bash
curl -X PUT "http://localhost:8000/api/v1/tasks/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true
  }'
```
