from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.workflow import ChangeRequest, AuditLog
from app.models.projects import Project
from app.models.users import User
from app.auth.router import get_current_user
from app.auth.dependencies import get_current_user_project_role
from app.audit.service import record_audit
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(tags=["workflow"])

class ChangeRequestCreate(BaseModel):
    title: str
    description: str
    reason: str | None = None
    impact_days: int = 0

class ChangeRequestResponse(ChangeRequestCreate):
    id: int
    project_id: int
    created_by: int
    status: str
    
    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity: str
    entity_id: int | None
    previous_value: str | None
    new_value: str | None
    timestamp: datetime
    role: str | None
    
    class Config:
        from_attributes = True

@router.get("/api/projects/{project_id}/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"] and not role:
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    return db.query(AuditLog).filter(AuditLog.project_id == project_id).order_by(AuditLog.timestamp.desc()).all()

@router.post("/api/projects/{project_id}/change-requests", response_model=ChangeRequestResponse)
def create_change_request(project_id: int, cr_in: ChangeRequestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if role != "PROJECT_MANAGER" and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Only PM or Director can create change requests")
        
    cr = ChangeRequest(
        project_id=project_id,
        created_by=current_user.id,
        title=cr_in.title,
        description=cr_in.description,
        reason=cr_in.reason,
        impact_days=cr_in.impact_days,
        status="SUBMITTED"
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    
    record_audit(db, project_id, "CREATE", "ChangeRequest", cr.id, new_value=cr.title, user=current_user, role=role)
    return cr

@router.get("/api/projects/{project_id}/change-requests", response_model=List[ChangeRequestResponse])
def get_change_requests(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if not role and current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(ChangeRequest).filter(ChangeRequest.project_id == project_id).all()

@router.post("/api/change-requests/{cr_id}/approve", response_model=ChangeRequestResponse)
def approve_change_request(cr_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Only Project Director can approve change requests")
        
    cr = db.query(ChangeRequest).filter(ChangeRequest.id == cr_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
        
    cr.status = "APPROVED"
    cr.reviewed_by = current_user.id
    db.commit()
    
    record_audit(db, cr.project_id, "APPROVE", "ChangeRequest", cr.id, previous_value="SUBMITTED", new_value="APPROVED", user=current_user, role="PROJECT_DIRECTOR")
    return cr

@router.post("/api/change-requests/{cr_id}/reject", response_model=ChangeRequestResponse)
def reject_change_request(cr_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Only Project Director can reject change requests")
        
    cr = db.query(ChangeRequest).filter(ChangeRequest.id == cr_id).first()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
        
    cr.status = "REJECTED"
    cr.reviewed_by = current_user.id
    db.commit()
    
    record_audit(db, cr.project_id, "REJECT", "ChangeRequest", cr.id, previous_value="SUBMITTED", new_value="REJECTED", user=current_user, role="PROJECT_DIRECTOR")
    return cr
