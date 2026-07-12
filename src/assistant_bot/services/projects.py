import re
from pathlib import Path
from assistant_bot.db.models import Project, Memory
SAFE = re.compile(r"[^a-zA-Z0-9_.-]+")
def slugify(name: str) -> str: return SAFE.sub("-", name.strip()).strip("-").lower()[:80] or "project"
class ProjectService:
    def __init__(self, workspace_root: Path): self.workspace_root=Path(workspace_root); self.workspace_root.mkdir(parents=True, exist_ok=True)
    async def create(self, session, name: str, objective: str = "") -> Project:
        path=self.workspace_root/slugify(name); path.mkdir(parents=True, exist_ok=True)
        p=session.add_project(Project(name=name[:120], objective=objective, workspace_path=str(path), context={})); await session.commit(); return p
    async def list(self, session) -> list[Project]: return session.list_projects()
    async def remember(self, session, key: str, value: str, project_id: int | None = None) -> None:
        session.add_memory(Memory(project_id=project_id,key=key[:120],value=value[:4000])); await session.commit()
    async def memories(self, session, project_id: int | None = None) -> list[Memory]: return session.list_memories(project_id)
