from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    name = Column(String, nullable=False)
    description = Column(String)
    is_summary = Column(Boolean, default=False)
    
    planned_start = Column(Date)
    planned_end = Column(Date)
    duration = Column(Integer)
    
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)
    progress = Column(Integer, default=0)
    status = Column(String, default="NOT_STARTED")
    priority = Column(String, default="MEDIUM")
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    forecast_start = Column(Date)
    forecast_end = Column(Date)
    early_start = Column(Date)
    early_finish = Column(Date)
    late_start = Column(Date)
    late_finish = Column(Date)
    
    total_float = Column(Integer)
    is_critical = Column(Boolean, default=False)
    delay_days = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    predecessor_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    successor_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    dependency_type = Column(String, default="FS")
    lag_days = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('predecessor_task_id', 'successor_task_id', name='uq_task_dependency'),
    )

class TaskProgress(Base):
    __tablename__ = "task_progress"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    progress = Column(Integer, nullable=False)
    note = Column(String)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_at = Column(DateTime(timezone=True), default=utc_now)
