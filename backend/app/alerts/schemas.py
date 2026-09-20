from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertResponse(BaseModel):
    id: int
    project_id: int
    task_id: Optional[int] = None
    type: str
    severity: str
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
