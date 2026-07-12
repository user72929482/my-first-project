import asyncio, subprocess
from pathlib import Path

async def run_in_workspace(workspace: Path, command: list[str], timeout: int = 120) -> str:
    workspace.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(*command, cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill(); return "Command timed out"
    return out.decode(errors="replace")[-8000:]

async def init_git(workspace: Path) -> str:
    await run_in_workspace(workspace, ["git", "init"], 30)
    return await run_in_workspace(workspace, ["git", "status", "--short"], 30)
