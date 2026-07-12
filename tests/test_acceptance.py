from pathlib import Path
import asyncio, pytest
from assistant_bot.config import Settings
from assistant_bot.db import session as dbs
from assistant_bot.services.auth import AuthService
from assistant_bot.services.files import safe_filename, validate_upload
from assistant_bot.services.projects import ProjectService
from assistant_bot.agents.factory import AssistantAgent
from assistant_bot.tools.workspace import run_in_workspace, init_git

def test_owner_auth_project_memory_and_restart(tmp_path):
    async def inner():
        db = tmp_path / "app.db"
        settings = Settings(database_url=f"sqlite+aiosqlite:///{db}", workspace_root=tmp_path/"ws", telegram_allowed_user_id=42, telegram_bot_token="0:test", openai_api_key="sk-test")
        dbs.init_engine(settings.database_url); await dbs.create_schema()
        async with dbs.SessionLocal() as session:
            assert await AuthService(settings).is_authorized(session, 42)
            assert not await AuthService(settings).is_authorized(session, 7)
            projects = ProjectService(settings.workspace_root)
            project = await projects.create(session, "Test Project", "objective")
            await projects.remember(session, "preference", "concise updates", project.id)
        dbs.init_engine(settings.database_url); await dbs.create_schema()
        async with dbs.SessionLocal() as session:
            assert (await ProjectService(settings.workspace_root).memories(session))[0].value == "concise updates"
    asyncio.run(inner())

def test_pairing_secret_records_owner(tmp_path):
    async def inner():
        settings = Settings(database_url=f"sqlite+aiosqlite:///{tmp_path/'pair.db'}", workspace_root=tmp_path, telegram_pairing_secret="secret", telegram_bot_token="0:test", openai_api_key="sk-test")
        dbs.init_engine(settings.database_url); await dbs.create_schema()
        async with dbs.SessionLocal() as session:
            auth = AuthService(settings)
            assert await auth.pair(session, 12345, "secret")
            assert await auth.is_authorized(session, 12345)
            assert not await auth.pair(session, 9, "secret")
    asyncio.run(inner())

def test_file_validation_and_workspace_execution(tmp_path):
    async def inner():
        validate_upload("input.pdf", 100, 1)
        with pytest.raises(ValueError): validate_upload("evil.exe", 1, 1)
        assert safe_filename("../My File.PDF") == "my-file.pdf"
        await init_git(tmp_path)
        out = await run_in_workspace(tmp_path, ["python", "-c", "print('tests ran')"])
        assert "tests ran" in out
    asyncio.run(inner())

def test_agent_safe_without_real_credentials(tmp_path):
    async def inner():
        from assistant_bot.agents.factory import MissingOpenAIKeyError
        settings = Settings(database_url=f"sqlite+aiosqlite:///{tmp_path/'a.db'}", telegram_bot_token="0:test", openai_api_key="", workspace_root=tmp_path)
        with pytest.raises(MissingOpenAIKeyError, match="OPENAI_API_KEY"):
            await AssistantAgent(settings).run("hello")
    asyncio.run(inner())

def test_dotenv_loader_sets_token(tmp_path, monkeypatch):
    from assistant_bot.config import load_dotenv
    env_file = tmp_path / ".env"
    env_file.write_text('TELEGRAM_BOT_TOKEN="999:test-token"\n')
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    load_dotenv(str(env_file))
    assert __import__("os").environ["TELEGRAM_BOT_TOKEN"] == "999:test-token"

def test_configure_token_upsert_preserves_other_values(tmp_path):
    from assistant_bot.configure_token import _upsert
    lines = ["OPENAI_API_KEY=sk-placeholder", "TELEGRAM_BOT_TOKEN=old"]
    updated = _upsert(lines, "TELEGRAM_BOT_TOKEN", "123456:abcdefghijklmnopqrstuvwxyz")
    assert updated == ["OPENAI_API_KEY=sk-placeholder", "TELEGRAM_BOT_TOKEN=123456:abcdefghijklmnopqrstuvwxyz"]

def test_selected_project_and_conversation_persist(tmp_path):
    async def inner():
        db = tmp_path / "state.db"
        settings = Settings(database_url=f"sqlite+aiosqlite:///{db}", workspace_root=tmp_path/"ws", telegram_allowed_user_id=42, telegram_bot_token="0:test", openai_api_key="sk-test")
        dbs.init_engine(settings.database_url); await dbs.create_schema()
        async with dbs.SessionLocal() as session:
            project = await ProjectService(settings.workspace_root).create(session, "Persisted Project")
            session.set_selected_project(42, project.id)
            session.add_message(42, "user", "remember this", project.id)
            await session.commit()
        dbs.init_engine(settings.database_url); await dbs.create_schema()
        async with dbs.SessionLocal() as session:
            assert session.selected_project(42) == project.id
            assert session.recent_messages(42, project.id)[0] == ("user", "remember this")
    asyncio.run(inner())


def test_agent_reports_missing_openai_key(tmp_path):
    async def inner():
        from assistant_bot.agents.factory import MissingOpenAIKeyError
        settings = Settings(database_url=f"sqlite+aiosqlite:///{tmp_path/'missing.db'}", telegram_bot_token="0:test", openai_api_key="", workspace_root=tmp_path)
        with pytest.raises(MissingOpenAIKeyError, match="OPENAI_API_KEY"):
            await AssistantAgent(settings).run("hello")
    asyncio.run(inner())
