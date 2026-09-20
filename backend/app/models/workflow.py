from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    reason = Column(String, nullable=True)
    impact_days = Column(Integer, default=0)
    
    # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, IMPLEMENTED
    status = Column(String, default="DRAFT")
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User")
    project = relationship("Project")
