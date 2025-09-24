import os

class Settings:
    @property
    def database_url(self) -> str:
        return os.getenv("DATABASE_URL", "")
    @property
    def storage_root(self) -> str:
        return os.getenv("APP_STORAGE", "/app/storage")

settings = Settings()
