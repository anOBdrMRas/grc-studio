from pydantic import BaseModel, Field


class CustomFieldIO(BaseModel):
    key: str = Field("", description='"x_…"; empty for a new field (the API assigns it)')
    label: str
    type: str = Field(description="text, textarea, number, date, bool, select, multiselect, user")
    section: str = Field("", description="section of the form the field is shown in")
    options: list[str] = []
    removed: bool = Field(False, description="hidden; stored values are kept")


class ContentOut(BaseModel):
    version: int = Field(description="0 while nothing has been configured")
    fields: dict[str, list[CustomFieldIO]] = Field(description="custom fields per module (kind)")
    options: dict[str, list[str]] = Field(
        description='additional values of standard dropdowns, key "kind.field"'
    )
    kinds: list[str]
    types: list[str]


class ContentIn(BaseModel):
    version: int | None = None
    fields: dict[str, list[CustomFieldIO]] = {}
    options: dict[str, list[str]] = {}
