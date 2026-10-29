from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

import httpx
from cryptography.fernet import Fernet, InvalidToken

if TYPE_CHECKING:
    from .settings import Settings


MAX_RESPONSE_BYTES = 2 * 1024 * 1024
# shortcut: 配置保存锁只覆盖单进程，增加服务进程前需改用跨进程配置事务。
_configuration_lock = threading.RLock()


class ProviderError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def _validate_fields(provider: object, base_url: object, model: object) -> dict:
    if provider not in ("deepseek", "openai-compatible"):
        raise ProviderError("请选择受支持的模型供应商。", 422)
    if not isinstance(base_url, str) or not 1 <= len(base_url) <= 2048:
        raise ProviderError("请填写有效的 HTTPS 模型接口地址。", 422)
    if any(char.isspace() or ord(char) < 32 for char in base_url) or "\\" in base_url:
        raise ProviderError("模型接口地址不能包含空白或反斜线。", 422)
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except ValueError:
        raise ProviderError("请填写有效的 HTTPS 模型接口地址。", 422) from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or "?" in base_url
        or "#" in base_url
        or port == 0
    ):
        raise ProviderError("模型接口必须使用 HTTPS，且不能包含账号、查询参数或片段。", 422)
    try:
        httpx.URL(base_url)
    except (httpx.InvalidURL, UnicodeError):
        raise ProviderError("请填写有效的 HTTPS 模型接口地址。", 422) from None
    if not isinstance(model, str) or not model.strip() or len(model) > 200:
        raise ProviderError("请填写长度不超过 200 字符的模型 ID。", 422)
    if any(ord(char) < 32 for char in model):
        raise ProviderError("模型 ID 不能包含控制字符。", 422)
    hostname = parsed.hostname.lower()
    netloc = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None and port != 443:
        netloc += f":{port}"
    return {
        "provider": provider,
        "base_url": urlunsplit(("https", netloc, parsed.path.rstrip("/"), "", "")),
        "model": model.strip(),
    }


def _validate_key(value: object) -> str:
    if not isinstance(value, str):
        raise ProviderError("模型 API 密钥必须为文本。", 422)
    value = value.strip()
    if len(value) > 4096 or any(not 33 <= ord(char) <= 126 for char in value):
        raise ProviderError("模型 API 密钥格式不正确，请重新填写。", 422)
    if "*" in value:
        raise ProviderError("请填写实际密钥，不能保存密钥掩码。", 422)
    return value


def _json_object(value: str | bytes) -> dict:
    def reject_constant(_: str) -> None:
        raise ValueError("不支持的 JSON 数值")

    parsed = json.loads(value, parse_constant=reject_constant)
    if not isinstance(parsed, dict):
        raise ValueError("JSON 顶层必须为对象")
    return parsed


class ProviderService:
    def __init__(
        self,
        settings: Settings,
        store: object,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.store = store
        self.transport = transport

    def _current(self) -> dict:
        saved = self.store.get_setting("provider")
        if saved is not None:
            return {**saved, "source": "saved"}
        return {
            "provider": self.settings.provider_name,
            "base_url": self.settings.provider_base_url,
            "model": self.settings.provider_model,
            "api_key": self.settings.provider_api_key,
            "source": "environment" if self.settings.provider_api_key else "default",
        }

    def public_config(self) -> dict:
        config = self._current()
        return {
            "provider": config["provider"],
            "base_url": config["base_url"],
            "model": config["model"],
            "api_key_set": bool(config.get("api_key") or config.get("api_key_encrypted")),
            "source": config["source"],
        }

    def _fernet(self, create: bool = False) -> Fernet:
        key_path = Path(self.settings.data_dir) / "provider.key"
        try:
            with _configuration_lock:
                if not key_path.exists():
                    saved = self.store.get_setting("provider")
                    if not create or (saved and saved.get("api_key_encrypted")):
                        raise ProviderError("模型密钥加密文件缺失，请恢复原数据目录中的 provider.key。", 503)
                    key_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    except FileExistsError:
                        pass
                    else:
                        with os.fdopen(descriptor, "wb") as handle:
                            handle.write(Fernet.generate_key())
                            handle.flush()
                            os.fsync(handle.fileno())
                return Fernet(key_path.read_bytes())
        except (OSError, ValueError):
            raise ProviderError("模型密钥存储不可用，请检查数据目录权限和 provider.key 文件。", 503) from None

    def _plain_key(self, config: dict) -> str:
        if config.get("api_key_encrypted"):
            try:
                value = self._fernet().decrypt(config["api_key_encrypted"].encode("ascii")).decode("utf-8")
            except (InvalidToken, UnicodeError, ValueError):
                raise ProviderError("模型密钥无法解密，请恢复与数据库匹配的 provider.key。", 503) from None
        else:
            value = config.get("api_key", "")
        value = _validate_key(value)
        if not value:
            raise ProviderError("尚未配置模型 API 密钥，请先在模型设置中填写。", 503)
        return value

    def save_config(self, payload: dict) -> dict:
        with _configuration_lock:
            current = self._current()
            fields = _validate_fields(
                payload.get("provider", current["provider"]),
                payload.get("base_url", current["base_url"]),
                payload.get("model", current["model"]),
            )
            key = _validate_key(payload.get("api_key", ""))
            has_key = bool(current.get("api_key") or current.get("api_key_encrypted"))
            changed = any(
                fields[name] != (current[name].rstrip("/") if name == "base_url" else current[name])
                for name in fields
            )
            if changed and has_key and not key:
                raise ProviderError("切换供应商、接口地址或模型时，请重新填写密钥，避免发送旧凭据。", 422)
            encrypted = current.get("api_key_encrypted", "")
            if key or (not encrypted and current.get("api_key")):
                key = key or _validate_key(current["api_key"])
                encrypted = self._fernet(create=True).encrypt(key.encode("utf-8")).decode("ascii")
            self.store.set_setting("provider", {**fields, "api_key_encrypted": encrypted})
            return self.public_config()

    async def complete(self, messages: list[dict]) -> dict:
        config = self._current()
        fields = _validate_fields(config["provider"], config["base_url"], config["model"])
        key = self._plain_key(config)
        payload = {
            "model": fields["model"],
            "messages": messages,
            "response_format": {"type": "json_object"},
            "max_tokens": 4096,
            "stream": False,
        }
        if (
            fields["provider"] == "deepseek"
            and urlsplit(fields["base_url"]).hostname == "api.deepseek.com"
            and fields["model"] == "deepseek-flash"
        ):
            payload["thinking"] = {"type": "disabled"}
        try:
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=self.settings.provider_timeout,
                follow_redirects=False,
            ) as client:
                async with client.stream(
                    "POST",
                    fields["base_url"] + "/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json=payload,
                ) as response:
                    if not 200 <= response.status_code < 300:
                        raise ProviderError(f"模型服务返回 HTTP {response.status_code}，请检查模型配置后重试。")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise ProviderError("模型响应超过大小限制，请缩小本次任务后重试。")
        except httpx.TimeoutException:
            raise ProviderError("模型服务响应超时，请稍后重试；已有内容已保留。", 504) from None
        except httpx.RequestError:
            raise ProviderError("无法连接模型服务，请检查接口地址和网络后重试。") from None
        try:
            envelope = _json_object(bytes(body))
            choice = envelope["choices"][0]
            if choice["finish_reason"] != "stop":
                raise ValueError("模型输出未完整结束")
            content = choice["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("模型输出为空")
            return _json_object(content)
        except (ValueError, KeyError, IndexError, TypeError, RecursionError):
            raise ProviderError("模型未返回完整有效的 JSON 内容，请重试；已有内容已保留。") from None
