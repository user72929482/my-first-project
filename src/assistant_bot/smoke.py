import asyncio, tempfile
from pathlib import Path
from assistant_bot.config import Settings
from assistant_bot.db import session as dbs
from assistant_bot.services.auth import AuthService
from assistant_bot.services.files import safe_filename, validate_upload
from assistant_bot.services.projects import ProjectService
from assistant_bot.tools.workspace import init_git, run_in_workspace

async def run() -> None:
    tmp = Path(tempfile.mkdtemp())
    s = Settings(database_url=f"sqlite+aiosqlite:///{tmp/'smoke.db'}", workspace_root=tmp/"ws", telegram_allowed_user_id=123, telegram_bot_token="0:test", openai_api_key="sk-test")
    dbs.init_engine(s.database_url); await dbs.create_schema()
    async with dbs.SessionLocal() as session:
        assert await AuthService(s).is_authorized(session, 123)
        assert not await AuthService(s).is_authorized(session, 999)
        p = await ProjectService(s.workspace_root).create(session, "Smoke Project", "test")
        assert p.id and Path(p.workspace_path).exists()
    validate_upload("report.pdf", 10, 1); assert safe_filename("../Bad File.pdf") == "bad-file.pdf"
    await init_git(tmp/"ws"/"code")
    out = await run_in_workspace(tmp/"ws"/"code", ["python", "-c", "print('ok')"])
    assert "ok" in out
    print("smoke ok")

def main() -> None: asyncio.run(run())
if __name__ == "__main__": main()
