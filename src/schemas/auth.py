from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Annotated, Literal, Dict, Optional

class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        examples=["krushan"],
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
        examples=["Password@123"],
    )

    first_name: str = Field(
        min_length=1,
        max_length=100,
        examples=["Krushan"],
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
        examples=["Patel"],
    )

class RegisterResponse(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    is_verified: bool
    message: str
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    