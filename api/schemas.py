"""Pydantic request / response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Auth ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str
    password: str = Field(min_length=6, max_length=128)

    model_config = {"json_schema_extra": {"examples": [{"username": "demo", "email": "demo@example.com", "password": "secret123"}]}}


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime


# ── Sessions ─────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    name: str = Field(default="default", max_length=128)


class SessionResponse(BaseModel):
    id: str
    name: str
    stack_depth: int
    created_at: datetime
    updated_at: datetime


class SettingsResponse(BaseModel):
    angle_mode: str
    num_format: str
    fix_digits: Optional[int]


class SessionDetailResponse(BaseModel):
    id: str
    name: str
    stack: List[StackItem]
    variables: Dict[str, StackItem]
    settings: SettingsResponse
    stack_depth: int
    created_at: datetime
    updated_at: datetime


class SettingsUpdate(BaseModel):
    angle_mode: Optional[str] = None
    num_format: Optional[str] = None
    fix_digits: Optional[int] = None


# ── Stack / Execution ────────────────────────────────────────────────

class StackItem(BaseModel):
    level: int = Field(description="Stack level (1 = top)")
    value: Any = Field(description="Value (number, string, list, vector, matrix, program tokens)")
    type: str = Field(description="RPN type: number, string, list, vector, matrix, program, symbol")
    display: str = Field(description="Formatted display string")


class ExecuteRequest(BaseModel):
    input: str = Field(min_length=1, description="RPN expression to evaluate")

    model_config = {"json_schema_extra": {"examples": [{"input": "3 4 + DUP *"}]}}


class PushRequest(BaseModel):
    value: Any = Field(description="Value to push")
    type: str = Field(default="number", description="Type: number, string, list, vector, matrix")

    model_config = {"json_schema_extra": {"examples": [{"value": 42, "type": "number"}]}}


class ExecutionResult(BaseModel):
    stack: List[StackItem]
    stack_depth: int
    error: Optional[str] = None


# ── Operations discovery ─────────────────────────────────────────────

class OperationInfo(BaseModel):
    name: str
    aliases: List[str]
    category: str
    description: Optional[str]


class OperationCategory(BaseModel):
    name: str
    count: int
    operations: List[str]
