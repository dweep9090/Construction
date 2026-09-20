from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    type = Column(String, nullable=False)
    severity = Column(String, default="WARNING")
    message = Column(String, nullable=False)
    details = Column(Text, nullable=True) # JSON text
    status = Column(String, default="ACTIVE")
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
