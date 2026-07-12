from assistant_bot.config import Settings

class AuthService:
    def __init__(self, settings: Settings): self.settings = settings
    async def is_authorized(self, session, telegram_user_id: int) -> bool:
        return telegram_user_id == self.settings.telegram_allowed_user_id if self.settings.telegram_allowed_user_id else session.owner_by_user(telegram_user_id) is not None
    async def pair(self, session, telegram_user_id: int, supplied_secret: str) -> bool:
        configured = self.settings.telegram_pairing_secret.get_secret_value() if self.settings.telegram_pairing_secret else ""
        if not configured or supplied_secret != configured or session.any_owner(): return False
        session.add_owner(telegram_user_id); await session.commit(); self.settings.telegram_pairing_secret = None; return True
