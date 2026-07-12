import asyncio
import signal

from assistant_bot.config import settings
from assistant_bot.db import session as dbs
from assistant_bot.logging import configure_logging


def main() -> None:
    """Start Telegram long polling after initializing local persistence."""
    configure_logging(settings.log_level)
    token = settings.telegram_bot_token.get_secret_value()
    if not token or token.startswith("123456:") or token == "0:test":
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not configured. Set it in the environment or in a local .env file."
        )

    from assistant_bot.agents.factory import AssistantAgent
    from assistant_bot.services.tasks import TaskService
    from assistant_bot.telegram.app import build_application

    dbs.init_engine(settings.database_url)
    asyncio.run(dbs.create_schema())
    tasks = TaskService(dbs.SessionLocal, AssistantAgent(settings), settings.max_concurrent_tasks)
    app = build_application(settings, tasks)
    app.run_polling(
        allowed_updates=None,
        close_loop=False,
        stop_signals=(signal.SIGINT, signal.SIGTERM),
    )


if __name__ == "__main__":
    main()
