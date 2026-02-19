# File Uploads API

Endpoints for file upload and retrieval. All endpoints require authentication.

## Base URL

```
/api/v1/uploads
```

## Endpoints

### POST /uploads/upload

Upload a file to the server.

**Authentication:** Required (Bearer token)

**Content-Type:** `multipart/form-data`

**Request Body:**
- `file` (required): File to upload

**Allowed File Types:**
- Images: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- Documents: `application/pdf`, `text/plain`

**Max File Size:** 10 MB

**Response (201):**
```json
{
  "filename": "550e8400-e29b-41d4-a716-446655440000.jpg",
  "original_name": "vacation_photo.jpg",
  "content_type": "image/jpeg",
  "size": 2048576,
  "url": "/uploads/550e8400-e29b-41d4-a716-446655440000.jpg"
}
```

**Errors:**
- `401 Unauthorized`: Not authenticated
- `413 Request Entity Too Large`: File exceeds 10MB
- `415 Unsupported Media Type`: File type not allowed

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/v1/uploads/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/photo.jpg"
```

---

### GET /uploads/uploads/{filename}

Download a previously uploaded file.

**Authentication:** Required (Bearer token)

**Parameters:**
- `filename` (path): Filename returned from upload (UUID format)

**Response (200):** File content with appropriate Content-Type header

**Errors:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: File not found

**Example (cURL):**
```bash
curl "http://localhost:8000/api/v1/uploads/uploads/550e8400-e29b-41d4-a716-446655440000.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -o downloaded_file.jpg
```

---

## Security Features

### File Validation

- **Type validation**: Only allowed MIME types are accepted
- **Size limit**: Maximum 10MB per file
- **Unique filenames**: Files are stored with UUID names to prevent overwriting and information disclosure

### Storage

- Files are stored in the `uploads/` directory
- Directory is outside web root for security
- Original filenames are preserved in metadata but not used for storage

### Access Control

- All file operations require authentication
- Files are not namespaced by user (all authenticated users can access any file)
- Future enhancement: User-scoped file access

---

## File Lifecycle

1. **Upload**: File is validated and stored with UUID filename
2. **Storage**: File saved to `uploads/` directory
3. **Access**: Retrieved by UUID filename via authenticated request
4. **Deletion**: Currently no deletion endpoint (files persist indefinitely)

---

## Limitations

- No file deletion endpoint
- No file listing endpoint
- No user-scoped file access
- No virus scanning
- Files stored on local filesystem (not cloud storage)

---

## Future Enhancements

- File deletion endpoint
- List user's uploaded files
- Cloud storage integration (S3, etc.)
- Image resizing/thumbnails
- Virus scanning
- User-scoped file access
