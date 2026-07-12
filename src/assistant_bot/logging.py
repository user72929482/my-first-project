import logging
import re

SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_-]+|\d{6,}:[A-Za-z0-9_-]+|TELEGRAM_PAIRING_SECRET=[^\s]+)")


def redact(value: object) -> object:
    if isinstance(value, str):
        return SECRET_RE.sub("[REDACTED]", value)
    return value


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(message)s")
    try:
        import structlog
    except Exception:
        return
    structlog.configure(
        processors=[
            lambda _, __, event: {k: redact(v) for k, v in event.items()},
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
    )
