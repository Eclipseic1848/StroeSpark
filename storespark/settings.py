"""读取服务端配置，客户端不接触模型密钥。"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=lambda: ROOT / "data")
    provider_name: str = "deepseek"
    provider_base_url: str = "https://api.deepseek.com"
    provider_model: str = "deepseek-flash"
    provider_api_key: str = field(default="", repr=False)
    provider_timeout: float = 60.0
    access_token: str = field(default="", repr=False)
    host: str = "127.0.0.1"
    port: int = 8000

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(ROOT / ".env", encoding="utf-8", override=False)
        timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        port = int(os.getenv("STORESPARK_PORT", "8000"))
        host = os.getenv("STORESPARK_HOST", "127.0.0.1")
        token = os.getenv("STORESPARK_ACCESS_TOKEN", "")
        if not 1 <= timeout <= 300 or not 1 <= port <= 65535:
            raise ValueError("模型超时或服务端口超出允许范围")
        if token and len(token) < 24:
            raise ValueError("访问令牌至少需要 24 个字符")
        if host not in {"127.0.0.1", "localhost", "::1"} and not token:
            raise ValueError("监听外部网络前必须配置 STORESPARK_ACCESS_TOKEN")
        return cls(
            data_dir=Path(os.getenv("STORESPARK_DATA_DIR") or ROOT / "data").resolve(),
            provider_name=os.getenv("LLM_DEFAULT_PROVIDER", "deepseek"),
            provider_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            provider_model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
            provider_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            provider_timeout=timeout,
            access_token=token,
            host=host,
            port=port,
        )
