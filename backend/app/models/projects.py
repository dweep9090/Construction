from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    location = Column(String)
    start_date = Column(Date, nullable=False)
    
    baseline_end = Column(Date)
    forecast_end = Column(Date)
    delay_days = Column(Integer, default=0)
    health = Column(String, default="GREEN")
    status = Column(String, default="PLANNING")
    budget = Column(String, nullable=True) # display only
    
    is_public = Column(Integer, default=0) # SQLite/DB compatible boolean
    baseline_status = Column(String, default="DRAFT") # DRAFT, SUBMITTED, APPROVED, REJECTED
    
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    creator = relationship("User")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)
    
    project = relationship("Project", back_populates="members")
    user = relationship("User")
