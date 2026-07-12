from pathlib import Path
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from assistant_bot.config import Settings
from assistant_bot.db.models import Task
from assistant_bot.db.session import SessionLocal
from assistant_bot.services.auth import AuthService
from assistant_bot.services.files import validate_upload
from assistant_bot.services.projects import ProjectService
from assistant_bot.services.tasks import TaskService

MAX_MSG = 3900

def chunks(text: str):
    for i in range(0, len(text), MAX_MSG): yield text[i:i+MAX_MSG]

class TelegramApp:
    def __init__(self, settings: Settings, tasks: TaskService):
        self.settings=settings; self.auth=AuthService(settings); self.projects=ProjectService(settings.workspace_root); self.tasks=tasks
    async def guard(self, update: Update) -> bool:
        user = update.effective_user
        if not user: return False
        async with SessionLocal() as session:
            if await self.auth.is_authorized(session, user.id): return True
        if update.message: await update.message.reply_text("This private assistant is locked. Use /pair <secret> if you are the owner.")
        return False
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.guard(update): await update.message.reply_text("Private AI executive assistant is online. Send a task or /help.")
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        await update.message.reply_text("Commands: /newproject name, /projects, /useproject id, /status, /tasks, /cancel id, /files, /memory, /settings, /approve id, /reject id, /whoami, /health. You can also speak naturally.")
    async def pair(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user=update.effective_user; secret=" ".join(context.args)
        async with SessionLocal() as session:
            ok = await self.auth.pair(session, user.id, secret)
        await update.message.reply_text("Owner paired successfully. Pairing secret invalidated." if ok else "Pairing failed.")
    async def whoami(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"Telegram numeric user ID: {update.effective_user.id}")
    async def health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.guard(update): await update.message.reply_text("OK: bot, database, and task service are reachable.")
    async def newproject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        name = " ".join(context.args) or "New Project"
        async with SessionLocal() as session:
            p = await self.projects.create(session, name)
        context.user_data["project_id"] = p.id
        await update.message.reply_text(f"Created and selected project #{p.id}: {p.name}")
    async def projects_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        async with SessionLocal() as session: projects = await self.projects.list(session)
        text = "\n".join(f"#{p.id} {p.name} — {p.status}" for p in projects) or "No projects yet."
        await update.message.reply_text(text)
    async def useproject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        context.user_data["project_id"] = int(context.args[0]) if context.args else None
        await update.message.reply_text(f"Selected project {context.user_data.get('project_id')}")
    async def memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        async with SessionLocal() as session: memories = await self.projects.memories(session)
        await update.message.reply_text("\n".join(f"{m.key}: {m.value}" for m in memories) or "No memory stored yet.")
    async def text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        await update.message.chat.send_action(ChatAction.TYPING)
        async with SessionLocal() as session:
            t = await self.tasks.create_task(session, update.effective_user.id, update.message.text, context.user_data.get("project_id"))
        await update.message.reply_text(f"Task #{t.id} accepted. I’ll work on it and report progress. Use /status or /cancel {t.id}.")
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        async with SessionLocal() as session:
            task = session.latest_task()
        if not task: await update.message.reply_text("No tasks yet."); return
        text = f"Task #{task.id}: {task.status}\n{task.progress}\n{task.result or task.error}"
        for part in chunks(text): await update.message.reply_text(part)
    async def tasks_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        async with SessionLocal() as session:
            tasks = session.list_tasks()
        await update.message.reply_text("\n".join(f"#{t.id} {t.status}: {t.description[:60]}" for t in tasks) or "No tasks.")
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        tid = int(context.args[0]) if context.args else 0
        ok = self.tasks.cancel(tid)
        await update.message.reply_text("Cancellation requested." if ok else "Task is not running or was already finished.")
    async def file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        doc = update.message.document or (update.message.photo[-1] if update.message.photo else None)
        if not doc: return
        name = getattr(doc, "file_name", "telegram-upload.bin")
        validate_upload(name, getattr(doc, "file_size", 0) or 0, self.settings.max_upload_mb)
        await update.message.reply_text(f"Accepted file {name}. It will be preserved and processed as untrusted content.")
    async def simple(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.guard(update): await update.message.reply_text("This command is implemented as a safe placeholder and will be expanded by tasks/approvals modules.")

def build_application(settings: Settings, tasks: TaskService) -> Application:
    app = ApplicationBuilder().token(settings.telegram_bot_token.get_secret_value()).build()
    tg = TelegramApp(settings, tasks)
    for name, fn in [("start",tg.start),("help",tg.help),("pair",tg.pair),("newproject",tg.newproject),("projects",tg.projects_cmd),("useproject",tg.useproject),("status",tg.status),("tasks",tg.tasks_cmd),("cancel",tg.cancel),("memory",tg.memory),("whoami",tg.whoami),("health",tg.health)]: app.add_handler(CommandHandler(name, fn))
    for name in ["files","settings","approve","reject"]: app.add_handler(CommandHandler(name, tg.simple))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VOICE, tg.file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg.text))
    return app
