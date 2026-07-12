from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from assistant_bot.config import Settings
from assistant_bot.db.models import FileRecord
from assistant_bot.db.session import SessionLocal
from assistant_bot.services.auth import AuthService
from assistant_bot.services.files import safe_filename, validate_upload
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
        user = update.effective_user
        if not user:
            return
        async with SessionLocal() as session:
            authorized = await self.auth.is_authorized(session, user.id)
        if authorized:
            await update.message.reply_text("Private AI assistant is online. Send a normal message, upload a file, or use /help.")
            return
        await update.message.reply_text("Private AI assistant is locked. Pair the owner account with /pair <secret>.")
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
            session.set_selected_project(update.effective_user.id, p.id)
            await session.commit()
        await update.message.reply_text(f"Created and selected project #{p.id}: {p.name}")
    async def projects_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        async with SessionLocal() as session: projects = await self.projects.list(session)
        text = "\n".join(f"#{p.id} {p.name} — {p.status}" for p in projects) or "No projects yet."
        await update.message.reply_text(text)
    async def useproject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        pid = int(context.args[0]) if context.args else None
        async with SessionLocal() as session:
            if pid and not session.get_project(pid):
                await update.message.reply_text(f"Project #{pid} does not exist.")
                return
            session.set_selected_project(update.effective_user.id, pid)
            await session.commit()
        context.user_data["project_id"] = pid
        await update.message.reply_text(f"Selected project {pid or 'none'}")
    async def memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        async with SessionLocal() as session:
            pid = session.selected_project(update.effective_user.id)
            memories = await self.projects.memories(session, pid)
        await update.message.reply_text("\n".join(f"{m.key}: {m.value}" for m in memories) or "No memory stored yet.")
    async def text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        await update.message.chat.send_action(ChatAction.TYPING)
        user_id = update.effective_user.id
        message = update.message.text or ""
        async with SessionLocal() as session:
            project_id = session.selected_project(user_id)
            context.user_data["project_id"] = project_id
            project = session.get_project(project_id)
            memories = await self.projects.memories(session, project_id)
            history = session.recent_messages(user_id, project_id)
            session.add_message(user_id, "user", message, project_id)
            await session.commit()
        context_text = self._context_text(project, memories, history)
        try:
            result = await self.tasks.agent.run(message, context_text)
            reply = result.text
        except Exception as exc:
            reply = str(exc)
        async with SessionLocal() as session:
            session.add_message(user_id, "assistant", reply, project_id)
            await session.commit()
        for part in chunks(reply):
            await update.message.reply_text(part)
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
        name = getattr(doc, "file_name", None) or f"telegram-upload-{doc.file_unique_id}.jpg"
        try:
            validate_upload(name, getattr(doc, "file_size", 0) or 0, self.settings.max_upload_mb)
            tg_file = await doc.get_file()
            async with SessionLocal() as session:
                project_id = session.selected_project(update.effective_user.id)
                dest_dir = self.settings.workspace_root / "uploads" / str(update.effective_user.id) / (str(project_id) if project_id else "unassigned")
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / safe_filename(name)
                await tg_file.download_to_drive(custom_path=dest)
                rec = session.add_file(FileRecord(project_id=project_id, original_name=name, stored_path=str(dest), media_type=getattr(doc, "mime_type", "application/octet-stream") or "application/octet-stream"), update.effective_user.id)
                session.add_message(update.effective_user.id, "user", f"Uploaded file #{rec.id}: {name} stored at {dest}", project_id)
                await session.commit()
            await update.message.reply_text(f"Downloaded file #{rec.id}: {name} ({dest.stat().st_size} bytes). Stored as untrusted content.")
        except Exception as exc:
            await update.message.reply_text(f"File upload failed: {exc}")
    async def files(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.guard(update): return
        async with SessionLocal() as session:
            files = session.list_files(session.selected_project(update.effective_user.id))
        await update.message.reply_text("\n".join(f"#{f.id} {f.original_name} -> {f.stored_path}" for f in files) or "No downloaded files yet.")

    def _context_text(self, project, memories, history) -> str:
        project_text = f"Selected project: #{project.id} {project.name} ({project.objective})" if project else "Selected project: none"
        memory_text = "\n".join(f"- {m.key}: {m.value}" for m in memories) or "No stored memory."
        history_text = "\n".join(f"{role}: {content}" for role, content in history) or "No previous conversation."
        return f"{project_text}\nMemory:\n{memory_text}\nRecent conversation:\n{history_text}"

    async def simple(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.guard(update): await update.message.reply_text("That command is not available yet in this build.")

def build_application(settings: Settings, tasks: TaskService) -> Application:
    app = ApplicationBuilder().token(settings.telegram_bot_token.get_secret_value()).build()
    tg = TelegramApp(settings, tasks)
    for name, fn in [("start",tg.start),("help",tg.help),("pair",tg.pair),("newproject",tg.newproject),("projects",tg.projects_cmd),("useproject",tg.useproject),("status",tg.status),("tasks",tg.tasks_cmd),("cancel",tg.cancel),("memory",tg.memory),("whoami",tg.whoami),("health",tg.health)]: app.add_handler(CommandHandler(name, fn))
    app.add_handler(CommandHandler("files", tg.files))
    for name in ["settings","approve","reject"]: app.add_handler(CommandHandler(name, tg.simple))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VOICE, tg.file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg.text))
    return app
