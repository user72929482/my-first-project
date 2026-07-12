import asyncio
from assistant_bot.agents.factory import AssistantAgent
from assistant_bot.db.models import Task

class TaskService:
    def __init__(self, maker, agent: AssistantAgent, max_concurrent: int): self.maker=maker; self.agent=agent; self.sem=asyncio.Semaphore(max_concurrent); self.running={}
    async def create_task(self, session, user_id:int, description:str, project_id:int|None=None)->Task:
        t=session.add_task(Task(user_id=user_id,description=description,project_id=project_id)); await session.commit(); self.running[t.id]=asyncio.create_task(self._run(t.id)); return t
    async def _run(self, task_id:int):
        async with self.sem, self.maker() as session:
            t=session.get_task(task_id); 
            if not t: return
            t.status='running'; t.progress='Planning and executing'; session.update_task(t); await session.commit()
            try:
                r=await self.agent.run(t.description); t.status='completed'; t.progress='Completed'; t.result=r.text[:12000]
            except asyncio.CancelledError: t.status='cancelled'; t.progress='Cancelled by owner'
            except Exception as exc: t.status='failed'; t.error=type(exc).__name__; t.progress='Failed safely'
            session.update_task(t); await session.commit()
    def cancel(self, task_id:int)->bool:
        task=self.running.get(task_id)
        if task and not task.done(): task.cancel(); return True
        return False
