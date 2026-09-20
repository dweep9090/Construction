from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_summary: bool = False
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    duration: Optional[int] = None
    priority: str = "MEDIUM"
    assignee_id: Optional[int] = None

class TaskCreate(TaskBase):
    parent_id: Optional[int] = None

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    duration: Optional[int] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None

class TaskStatusUpdate(BaseModel):
    status: str
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None

class TaskProgressUpdate(BaseModel):
    progress: int
    note: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    project_id: int
    parent_id: Optional[int] = None
    status: str
    progress: int
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    
    forecast_start: Optional[date] = None
    forecast_end: Optional[date] = None
    early_start: Optional[date] = None
    early_finish: Optional[date] = None
    late_start: Optional[date] = None
    late_finish: Optional[date] = None
    total_float: Optional[int] = None
    is_critical: bool = False
    delay_days: int = 0
    
    class Config:
        from_attributes = True

class TaskDependencyCreate(BaseModel):
    predecessor_id: int
    lag_days: int = 0

class TaskDependencyResponse(BaseModel):
    id: int
    predecessor_task_id: int
    successor_task_id: int
    dependency_type: str
    lag_days: int

    class Config:
        from_attributes = True
