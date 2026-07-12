import sqlite3, json
from pathlib import Path
from datetime import datetime
from assistant_bot.db.models import Owner, Project, Memory, Task

_db_path = Path("data/assistant.db")

def _path_from_url(url: str) -> Path:
    return Path(url.removeprefix("sqlite+aiosqlite:///").removeprefix("sqlite:///"))

def init_engine(database_url: str):
    global _db_path
    _db_path = _path_from_url(database_url); _db_path.parent.mkdir(parents=True, exist_ok=True); return _db_path

async def create_schema() -> None:
    con=sqlite3.connect(_db_path); cur=con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS owners(id INTEGER PRIMARY KEY, telegram_user_id INTEGER UNIQUE, active INTEGER, paired_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, name TEXT, objective TEXT, status TEXT, workspace_path TEXT, context TEXT, created_at TEXT, updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY, project_id INTEGER, key TEXT, value TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, project_id INTEGER, user_id INTEGER, description TEXT, status TEXT, progress TEXT, result TEXT, error TEXT, created_at TEXT, updated_at TEXT)")
    con.commit(); con.close()

class Session:
    def __init__(self): self.con=sqlite3.connect(_db_path)
    async def __aenter__(self): return self
    async def __aexit__(self,*a): self.con.close()
    async def commit(self): self.con.commit()
    def owner_by_user(self, uid:int):
        r=self.con.execute("SELECT id,telegram_user_id,active,paired_at FROM owners WHERE telegram_user_id=? AND active=1",(uid,)).fetchone(); return Owner(r[0],r[1],bool(r[2])) if r else None
    def any_owner(self): return self.con.execute("SELECT id FROM owners WHERE active=1").fetchone()
    def add_owner(self, uid:int): self.con.execute("INSERT INTO owners(telegram_user_id,active,paired_at) VALUES(?,?,?)",(uid,1,datetime.utcnow().isoformat()))
    def add_project(self,p:Project):
        cur=self.con.execute("INSERT INTO projects(name,objective,status,workspace_path,context,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(p.name,p.objective,p.status,p.workspace_path,json.dumps(p.context),p.created_at.isoformat(),p.updated_at.isoformat())); p.id=cur.lastrowid; return p
    def list_projects(self):
        return [Project(id=r[0],name=r[1],objective=r[2],status=r[3],workspace_path=r[4],context=json.loads(r[5] or '{}')) for r in self.con.execute("SELECT id,name,objective,status,workspace_path,context FROM projects ORDER BY updated_at DESC")]
    def add_memory(self,m:Memory): self.con.execute("INSERT INTO memories(project_id,key,value,created_at) VALUES(?,?,?,?)",(m.project_id,m.key,m.value,m.created_at.isoformat()))
    def list_memories(self): return [Memory(id=r[0],project_id=r[1],key=r[2],value=r[3]) for r in self.con.execute("SELECT id,project_id,key,value FROM memories ORDER BY created_at DESC LIMIT 25")]
    def add_task(self,t:Task):
        cur=self.con.execute("INSERT INTO tasks(project_id,user_id,description,status,progress,result,error,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",(t.project_id,t.user_id,t.description,t.status,t.progress,t.result,t.error,t.created_at.isoformat(),t.updated_at.isoformat())); t.id=cur.lastrowid; return t
    def get_task(self,tid:int):
        r=self.con.execute("SELECT id,project_id,user_id,description,status,progress,result,error FROM tasks WHERE id=?",(tid,)).fetchone(); return Task(id=r[0],project_id=r[1],user_id=r[2],description=r[3],status=r[4],progress=r[5],result=r[6],error=r[7]) if r else None
    def update_task(self,t:Task): self.con.execute("UPDATE tasks SET status=?,progress=?,result=?,error=?,updated_at=? WHERE id=?",(t.status,t.progress,t.result,t.error,datetime.utcnow().isoformat(),t.id))
    def latest_task(self):
        r=self.con.execute("SELECT id,project_id,user_id,description,status,progress,result,error FROM tasks ORDER BY created_at DESC LIMIT 1").fetchone(); return Task(id=r[0],project_id=r[1],user_id=r[2],description=r[3],status=r[4],progress=r[5],result=r[6],error=r[7]) if r else None
    def list_tasks(self):
        return [Task(id=r[0],description=r[1],status=r[2]) for r in self.con.execute("SELECT id,description,status FROM tasks ORDER BY created_at DESC LIMIT 10")]

def SessionLocal(): return Session()
