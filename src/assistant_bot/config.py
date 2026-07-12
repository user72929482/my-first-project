import os
from pathlib import Path
from dataclasses import dataclass

def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value

load_dotenv()

class Secret:
    def __init__(self, value: str = ""): self.value=value
    def get_secret_value(self) -> str: return self.value
    def __bool__(self): return bool(self.value)

@dataclass
class Settings:
    telegram_bot_token: Secret | str = Secret(os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_allowed_user_id: int | None = int(os.getenv("TELEGRAM_ALLOWED_USER_ID")) if os.getenv("TELEGRAM_ALLOWED_USER_ID") else None
    telegram_pairing_secret: Secret | str | None = Secret(os.getenv("TELEGRAM_PAIRING_SECRET", "")) if os.getenv("TELEGRAM_PAIRING_SECRET") else None
    openai_api_key: Secret | str = Secret(os.getenv("OPENAI_API_KEY", ""))
    openai_default_model: str = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-5.5")
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/assistant.db")
    redis_url: str | None = os.getenv("REDIS_URL") or None
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_TASKS", "2"))
    encryption_key: Secret | str | None = Secret(os.getenv("ENCRYPTION_KEY", "")) if os.getenv("ENCRYPTION_KEY") else None
    workspace_root: Path | str = Path(os.getenv("WORKSPACE_ROOT", "./workspaces"))
    task_timeout_seconds: int = 900
    def __post_init__(self):
        if isinstance(self.telegram_bot_token, str): self.telegram_bot_token=Secret(self.telegram_bot_token)
        if isinstance(self.openai_api_key, str): self.openai_api_key=Secret(self.openai_api_key)
        if isinstance(self.telegram_pairing_secret, str): self.telegram_pairing_secret=Secret(self.telegram_pairing_secret)
        self.workspace_root=Path(self.workspace_root)
        if not (1 <= self.max_upload_mb <= 100): raise ValueError("MAX_UPLOAD_MB must be between 1 and 100")
settings = Settings()
