from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.alerts import Alert
from app.models.users import User
from app.auth.router import get_current_user
from app.auth.dependencies import get_current_user_project_role
from app.alerts.schemas import AlertResponse
from app.audit.service import record_audit

router = APIRouter(tags=["alerts"])

@router.get("/api/projects/{project_id}/alerts", response_model=List[AlertResponse])
def get_alerts(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if not role and current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    query = db.query(Alert).filter(Alert.project_id == project_id)
    if status:
        query = query.filter(Alert.status == status)
    return query.all()

@router.post("/api/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    role = get_current_user_project_role(alert.project_id, db, current_user)
    if role != "PROJECT_MANAGER" and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Not authorized to acknowledge alerts")
        
    alert.status = "ACKNOWLEDGED"
    db.commit()
    record_audit(db, alert.project_id, "ACKNOWLEDGE", "Alert", alert.id, user=current_user, role=role)
    db.refresh(alert)
    return alert
