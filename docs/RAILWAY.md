# Railway deployment

Deploy the GitHub repository named **private-telegram-ai-assistant** to Railway. Do not deploy a repository named `my-first-project`; that name is only the local workspace path in this environment.

Railway should use the repository root and the existing `Dockerfile`. The `railway.json` file pins Railway to Dockerfile builds so the same container entrypoint (`assistant-bot`) runs in Railway.

## Required Railway variables

Set these in the Railway service Variables tab before starting the service:

```text
TELEGRAM_BOT_TOKEN=<BotFather token>
OPENAI_API_KEY=<OpenAI API key>
TELEGRAM_PAIRING_SECRET=<one-time owner pairing phrase>
DATABASE_URL=sqlite+aiosqlite:///./data/assistant.db
WORKSPACE_ROOT=./workspaces
APP_ENV=production
```

Optional variables:

```text
TELEGRAM_ALLOWED_USER_ID=<your numeric Telegram user ID after you know it>
OPENAI_DEFAULT_MODEL=gpt-5.5
MAX_UPLOAD_MB=25
MAX_CONCURRENT_TASKS=2
```

## Expected first-run check

After Railway reports the service is running:

1. Send `/start` to the Telegram bot.
2. Pair the owner with `/pair <TELEGRAM_PAIRING_SECRET>`.
3. Send one normal message and confirm the bot replies through the OpenAI API.

Do not consider deployment complete until all three checks pass.
