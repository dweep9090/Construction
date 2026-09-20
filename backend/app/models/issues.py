from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(String)
    severity = Column(String, default="MEDIUM")
    is_blocking = Column(Boolean, default=False)
    status = Column(String, default="OPEN")
    
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
