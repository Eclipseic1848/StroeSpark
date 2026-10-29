"""Web 与未来小程序共用的业务 API。"""

import asyncio
import hmac
import io
import json
import sqlite3
import warnings
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from . import __version__
from .provider import ProviderError, ProviderService
from .schema import ArtifactInput, ModelReply, ProviderInput, TaskCreate, TurnInput
from .settings import ROOT, Settings
from .store import Store
from .upload_limit import UploadLimitMiddleware
from .workflow import ACTION_TEXT, build_messages, render_artifact, render_reply

MAX_FILE_SIZE = 5 * 1024 * 1024
TEXT_TYPES = {"txt": "text/plain", "md": "text/markdown", "csv": "text/csv"}
IMAGE_TYPES = {"jpg": ("JPEG", "image/jpeg"), "jpeg": ("JPEG", "image/jpeg"),
               "png": ("PNG", "image/png"), "webp": ("WEBP", "image/webp")}


def validate_material(name: str, content: bytes) -> str:
    extension = name.rsplit(".", 1)[-1].lower()
    if not content:
        raise HTTPException(400, "素材文件不能为空")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "单个素材不得超过 5 MB")
    if extension in TEXT_TYPES:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(400, "文本素材需要使用 UTF-8 编码") from None
        if "\x00" in text or len(text) > 40000:
            raise HTTPException(400, "文本素材需要为普通文本，且不超过 40000 字符")
        return TEXT_TYPES[extension]
    if extension in IMAGE_TYPES:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as image:
                    if image.format != IMAGE_TYPES[extension][0] or image.width * image.height > 20_000_000:
                        raise ValueError("图片格式或尺寸不合适")
                    image.verify()
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
                Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise HTTPException(400, "图片内容无效，或像素超过 2000 万；请使用 JPEG、PNG 或 WebP") from None
        return IMAGE_TYPES[extension][1]
    raise HTTPException(400, "当前支持 TXT、MD、CSV、JPEG、PNG 和 WebP 素材")


def create_app(settings: Settings | None = None, transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    store = Store(settings.data_dir)
    provider = ProviderService(settings, store, transport=transport)
    # shortcut: 单进程内串行处理同一任务，扩展多进程前需要数据库任务锁。
    locks: dict[str, asyncio.Lock] = {}

    @asynccontextmanager
    async def lifespan(app):
        yield

    app = FastAPI(title="StoreSpark API", version=__version__, lifespan=lifespan)
    app.state.store = store
    app.state.provider = provider
    # 后注册的认证中间件包在外层，未认证请求不会读取上传正文。
    app.add_middleware(UploadLimitMiddleware, max_body_size=MAX_FILE_SIZE + 64 * 1024)

    @app.middleware("http")
    async def protect_api(request: Request, call_next):
        if request.url.path.startswith("/api/v1"):
            if settings.access_token:
                supplied = request.headers.get("authorization", "")
                if not hmac.compare_digest(supplied.encode("utf-8"), ("Bearer " + settings.access_token).encode("utf-8")):
                    return JSONResponse({"detail": "访问令牌无效，请重新连接"}, status_code=401)
            elif (not request.client or request.client.host not in {"127.0.0.1", "::1", "testclient"}
                  or request.url.hostname not in {"127.0.0.1", "localhost", "::1", "testserver"}):
                return JSONResponse({"detail": "外部访问需要先配置服务端访问令牌"}, status_code=403)
            origin = request.headers.get("origin")
            if origin and request.method not in {"GET", "HEAD", "OPTIONS"}:
                parsed = urlsplit(origin)
                if parsed.netloc != request.url.netloc:
                    return JSONResponse({"detail": "不允许跨站修改数据"}, status_code=403)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # Pydantic 默认错误可能含原始密钥，接口只返回字段位置。
        fields = ", ".join(".".join(str(part) for part in error["loc"]) for error in exc.errors())
        return JSONResponse({"detail": "请检查输入字段：" + fields}, status_code=422)

    @app.exception_handler(ProviderError)
    async def provider_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=exc.status_code)

    @app.exception_handler(sqlite3.Error)
    async def storage_error(request, exc):
        return JSONResponse({"detail": "数据保存失败，请检查数据目录空间和权限后重试"}, status_code=503)

    def require_task(task_id: str) -> dict:
        task = store.get_task(task_id)
        if task is None:
            raise HTTPException(404, "任务不存在")
        return task

    def task_lock(task_id: str) -> asyncio.Lock:
        require_task(task_id)
        return locks.setdefault(task_id, asyncio.Lock())

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": __version__, "provider_configured": provider.public_config()["api_key_set"]}

    @app.get("/api/v1/provider")
    def provider_config():
        return provider.public_config()

    @app.put("/api/v1/provider")
    def save_provider(payload: ProviderInput):
        values = payload.model_dump(exclude={"api_key"})
        if payload.api_key is not None:
            values["api_key"] = payload.api_key.get_secret_value()
        return provider.save_config(values)

    @app.get("/api/v1/tasks")
    def list_tasks():
        return store.list_tasks()

    @app.post("/api/v1/tasks", status_code=201)
    def create_task(payload: TaskCreate):
        return store.create_task(payload.model_dump())

    @app.get("/api/v1/tasks/{task_id}")
    def task_detail(task_id: str):
        return require_task(task_id)

    @app.post("/api/v1/tasks/{task_id}/materials", status_code=201)
    async def upload(task_id: str, file: UploadFile = File(...)):
        require_task(task_id)
        name = (file.filename or "").replace("\\", "/").split("/")[-1]
        if not name or len(name) > 200 or any(ord(char) < 32 for char in name):
            raise HTTPException(400, "素材文件名无效")
        try:
            content = await file.read(MAX_FILE_SIZE + 1)
        finally:
            await file.close()
        media_type = validate_material(name, content)
        async with task_lock(task_id):
            try:
                return store.add_material(task_id, name, media_type, content)
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from None

    @app.post("/api/v1/tasks/{task_id}/messages")
    async def send_message(task_id: str, payload: TurnInput):
        content = payload.content or ACTION_TEXT.get(payload.action)
        if not content:
            raise HTTPException(422, "请填写希望修改的内容")
        lock = task_lock(task_id)
        if lock.locked():
            raise HTTPException(409, "当前任务正在处理，请等待完成后再操作")
        async with lock:
            task = require_task(task_id)
            if len(task["messages"]) >= 60:
                raise HTTPException(400, "本任务对话已达到 60 条，请新建任务并整理已有结果")
            if payload.action == "revise" and not task["artifacts"]:
                raise HTTPException(409, "请先生成一份内容，再进行修改")
            store.add_message(task_id, "user", content)
            task = require_task(task_id)
            materials = store.material_content(task_id)
            messages = build_messages(task, materials, payload.action)
            if len(json.dumps(messages, ensure_ascii=False)) > 32 * 1024 * 1024:
                raise HTTPException(413, "任务上下文过大，请减少素材或整理后新建任务；本次输入已保存")
            try:
                result = ModelReply.model_validate(await provider.complete(messages))
            except ValidationError:
                raise HTTPException(502, "模型返回内容结构不完整，本次输入已保存，可以重试") from None
            if payload.action == "direction" and not result.direction:
                raise HTTPException(502, "模型没有返回宣传方向，本次输入已保存，可以重试")
            if payload.action in {"generate", "revise"} and not (result.content and result.usage and result.validation):
                raise HTTPException(502, "模型未完整生成正文、使用与验证建议，本次输入已保存，可以重试")
            artifact = {"title": result.title, "content": render_artifact(result)} if result.content else None
            status = {"clarify": "clarifying", "direction": "direction", "generate": "content", "revise": "content"}[payload.action]
            store.complete_turn(task_id, render_reply(result), status, artifact)
            return require_task(task_id)

    @app.patch("/api/v1/tasks/{task_id}/artifacts/{artifact_id}")
    async def save_artifact(task_id: str, artifact_id: str, payload: ArtifactInput):
        async with task_lock(task_id):
            artifact = store.edit_artifact(task_id, artifact_id, payload.title, payload.content)
            if artifact is None:
                raise HTTPException(404, "内容不存在或不属于当前任务")
            return artifact

    @app.get("/api/v1/tasks/{task_id}/export")
    def export(task_id: str):
        task = require_task(task_id)
        sections = [f"# {task['title']}", "## 任务描述\n\n" + (task["brief"] or "未填写"),
                    "使用前请核实菜品、价格、位置、活动和素材权限。此文件包含任务记录与文本内容，不代表图片或视频成片。"]
        if task["messages"]:
            sections.append("## 对话与宣传方向\n\n" + "\n\n".join(
                ("商家：" if m["role"] == "user" else "StoreSpark：") + m["content"] for m in task["messages"]))
        for artifact in task["artifacts"]:
            sections.append("## " + artifact["title"] + "\n\n" + artifact["content"])
        return Response("\n\n".join(sections) + "\n", media_type="text/markdown; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="storespark-{task_id}.md"'})

    dist = ROOT / "web" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="web")
    else:
        @app.get("/")
        def root():
            return {"name": "StoreSpark", "api_docs": "/docs", "web": "请先构建 web，或启动 Vite 开发服务"}
    return app
