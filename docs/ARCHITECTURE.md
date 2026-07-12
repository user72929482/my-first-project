# Architecture Summary

The app is an async Python Telegram bot with a persistent database, background task runner, owner-only authentication, and an OpenAI Agents SDK coordinator.

- Telegram layer: command handlers, file intake, readable status messages.
- Agent layer: executive coordinator prompt plus named specialist responsibilities.
- Persistence: SQLAlchemy models for owners, projects, memories, tasks, files, approvals.
- Workspaces: per-project directories with Git initialization and subprocess execution hooks intended to be run inside Docker for untrusted code.
- Safety: numeric Telegram authorization, one-time pairing, upload validation, path sanitization, approval records, secret redaction, no secrets in `.env.example`.
