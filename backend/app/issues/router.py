from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.issues import Issue
from app.models.tasks import Task
from app.models.users import User
from app.auth.router import get_current_user
from app.auth.dependencies import get_current_user_project_role
from app.issues.schemas import IssueCreate, IssueUpdate, IssueResponse
from app.scheduling.service import recalculate_project
from app.audit.service import record_audit

router = APIRouter(tags=["issues"])

@router.get("/api/projects/{project_id}/issues", response_model=List[IssueResponse])
def get_issues(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if not role and current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    query = db.query(Issue).filter(Issue.project_id == project_id)
    if status:
        query = query.filter(Issue.status == status)
    return query.all()

@router.post("/api/projects/{project_id}/issues", response_model=IssueResponse)
def create_issue(project_id: int, issue_in: IssueCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if not role and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    issue = Issue(**issue_in.model_dump(), project_id=project_id, reported_by=current_user.id)
    db.add(issue)
    
    if issue.is_blocking and issue.task_id:
        task = db.query(Task).filter(Task.id == issue.task_id).first()
        if task and task.status == "IN_PROGRESS":
            task.status = "BLOCKED"
            
    db.commit()
    record_audit(db, project_id, "CREATE", "Issue", issue.id, new_value=issue.title, user=current_user, role=role)
    recalculate_project(db, project_id)
    db.refresh(issue)
    return issue

@router.get("/api/issues/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
        
    role = get_current_user_project_role(issue.project_id, db, current_user)
    if not role and current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return issue

@router.post("/api/issues/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
        
    role = get_current_user_project_role(issue.project_id, db, current_user)
    if role not in ["PROJECT_MANAGER", "SITE_ENGINEER", "CONTRACTOR"] and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Not authorized to resolve issues")
        
    issue.status = "RESOLVED"
    issue.resolved_by = current_user.id
    issue.resolved_at = datetime.now()
    
    if issue.task_id:
        # Check if task is unblocked
        task = db.query(Task).filter(Task.id == issue.task_id).first()
        if task and task.status == "BLOCKED":
            open_blocking = db.query(Issue).filter(
                Issue.task_id == task.id, 
                Issue.is_blocking == True, 
                Issue.status == "OPEN"
            ).count()
            if open_blocking == 0:
                task.status = "IN_PROGRESS"
                
    db.commit()
    record_audit(db, issue.project_id, "RESOLVE", "Issue", issue.id, user=current_user, role=role)
    recalculate_project(db, issue.project_id)
    db.refresh(issue)
    return issue
