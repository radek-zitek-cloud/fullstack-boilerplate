"""Authentication schemas for API requests and responses."""

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response schema.
    
    Returned by login and refresh endpoints.
    """
    
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication (valid for 30 days)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens (valid for 7 days)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
        examples=["bearer"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    }


class TokenPayload(BaseModel):
    sub: int | None = None
    email: str | None = None
    type: str | None = None


class LoginRequest(BaseModel):
    """Login request schema.
    
    Used to authenticate a user and obtain JWT tokens.
    """
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="User's password",
        examples=["password123"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }
    }


class RefreshRequest(BaseModel):
    """Token refresh request schema.
    
    Used to exchange a refresh token for new access and refresh tokens.
    """
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema.
    
    Used to request a password reset email.
    Always returns 204 to prevent email enumeration.
    """
    
    email: EmailStr = Field(
        ...,
        description="Email address associated with the account",
        examples=["user@example.com"]
    )


class ResetPasswordRequest(BaseModel):
    """Reset password request schema.
    
    Used to reset password using a token from email.
    """
    
    token: str = Field(
        ...,
        description="Password reset token received via email",
        examples=["abc123..."]
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (minimum 8 characters)",
        examples=["newsecurepassword123"]
    )
