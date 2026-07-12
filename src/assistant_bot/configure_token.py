import getpass
import os
import re
from pathlib import Path

TOKEN_PATTERN = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{20,}$")


def _read_env(path: Path) -> list[str]:
    return path.read_text().splitlines() if path.exists() else []


def _upsert(lines: list[str], key: str, value: str) -> list[str]:
    replacement = f"{key}={value}"
    updated: list[str] = []
    seen = False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            updated.append(replacement)
            seen = True
        else:
            updated.append(line)
    if not seen:
        updated.append(replacement)
    return updated


def configure_token(env_path: str = ".env") -> int:
    path = Path(env_path)
    print("Paste your Telegram bot token from BotFather. Input is hidden and will not be printed.")
    token = getpass.getpass("TELEGRAM_BOT_TOKEN: ").strip()
    if not TOKEN_PATTERN.match(token):
        print("Token was not saved: it does not look like a Telegram bot token.")
        return 2
    lines = _read_env(path)
    lines = _upsert(lines, "TELEGRAM_BOT_TOKEN", token)
    if not any(line.startswith("TELEGRAM_PAIRING_SECRET=") for line in lines):
        lines = _upsert(lines, "TELEGRAM_PAIRING_SECRET", getpass.getpass("One-time pairing secret to use with /pair: ").strip())
    path.write_text("\n".join(lines).rstrip() + "\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    print(f"Saved token securely to {path} with restricted permissions. The token was not displayed.")
    return 0


def main() -> None:
    raise SystemExit(configure_token())


if __name__ == "__main__":
    main()
