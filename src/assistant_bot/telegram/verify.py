import json
import os
import sys
import urllib.error
import urllib.request

from assistant_bot.config import settings


def verify_token() -> int:
    token = settings.telegram_bot_token.get_secret_value() or os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token or token.startswith("123456:"):
        print("TELEGRAM_BOT_TOKEN is not configured", file=sys.stderr)
        return 2
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"Telegram rejected the token: HTTP {exc.code}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"Could not reach Telegram getMe: {type(exc).__name__}", file=sys.stderr)
        return 4
    if not payload.get("ok"):
        print("Telegram getMe returned not ok", file=sys.stderr)
        return 5
    user = payload.get("result", {})
    print(f"Telegram token verified for bot @{user.get('username', '<unknown>')}")
    return 0


def main() -> None:
    raise SystemExit(verify_token())


if __name__ == "__main__":
    main()
