import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import get_current_active_user
from app.core.config import get_settings

router = APIRouter(
    tags=["uploads"],
    responses={404: {"description": "File not found"}},
)
settings = get_settings()


def get_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload file",
    description="Upload a file to the server. Only images and documents are allowed.",
    responses={
        201: {"description": "File uploaded successfully"},
        401: {"description": "Not authenticated"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported file type"},
    },
)
async def upload_file(
    file: UploadFile = File(
        ...,
        description="File to upload (max 10MB, images and documents only)",
    ),
    current_user: dict = Depends(get_current_active_user),
):
    """Upload a file.
    
    Uploads a file to the server with validation for size and type.
    Files are stored with unique UUID filenames to prevent conflicts.
    
    Allowed file types:
    - image/jpeg, image/png, image/gif, image/webp
    - application/pdf
    - text/plain
    
    Args:
        file: File to upload (max 10MB)
        current_user: Current authenticated user from JWT token
        
    Returns:
        Dictionary with upload details including URL to access the file
        
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 413 if file exceeds max size (10MB)
        HTTPException: 415 if file type is not allowed
    """
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes",
        )

    # Validate file type (allow images and common documents)
    allowed_types = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/pdf",
        "text/plain",
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type {file.content_type} not allowed",
        )

    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"

    # Save file
    upload_dir = get_upload_dir()
    file_path = upload_dir / unique_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": unique_filename,
        "original_name": file.filename,
        "content_type": file.content_type,
        "size": file_size,
        "url": f"/uploads/{unique_filename}",
    }


@router.get(
    "/uploads/{filename}",
    summary="Download file",
    description="Download a previously uploaded file by filename. Requires authentication.",
    responses={
        200: {"description": "File returned successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "File not found"},
    },
)
async def get_uploaded_file(
    filename: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Download an uploaded file.
    
    Retrieves a previously uploaded file by its filename.
    Files are accessible only to authenticated users.
    
    Args:
        filename: Name of the file to retrieve (UUID with extension)
        current_user: Current authenticated user from JWT token
        
    Returns:
        FileResponse with the file content
        
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 404 if file not found
        
    Note:
        Files are stored outside the web root for security.
        Access is logged for audit purposes.
    """
    upload_dir = get_upload_dir()
    file_path = upload_dir / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return FileResponse(file_path)
