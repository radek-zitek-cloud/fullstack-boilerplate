from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    note: Optional[str] = Field(None, max_length=5000)


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    note: Optional[str] = Field(None, max_length=5000)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


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
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    note: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
