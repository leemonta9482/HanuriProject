from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# 항상 이 파일과 같은 디렉터리의 .env 를 먼저 읽어 os.environ 에 넣습니다.
# (실행 시 작업 폴더와 무관하게 backend/.env 가 적용되도록)
_BACKEND_DIR = Path(__file__).resolve().parent
_ENV_FILE = _BACKEND_DIR / ".env"
if _ENV_FILE.is_file():
    load_dotenv(_ENV_FILE, encoding="utf-8")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # DB — 실제 값은 backend/.env 의 DB_* (민감 정보는 커밋하지 마세요)
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = ""
    db_password: str = ""
    db_name: str = "HanuriProject"

    # JWT — jwt_secret 은 반드시 .env 에 두고 운영에서는 강한 난수로 변경
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    # SMTP — backend/.env 의 SMTP_*
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = ""
    smtp_from_name: str = "하누리"
    app_public_url: str = "http://localhost:5173"

    @property
    def upload_dir(self) -> Path:
        return Path(__file__).resolve().parent / "uploads"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            "?charset=utf8mb4"
        )


settings = Settings()
