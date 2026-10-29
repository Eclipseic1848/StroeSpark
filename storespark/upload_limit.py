"""在 multipart 解析前限制上传正文，避免超大文件先写满临时磁盘。"""

import re

from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class UploadLimitMiddleware:
    def __init__(self, app: ASGIApp, max_body_size: int):
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] != "POST"
            or not re.fullmatch(r"/api/v1/tasks/[^/]+/materials/?", scope["path"])
        ):
            await self.app(scope, receive, send)
            return

        declared = Headers(scope=scope).get("content-length")
        if declared is not None:
            try:
                if not declared.isascii() or not declared.isdecimal():
                    raise ValueError
                size = int(declared)
            except ValueError:
                response = JSONResponse({"detail": "上传正文长度无效"}, status_code=400)
                await response(scope, receive, send)
                return
            if size > self.max_body_size:
                response = JSONResponse({"detail": "上传正文过大，单个素材不得超过 5 MB"}, status_code=413)
                await response(scope, receive, send)
                return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_size:
                    # Starlette 解析器会在读取失败时关闭已创建的全部上传临时文件。
                    raise HTTPException(413, "上传正文过大，单个素材不得超过 5 MB")
            return message

        await self.app(scope, limited_receive, send)
