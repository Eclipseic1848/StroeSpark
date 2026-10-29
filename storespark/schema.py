"""请求与模型输出都在服务端校验。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TaskCreate(InputModel):
    title: str = Field(min_length=1, max_length=100)
    brief: str = Field(default="", max_length=12000)
    channel: str = Field(default="", max_length=100)
    format: str = Field(default="", max_length=100)


class TurnInput(InputModel):
    content: str = Field(default="", max_length=16000)
    action: Literal["clarify", "direction", "generate", "revise"] = "clarify"


class ProviderInput(InputModel):
    provider: Literal["deepseek", "openai-compatible"]
    base_url: str = Field(min_length=1, max_length=300)
    model: str = Field(min_length=1, max_length=100)
    api_key: SecretStr | None = None


class ArtifactInput(InputModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=40000)


class ModelReply(InputModel):
    reply: str = Field(min_length=1, max_length=20000)
    direction: str = Field(default="", max_length=12000)
    title: str = Field(default="宣传文案", min_length=1, max_length=200)
    content: str = Field(default="", max_length=24000)
    missing_facts: list[str] = Field(max_length=30)
    usage: str = Field(default="", max_length=4000)
    validation: str = Field(default="", max_length=4000)
