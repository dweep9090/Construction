from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.core.database import get_db
from app.models.projects import Project, ProjectMember
from app.models.tasks import Task, TaskDependency
from app.models.users import User
from app.auth.router import get_current_user
from app.auth.dependencies import RequireProjectRole, get_current_user_project_role
from app.projects.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ScheduleResponse, ScheduleTaskResponse
from app.scheduling.service import recalculate_project
from app.scheduling.engine import topological_sort, EngineTask, EngineDependency
from app.audit.service import record_audit

router = APIRouter(tags=["projects"])

@router.get("/api/public/projects", response_model=List[ProjectResponse])
def list_public_projects(db: Session = Depends(get_db)):
    return db.query(Project).filter(Project.is_public == 1).all()

@router.get("/api/public/projects/{project_id}", response_model=ProjectResponse)
def get_public_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.is_public == 1).first()
    if not project:
        raise HTTPException(status_code=404, detail="Public project not found")
    return project

@router.get("/api/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role in ["PROJECT_DIRECTOR", "AUDITOR"]:
        return db.query(Project).all()
    # Otherwise, join with ProjectMember
    return db.query(Project).join(ProjectMember).filter(ProjectMember.user_id == current_user.id).all()

@router.post("/api/projects", response_model=ProjectResponse)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["PROJECT_DIRECTOR", "PROJECT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to create projects")
        
    project = Project(**project_in.model_dump(), created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Make creator a member
    pm = ProjectMember(project_id=project.id, user_id=current_user.id, role="PROJECT_MANAGER")
    db.add(pm)
    db.commit()
    
    record_audit(db, project.id, "CREATE", "Project", project.id, new_value=project.name, user=current_user, role=current_user.role)
    
    return project

@router.get("/api/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"] and not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
        
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/api/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int, 
    project_in: ProjectUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    role = get_current_user_project_role(project_id, db, current_user)
    if current_user.role != "PROJECT_DIRECTOR" and role != "PROJECT_MANAGER":
        raise HTTPException(status_code=403, detail="Not authorized to update project")
        
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    for var, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project, var, value)
        
    db.commit()
    db.refresh(project)
    record_audit(db, project.id, "UPDATE", "Project", project.id, new_value=f"Updated properties", user=current_user, role=role)
    return project

@router.post("/api/projects/{project_id}/baseline/approve")
def approve_baseline(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only PROJECT_DIRECTOR can approve baseline
    if current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Only Project Director can approve baseline")
        
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.baseline_status = "APPROVED"
    db.commit()
    
    record_audit(db, project.id, "APPROVE", "Baseline", project.id, previous_value="DRAFT", new_value="APPROVED", user=current_user, role="PROJECT_DIRECTOR")
    return {"status": "Baseline approved"}

@router.get("/api/projects/{project_id}/schedule", response_model=ScheduleResponse)
def get_schedule(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"] and not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")
        
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    db_tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_summary == False).all()
    task_ids = [t.id for t in db_tasks]
    db_deps = db.query(TaskDependency).filter(
        TaskDependency.predecessor_task_id.in_(task_ids),
        TaskDependency.successor_task_id.in_(task_ids)
    ).all()
    
    eng_tasks = [EngineTask(id=t.id, planned_start=t.planned_start, planned_end=t.planned_end, duration=t.duration, status=t.status, progress=t.progress) for t in db_tasks]
    eng_deps = [EngineDependency(d.predecessor_task_id, d.successor_task_id, d.lag_days) for d in db_deps]
    
    try:
        sorted_ids = topological_sort(eng_tasks, eng_deps)
    except ValueError:
        sorted_ids = [t.id for t in db_tasks] # fallback
        
    task_dict = {t.id: t for t in db_tasks}
    critical_path_names = [task_dict[tid].name for tid in sorted_ids if task_dict[tid].is_critical]
    
    sched_tasks = [
        ScheduleTaskResponse(
            id=t.id,
            name=t.name,
            early_start=t.early_start,
            early_finish=t.early_finish,
            late_start=t.late_start,
            late_finish=t.late_finish,
            float_days=t.total_float or 0,
            is_critical=t.is_critical
        ) for t in db_tasks
    ]
    
    return {
        "project_id": project.id,
        "project_start": project.start_date,
        "planned_completion": project.baseline_end,
        "forecast_completion": project.forecast_end,
        "delay_days": project.delay_days,
        "critical_path": critical_path_names,
        "tasks": sched_tasks
    }
