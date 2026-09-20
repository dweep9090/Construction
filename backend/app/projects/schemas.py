from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_date: date
    budget: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    baseline_end: Optional[date] = None
    forecast_end: Optional[date] = None
    delay_days: int = 0
    health: str
    status: str
    
    class Config:
        from_attributes = True

class ScheduleTaskResponse(BaseModel):
    id: int
    name: str
    early_start: Optional[date] = None
    early_finish: Optional[date] = None
    late_start: Optional[date] = None
    late_finish: Optional[date] = None
    float_days: int = 0
    is_critical: bool = False
    
    class Config:
        from_attributes = True

class ScheduleResponse(BaseModel):
    project_id: int
    project_start: date
    planned_completion: Optional[date] = None
    forecast_completion: Optional[date] = None
    delay_days: int = 0
    critical_path: List[str]
    tasks: List[ScheduleTaskResponse]
