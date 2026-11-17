from pydantic import BaseModel


class Me(BaseModel):
    id: str
    name: str
    system_roles: list[str]
    permissions: list[str]
    csrf_token: str
    position_title: str


class DemoPerson(BaseModel):
    id: str
    name: str
    position_title: str
    system_roles: list[str]


class DemoInfo(BaseModel):
    enabled: bool
    persons: list[DemoPerson]


class DemoLogin(BaseModel):
    user_id: str


class PasswordLogin(BaseModel):
    username: str
    password: str


class IsoClause(BaseModel):
    id: str
    standard: str
    clause: str
    title: str


class Catalogs(BaseModel):
    lists: dict[str, list[str]]
    iso: list[IsoClause]
