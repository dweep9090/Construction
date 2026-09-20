from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IssueBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "MEDIUM"
    is_blocking: bool = False
    task_id: Optional[int] = None

class IssueCreate(IssueBase):
    pass

class IssueUpdate(BaseModel):
    status: str

class IssueResponse(IssueBase):
    id: int
    project_id: int
    status: str
    reported_by: int
    resolved_by: Optional[int] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
