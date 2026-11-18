from typing import Literal

from pydantic import BaseModel, Field


class AiSettingsOut(BaseModel):
    version: int
    enabled: bool
    provider: str = Field(description="openai (OpenAI-compatible, e.g. con-AI) or anthropic")
    providers: list[str]
    base_url: str = Field(description="address of the service; empty: api.anthropic.com")
    model: str
    models: list[str] = Field(description="suggestions for Anthropic")
    has_key: bool = Field(description="an API key is stored (it is never returned)")
    key_readable: bool = Field(description="the stored key can be decrypted with SETTINGS_SECRET")
    key_hint: str = Field(description="last four characters of the stored key")
    secret_configured: bool = Field(description="SETTINGS_SECRET is set on the server")


class AiSettingsIn(BaseModel):
    version: int
    enabled: bool = False
    provider: str = "openai"
    base_url: str = ""
    model: str = ""
    api_key: str = Field("", description="new key; empty keeps the stored one")
    remove_key: bool = False


class AiTestOut(BaseModel):
    ok: bool
    code: str = Field(
        description="ok, no_key, incomplete, ai_auth, ai_busy, ai_rejected, ai_unavailable"
    )


class AssistantStatus(BaseModel):
    ai: bool = Field(description="the AI answers; otherwise the catalogue search does")


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(max_length=8000)


class AskIn(BaseModel):
    question: str = Field(max_length=2000)
    history: list[Turn] = Field(default_factory=list, max_length=20)
    lang: str = "de"


class Hit(BaseModel):
    kind: str
    id: str
    label: str
    sub: str


class AskOut(BaseModel):
    mode: Literal["ai", "search"]
    text: str = Field(description="answer with links [[kind:id|label]] (AI mode)")
    hits: list[Hit] = Field(description="search hits (search mode)")
    error: str = Field("", description="why the AI did not answer (search mode)")


class SuggestIn(BaseModel):
    lang: str = "de"


class SuggestedField(BaseModel):
    key: str
    text: str
    current: str = Field(description="value stored now (shown for comparison)")


class SuggestOut(BaseModel):
    version: int = Field(description="version of the element the suggestions were made for")
    fields: list[SuggestedField]


class DraftStepIO(BaseModel):
    name: str = Field(max_length=200)
    type: Literal["task", "system", "manual", "decision"] = "task"
    role_id: str = ""
    raci: Literal["R", "A"] = "R"
    no: str = Field("", max_length=200, description="decision only: end event on no")


class DraftIn(BaseModel):
    text: str = Field(max_length=5000)
    use_ai: bool = True
    lang: str = "de"


class DraftOut(BaseModel):
    mode: Literal["ai", "text"]
    title: str
    category: str
    area: str
    start: str
    end: str
    steps: list[DraftStepIO]


class DraftCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = "Core process"
    area: str = Field("", max_length=200)
    description: str = Field("", max_length=5000)
    start: str = Field("Start", max_length=200)
    end: str = Field("Ende", max_length=200)
    steps: list[DraftStepIO] = Field(min_length=1, max_length=30)
