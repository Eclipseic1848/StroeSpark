import uvicorn

from .settings import Settings


def main() -> None:
    settings = Settings.from_env()
    uvicorn.run("storespark.app:create_app", factory=True, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
