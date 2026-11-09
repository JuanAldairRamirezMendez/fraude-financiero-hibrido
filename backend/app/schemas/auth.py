from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["admin", "analyst", "viewer"]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)


class AuthUser(BaseModel):
    id: str
    username: str
    role: Role


class AuthResponse(BaseModel):
    user: AuthUser
    expires_in: int


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: AuthUser | None = None
