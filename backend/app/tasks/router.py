from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.core.database import get_db
from app.models.tasks import Task, TaskDependency, TaskProgress
from app.models.issues import Issue
from app.models.users import User
from app.auth.router import get_current_user
from app.auth.dependencies import get_current_user_project_role
from app.tasks.schemas import (
    TaskCreate, TaskUpdate, TaskStatusUpdate, TaskProgressUpdate, 
    TaskResponse, TaskDependencyCreate, TaskDependencyResponse
)
from app.scheduling.service import recalculate_project
from app.scheduling.engine import EngineTask, EngineDependency, detect_cycle
from app.audit.service import record_audit

router = APIRouter(tags=["tasks"])

@router.post("/api/projects/{project_id}/tasks", response_model=TaskResponse)
def create_task(project_id: int, task_in: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if role != "PROJECT_MANAGER" and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Not authorized to create tasks")
        
    task = Task(**task_in.model_dump(), project_id=project_id)
    if task.assignee_id:
        task.status = "ASSIGNED"
    db.add(task)
    db.commit()
    db.refresh(task)
    
    record_audit(db, project_id, "CREATE", "Task", task.id, new_value=task.name, user=current_user, role=role)
    recalculate_project(db, project_id)
    db.refresh(task)
    return task

@router.get("/api/projects/{project_id}/tasks", response_model=List[TaskResponse])
def list_tasks(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if not role and current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(Task).filter(Task.project_id == project_id).all()

@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    role = get_current_user_project_role(task.project_id, db, current_user)
    if not role and current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return task

@router.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    role = get_current_user_project_role(task.project_id, db, current_user)
    if role != "PROJECT_MANAGER" and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    for var, value in task_in.model_dump(exclude_unset=True).items():
        setattr(task, var, value)
        
    db.commit()
    record_audit(db, task.project_id, "UPDATE", "Task", task.id, new_value="Updated fields", user=current_user, role=role)
    recalculate_project(db, task.project_id)
    db.refresh(task)
    return task

@router.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    role = get_current_user_project_role(task.project_id, db, current_user)
    if role != "PROJECT_MANAGER" and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.query(TaskDependency).filter((TaskDependency.predecessor_task_id == task_id) | (TaskDependency.successor_task_id == task_id)).delete()
    
    project_id = task.project_id
    db.delete(task)
    db.commit()
    record_audit(db, project_id, "DELETE", "Task", task_id, user=current_user, role=role)
    recalculate_project(db, project_id)

@router.post("/api/tasks/{task_id}/status", response_model=TaskResponse)
def update_task_status(task_id: int, status_in: TaskStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    role = get_current_user_project_role(task.project_id, db, current_user)
    if not role:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    new_status = status_in.status
    old_status = task.status
    
    # Validation logic
    if new_status == "SUBMITTED":
        if role not in ["SITE_ENGINEER", "CONTRACTOR"]:
            raise HTTPException(status_code=403, detail="Only assigned engineers/contractors can submit work")
        
    elif new_status == "COMPLETED":
        if role not in ["QUALITY_INSPECTOR", "PROJECT_MANAGER"]:
            raise HTTPException(status_code=403, detail="Only Quality Inspector or PM can approve and complete tasks")
        
    if new_status == "IN_PROGRESS" and task.status != "IN_PROGRESS":
        preds = db.query(Task).join(TaskDependency, TaskDependency.predecessor_task_id == Task.id).filter(TaskDependency.successor_task_id == task_id).all()
        incomplete = [p.name for p in preds if p.status != "COMPLETED"]
        if incomplete:
            raise HTTPException(status_code=400, detail=f"Task cannot start because predecessor '{incomplete[0]}' is not completed.")
        
        task.actual_start = status_in.actual_start or date.today()
        
    elif new_status == "COMPLETED" and task.status != "COMPLETED":
        preds = db.query(Task).join(TaskDependency, TaskDependency.predecessor_task_id == Task.id).filter(TaskDependency.successor_task_id == task_id).all()
        incomplete = [p.name for p in preds if p.status != "COMPLETED"]
        if incomplete:
            raise HTTPException(status_code=400, detail=f"Task cannot complete because predecessor '{incomplete[0]}' is not completed.")
        
        task.progress = 100
        task.actual_end = status_in.actual_end or date.today()
        if not task.actual_start:
            task.actual_start = task.actual_end

    task.status = new_status
    db.commit()
    record_audit(db, task.project_id, "STATUS_CHANGE", "Task", task.id, previous_value=old_status, new_value=new_status, user=current_user, role=role)
    recalculate_project(db, task.project_id)
    db.refresh(task)
    return task

@router.post("/api/tasks/{task_id}/progress", response_model=TaskResponse)
def update_progress(task_id: int, prog_in: TaskProgressUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    role = get_current_user_project_role(task.project_id, db, current_user)
    if role not in ["SITE_ENGINEER", "CONTRACTOR", "PROJECT_MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to update progress")
        
    if not (0 <= prog_in.progress <= 100):
        raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")
        
    tp = TaskProgress(task_id=task_id, progress=prog_in.progress, note=prog_in.note, reported_by=current_user.id)
    db.add(tp)
    
    old_prog = task.progress
    task.progress = prog_in.progress
    
    if prog_in.progress > 0 and task.status in ["NOT_STARTED", "ASSIGNED"]:
        preds = db.query(Task).join(TaskDependency, TaskDependency.predecessor_task_id == Task.id).filter(TaskDependency.successor_task_id == task_id).all()
        incomplete = [p.name for p in preds if p.status != "COMPLETED"]
        if incomplete:
            raise HTTPException(status_code=400, detail=f"Task cannot start because predecessor '{incomplete[0]}' is not completed.")
        task.status = "IN_PROGRESS"
        task.actual_start = date.today()
        
    db.commit()
    record_audit(db, task.project_id, "PROGRESS_UPDATE", "Task", task.id, previous_value=str(old_prog), new_value=str(prog_in.progress), user=current_user, role=role)
    recalculate_project(db, task.project_id)
    db.refresh(task)
    return task

@router.post("/api/tasks/{task_id}/dependencies", response_model=TaskDependencyResponse)
def create_dependency(task_id: int, dep_in: TaskDependencyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    role = get_current_user_project_role(task.project_id, db, current_user)
    if role != "PROJECT_MANAGER" and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if task_id == dep_in.predecessor_id:
        raise HTTPException(status_code=400, detail="A task cannot depend on itself.")
        
    pred = db.query(Task).filter(Task.id == dep_in.predecessor_id).first()
    if not pred or task.project_id != pred.project_id:
        raise HTTPException(status_code=400, detail="Tasks must belong to the same project.")
        
    all_tasks = db.query(Task).filter(Task.project_id == task.project_id, Task.is_summary == False).all()
    all_deps = db.query(TaskDependency).join(Task, Task.id == TaskDependency.successor_task_id).filter(Task.project_id == task.project_id).all()
    
    eng_tasks = [EngineTask(id=t.id, planned_start=date.today(), planned_end=date.today(), duration=1, status="NOT_STARTED", progress=0) for t in all_tasks]
    eng_deps = [EngineDependency(d.predecessor_task_id, d.successor_task_id, d.lag_days) for d in all_deps]
    eng_deps.append(EngineDependency(pred.id, task.id, dep_in.lag_days))
    
    cycle = detect_cycle(eng_tasks, eng_deps)
    if cycle:
        raise HTTPException(status_code=409, detail=f"Dependency creates a cycle: {cycle}")
        
    new_dep = TaskDependency(predecessor_task_id=pred.id, successor_task_id=task.id, lag_days=dep_in.lag_days)
    db.add(new_dep)
    db.commit()
    
    record_audit(db, task.project_id, "CREATE", "Dependency", new_dep.id, user=current_user, role=role)
    recalculate_project(db, task.project_id)
    db.refresh(new_dep)
    return new_dep

@router.get("/api/tasks/{task_id}/dependencies", response_model=List[TaskDependencyResponse])
def get_dependencies(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    role = get_current_user_project_role(task.project_id, db, current_user)
    if not role and current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(TaskDependency).filter(TaskDependency.successor_task_id == task_id).all()

@router.delete("/api/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dependency(dependency_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dep = db.query(TaskDependency).filter(TaskDependency.id == dependency_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")
        
    task_id = dep.successor_task_id
    task = db.query(Task).filter(Task.id == task_id).first()
    
    role = get_current_user_project_role(task.project_id, db, current_user)
    if role != "PROJECT_MANAGER" and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(dep)
    db.commit()
    record_audit(db, task.project_id, "DELETE", "Dependency", dependency_id, user=current_user, role=role)
    if task:
        recalculate_project(db, task.project_id)
