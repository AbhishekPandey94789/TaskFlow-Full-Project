"""
Pydantic request/response schemas for TaskFlow.
Includes Field constraints and custom validators as required by the spec.
"""

from __future__ import annotations

from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Display name of the user")
    email: str = Field(..., description="Unique e-mail address")

    @field_validator("name", "email", mode="before")
    @classmethod
    def strip_and_reject_blank(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("Field must not be blank or whitespace-only")
        return v

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("email must contain '@'")
        return v.lower()


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

    @field_validator("name", "email", mode="before")
    @classmethod
    def strip_and_reject_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Field must not be blank or whitespace-only")
        return v


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Project schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Project name")
    description: Optional[str] = None
    owner_id: int = Field(..., gt=0, description="ID of the owning user")

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_reject_blank(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("name must not be blank or whitespace-only")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank or whitespace-only")
        return v


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Task schemas
# ---------------------------------------------------------------------------

PRIORITY_VALUES = Literal["low", "medium", "high"]
STATUS_VALUES = Literal["todo", "in_progress", "done"]


class TaskCreate(BaseModel):
    title: str = Field(..., description="Short task title")
    description: Optional[str] = None
    priority: PRIORITY_VALUES = Field("medium", description="low | medium | high")
    due_date: Optional[str] = Field(None, description="Raw text date, e.g. 'next friday'")
    status: STATUS_VALUES = Field("todo", description="todo | in_progress | done")
    project_id: int = Field(..., gt=0, description="ID of the owning project")

    @field_validator("title", mode="before")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        """Reject a title that is empty or whitespace-only after stripping."""
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("title must not be blank or whitespace-only")
        return v

    @field_validator("due_date", mode="before")
    @classmethod
    def normalise_due_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v if v else None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[PRIORITY_VALUES] = None
    due_date: Optional[str] = None
    status: Optional[STATUS_VALUES] = None

    @field_validator("title", mode="before")
    @classmethod
    def title_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank or whitespace-only")
        return v


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: str
    due_date: Optional[str]
    status: str
    project_id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Statistics schema
# ---------------------------------------------------------------------------

class StatusCount(BaseModel):
    status: str
    count: int


class ProjectStatsResponse(BaseModel):
    project_id: int
    project_name: str
    total_tasks: int
    by_status: List[StatusCount]


# ---------------------------------------------------------------------------
# Quick-add schema
# ---------------------------------------------------------------------------

class QuickAddRequest(BaseModel):
    description: str = Field(..., description="Free-text task description")
    project_id: int = Field(..., gt=0, description="ID of the target project")

    @field_validator("description", mode="before")
    @classmethod
    def description_must_not_be_empty(cls, v: str) -> str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("description must not be blank")
        return v
