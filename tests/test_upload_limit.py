"""验证上传限额先于 multipart 临时文件写入，并覆盖分块及伪造长度。"""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from PIL import Image

from storespark.app import MAX_FILE_SIZE, create_app
from storespark.settings import Settings


MAX_UPLOAD_BODY = MAX_FILE_SIZE + 64 * 1024


class ChunkedBody(httpx.AsyncByteStream):
    def __init__(self, body: bytes, chunk_size: int = 64 * 1024):
        self.body = body
        self.chunk_size = chunk_size
        self.reads = 0

    async def __aiter__(self):
        for offset in range(0, len(self.body), self.chunk_size):
            self.reads += 1
            yield self.body[offset:offset + self.chunk_size]


class TrackedFile:
    def __init__(self, *args, **kwargs):
        self.inner = tempfile.SpooledTemporaryFile(*args, **kwargs)
        self.written = 0

    def write(self, content):
        self.written += len(content)
        return self.inner.write(content)

    def __getattr__(self, name):
        return getattr(self.inner, name)


class UploadLimitTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app(Settings(data_dir=Path(self.temp.name)))
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://testserver")
        task = await self.client.post("/api/v1/tasks", json={"title": "上传边界"})
        self.url = f"/api/v1/tasks/{task.json()['id']}/materials"
        self.files = []

    async def asyncTearDown(self):
        await self.client.aclose()
        self.temp.cleanup()

    def tracked_file(self, *args, **kwargs):
        file = TrackedFile(*args, **kwargs)
        self.files.append(file)
        return file

    @staticmethod
    def multipart(content: bytes, filename: str = "notes.txt") -> bytes:
        header = (
            '--upload-boundary\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'
        ).encode("utf-8")
        return header + content + b"\r\n--upload-boundary--\r\n"

    async def upload(self, body: bytes, declared_length: str | None = None, client=None):
        stream = ChunkedBody(body)
        headers = {"Content-Type": "multipart/form-data; boundary=upload-boundary"}
        if declared_length is not None:
            headers["Content-Length"] = declared_length
        with patch("starlette.formparsers.SpooledTemporaryFile", self.tracked_file):
            response = await (client or self.client).post(self.url, content=stream, headers=headers)
        return response, stream

    def assert_files_released_within_limit(self):
        self.assertLessEqual(sum(file.written for file in self.files), MAX_UPLOAD_BODY)
        self.assertTrue(all(file.inner.closed for file in self.files))

    async def test_small_utf8_material_remains_usable(self):
        response, _ = await self.upload(self.multipart("门店素材".encode("utf-8")))
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["size"], len("门店素材".encode("utf-8")))
        self.assert_files_released_within_limit()

    async def test_exact_file_limit_allows_multipart_overhead(self):
        image = io.BytesIO()
        Image.new("RGB", (1, 1), "white").save(image, format="PNG")
        content = image.getvalue().ljust(MAX_FILE_SIZE, b"\x00")
        response, _ = await self.upload(self.multipart(content, "photo.png"))
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(sum(file.written for file in self.files), MAX_FILE_SIZE)
        self.assert_files_released_within_limit()

    async def test_oversized_content_length_rejects_before_reading_body(self):
        body = self.multipart(b"x" * (16 * 1024 * 1024))
        response, stream = await self.upload(body, str(len(body)))
        self.assertEqual(response.status_code, 413, response.text)
        self.assertEqual(stream.reads, 0)
        self.assertEqual(self.files, [])

    async def test_chunked_body_without_content_length_stops_before_disk_growth(self):
        response, stream = await self.upload(self.multipart(b"x" * (16 * 1024 * 1024)))
        self.assertEqual(response.status_code, 413, response.text)
        self.assertGreater(stream.reads, 1)
        self.assertLessEqual(stream.reads, MAX_UPLOAD_BODY // stream.chunk_size + 1)
        self.assertTrue(self.files)
        self.assert_files_released_within_limit()
        task_id = self.url.split("/")[-2]
        self.assertEqual(self.app.state.store.get_task(task_id)["materials"], [])

    async def test_forged_small_content_length_cannot_bypass_stream_limit(self):
        response, _ = await self.upload(self.multipart(b"x" * (16 * 1024 * 1024)), "1")
        self.assertEqual(response.status_code, 413, response.text)
        self.assertTrue(self.files)
        self.assert_files_released_within_limit()

    async def test_unauthenticated_large_upload_does_not_read_body(self):
        app = create_app(Settings(data_dir=Path(self.temp.name) / "auth", access_token="a" * 32))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            body = self.multipart(b"x" * (16 * 1024 * 1024))
            response, stream = await self.upload(body, str(len(body)), client=client)
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(stream.reads, 0)
        self.assertEqual(self.files, [])

    async def test_single_oversized_chunk_does_not_reach_multipart_parser(self):
        body = self.multipart(b"x" * (16 * 1024 * 1024))
        stream = ChunkedBody(body, chunk_size=len(body))
        with patch("starlette.formparsers.SpooledTemporaryFile", self.tracked_file):
            response = await self.client.post(self.url, content=stream, headers={
                "Content-Type": "multipart/form-data; boundary=upload-boundary"})
        self.assertEqual(response.status_code, 413, response.text)
        self.assertEqual(self.files, [])

    async def test_invalid_content_length_is_rejected_without_reading(self):
        response, stream = await self.upload(self.multipart(b"text"), "not-a-length")
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(stream.reads, 0)
        self.assertEqual(self.files, [])

    async def test_limit_does_not_swallow_unexpected_receive_errors(self):
        from storespark.upload_limit import UploadLimitMiddleware

        async def consume(scope, receive, send):
            await receive()

        async def broken_receive():
            raise RuntimeError("unexpected transport failure")

        async def no_response(message):
            self.fail("未知异常不应转换为限额响应")

        app = UploadLimitMiddleware(consume, max_body_size=MAX_UPLOAD_BODY)
        scope = {"type": "http", "method": "POST", "path": self.url, "headers": []}
        with self.assertRaisesRegex(RuntimeError, "unexpected transport failure"):
            await app(scope, broken_receive, no_response)


if __name__ == "__main__":
    unittest.main()
