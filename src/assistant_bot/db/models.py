from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Owner: id:int=0; telegram_user_id:int=0; active:bool=True; paired_at:datetime=field(default_factory=datetime.utcnow)
@dataclass
class Project: id:int=0; name:str=""; objective:str=""; status:str="active"; workspace_path:str=""; context:dict=field(default_factory=dict); created_at:datetime=field(default_factory=datetime.utcnow); updated_at:datetime=field(default_factory=datetime.utcnow)
@dataclass
class Memory: id:int=0; project_id:int|None=None; key:str=""; value:str=""; created_at:datetime=field(default_factory=datetime.utcnow)
@dataclass
class Task: id:int=0; project_id:int|None=None; user_id:int=0; description:str=""; status:str="queued"; progress:str="Queued"; result:str=""; error:str=""; created_at:datetime=field(default_factory=datetime.utcnow); updated_at:datetime=field(default_factory=datetime.utcnow)
@dataclass
class FileRecord: id:int=0; project_id:int|None=None; original_name:str=""; stored_path:str=""; media_type:str="application/octet-stream"; created_at:datetime=field(default_factory=datetime.utcnow)
@dataclass
class Approval: id:int=0; action:str=""; status:str="pending"; created_at:datetime=field(default_factory=datetime.utcnow)
