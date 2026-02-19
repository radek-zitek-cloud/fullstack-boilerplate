"""User schemas for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )


class UserCreate(UserBase):
    """Schema for creating a new user.
    
    Used during user registration.
    """
    
    password: str = Field(
        ...,
        min_length=8,
        description="User's password (minimum 8 characters)",
        examples=["securepassword123"]
    )
    first_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User's first name",
        examples=["John"]
    )
    last_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User's last name",
        examples=["Doe"]
    )


class UserUpdate(BaseModel):
    """Schema for updating user information (admin only).
    
    Allows updating all user fields including email and password.
    """
    
    email: Optional[EmailStr] = Field(
        None,
        description="New email address"
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        description="New password (minimum 8 characters)"
    )
    first_name: Optional[str] = Field(
        None,
        max_length=255,
        description="First name"
    )
    last_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Last name"
    )
    note: Optional[str] = Field(
        None,
        max_length=5000,
        description="Personal note or bio"
    )


class ProfileUpdate(BaseModel):
    """Schema for updating user profile (self-service).
    
    Used by users to update their own profile.
    Does not allow changing email or password.
    """
    
    first_name: Optional[str] = Field(
        None,
        max_length=255,
        description="First name",
        examples=["John"]
    )
    last_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Last name",
        examples=["Doe"]
    )
    note: Optional[str] = Field(
        None,
        max_length=5000,
        description="Personal note or bio (HTML will be sanitized)",
        examples=["Software developer passionate about clean code."]
    )


class PasswordChange(BaseModel):
    """Schema for changing password.
    
    Requires current password for verification.
    """
    
    current_password: str = Field(
        ...,
        description="Current password for verification",
        examples=["oldpassword123"]
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (minimum 8 characters)",
        examples=["newsecurepassword123"]
    )


class UserInDB(UserBase):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    note: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    hashed_password: str

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """User response schema.
    
    Returned by API endpoints containing user information.
    """
    
    id: int = Field(
        ...,
        description="Unique user identifier"
    )
    first_name: Optional[str] = Field(
        None,
        description="User's first name"
    )
    last_name: Optional[str] = Field(
        None,
        description="User's last name"
    )
    note: Optional[str] = Field(
        None,
        description="Personal note or bio"
    )
    is_active: bool = Field(
        ...,
        description="Whether the user account is active"
    )
    is_admin: bool = Field(
        ...,
        description="Whether the user has admin privileges"
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp (UTC)"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp (UTC)"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "note": "Software developer",
                "is_active": True,
                "is_admin": False,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    }
