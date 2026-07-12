# Security Notes

- Authorize by numeric Telegram ID or one-time `/pair <secret>`.
- Never commit `.env`; `.gitignore` excludes secrets and runtime data.
- Uploaded content is treated as untrusted data and validated by size and extension.
- ZIP paths are checked for traversal.
- Irreversible external actions must be recorded as approvals before execution.
- Use Docker or another sandbox for code execution in production. Mount workspaces separately and back up `data/`.
