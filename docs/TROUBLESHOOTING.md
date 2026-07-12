# Troubleshooting

- Bot does not answer: verify `TELEGRAM_BOT_TOKEN`, network access, and container logs.
- Pairing fails: ensure no owner is already paired and `TELEGRAM_PAIRING_SECRET` matches your `/pair` message.
- OpenAI failures: verify `OPENAI_API_KEY` and model access; tasks are saved and can be retried.
- Database errors: back up `data/assistant.db`, then run `assistant-smoke` in a clean environment.
