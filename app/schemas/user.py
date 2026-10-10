"""Schémas Pydantic v2 pour les utilisateurs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Role


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    full_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    full_name: str = Field(min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=200)
    role: Role = Role.LECTURE

    @field_validator("role", mode="before")
    @classmethod
    def _upper_role(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=200)
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=200)

    @field_validator("role", mode="before")
    @classmethod
    def _upper_role(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v