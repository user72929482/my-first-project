# Private Telegram AI Executive Assistant

A private, owner-controlled Telegram assistant for project management, document intake, coding workspaces, long-running tasks, and OpenAI-agent responses.

## What it does

- Locks access to your permanent numeric Telegram user ID.
- Supports first-run pairing with `/pair <secret>`.
- Accepts natural-language tasks and tracks them as persistent background jobs.
- Keeps projects, task history, memory, file records, and approvals in SQLite locally or PostgreSQL via `DATABASE_URL`.
- Uses the official OpenAI Python SDK and OpenAI Agents SDK through a configurable executive coordinator agent.
- Provides safe upload validation for PDFs, Word, Excel, CSV, text/code, images, voice placeholders, and ZIP path safety.
- Creates isolated per-project workspace folders with Git support and documented Docker sandboxing.

## 1. Create the Telegram bot

1. Open Telegram and message **@BotFather**.
2. Send `/newbot` and follow BotFather's prompts.
3. Copy the token BotFather gives you.
4. Do **not** paste the token into source code or chat logs.

## 2. Enter secrets safely

```bash
cp .env.example .env
```

Edit `.env` on the server only:

```text
TELEGRAM_BOT_TOKEN=your BotFather token
TELEGRAM_PAIRING_SECRET=a long random one-time phrase
OPENAI_API_KEY=your OpenAI API key
```

Optional: set `TELEGRAM_ALLOWED_USER_ID` if you already know your numeric Telegram ID.

## 3. Start locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
assistant-smoke
assistant-configure-token
assistant-verify-telegram
assistant-bot
```


## Secure token setup (recommended)

After installing the project, run this command on the computer or server where the bot will run:

```bash
assistant-configure-token
```

It opens a hidden prompt for your BotFather token, saves it only in your local `.env` file, restricts that file to your user account, and does not print the token to logs. Then run:

```bash
assistant-verify-telegram
assistant-bot
```

When `assistant-bot` is running, open Telegram and send `/start` to your bot.

## 4. Pair your Telegram account

Open your bot in Telegram and send:

```text
/pair your-long-random-one-time-phrase
```

After pairing, only your numeric Telegram account can use the assistant.

## 5. Test the assistant

Send:

```text
/newproject First Website
Build me a simple landing page plan and save the next steps.
/status
```

## 6. Deploy with Docker

```bash
docker compose up -d --build
```

Keep `.env`, `data/`, and `workspaces/` backed up. Do not publish them.

## 7. Update

```bash
git pull
pip install -e '.[dev]'
assistant-smoke
sudo systemctl restart assistant-bot  # if using systemd
```

With Docker:

```bash
docker compose up -d --build
```

## 8. Back up

For SQLite local mode, stop the bot and copy:

```bash
cp -a data workspaces backup-$(date +%Y%m%d)
```

For PostgreSQL, use your provider's backup tools or `pg_dump`.

## 9. Recover from common errors

See `docs/TROUBLESHOOTING.md`. The most common issues are an invalid Telegram token, failed pairing secret, missing OpenAI API key, or an unavailable model.

## 10. Stop or revoke access

Stop Docker:

```bash
docker compose down
```

Revoke the Telegram token in BotFather with `/revoke`. To reset owner pairing, back up the database, then remove the owner row from the `owners` table or create a fresh database.

## Commands

`/start`, `/help`, `/newproject`, `/projects`, `/useproject`, `/status`, `/tasks`, `/cancel`, `/files`, `/memory`, `/settings`, `/approve`, `/reject`, `/whoami`, `/health`.

## Automated smoke test

```bash
assistant-smoke
```

The smoke test verifies startup-critical configuration, database schema creation, unauthorized rejection, owner authorization, project persistence across restart, file validation, Git workspace setup, and isolated command execution.

## Current deployment status

The repository is production-oriented but external services are not deployed by this build process. Add real values to `.env`, run `assistant-smoke`, run `assistant-verify-telegram`, then start `assistant-bot` or `docker compose up -d --build`.


## If the bot does not respond

1. Confirm `.env` contains `TELEGRAM_BOT_TOKEN` from BotFather.
2. Run `assistant-verify-telegram` to confirm Telegram accepts the token.
3. Restart with `assistant-bot` or `docker compose restart assistant`.
4. Send `/start` to the bot in Telegram.
