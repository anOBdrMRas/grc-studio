from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserFields(BaseModel):
    last_name: str = ""
    first_name: str = ""
    division: str = ""
    department: str = ""
    position_id: str | None = None
    description: str = ""
    system_roles: list[str] = Field(default_factory=lambda: ["employee"])


class UserOut(UserFields):
    custom: dict[str, Any] = Field(
        default_factory=dict, description="values of the custom fields (content administration)"
    )
    id: str
    code: str
    name: str
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    labels: dict[str, str]
    can_manage: bool


class UserListItem(BaseModel):
    id: str
    code: str
    name: str
    position_title: str
    division: str


class PersonOut(BaseModel):
    id: str
    name: str
    position_id: str | None
    position_title: str
    system_roles: list[str]


class CreateUser(BaseModel):
    last_name: str = Field("", max_length=200)
    first_name: str = ""
