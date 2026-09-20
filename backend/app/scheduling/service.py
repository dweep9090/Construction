import json
from datetime import date
from sqlalchemy.orm import Session
from app.models.projects import Project
from app.models.tasks import Task, TaskDependency
from app.models.issues import Issue
from app.models.alerts import Alert
from app.scheduling.engine import (
    EngineTask, 
    EngineDependency, 
    compute_schedule, 
    downstream_impact
)

def recalculate_project(db: Session, project_id: int, today_date: date = None):
    if not today_date:
        today_date = date.today()
        
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return
        
    db_tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_summary == False).all()
    if not db_tasks:
        return
        
    task_ids = [t.id for t in db_tasks]
    db_deps = db.query(TaskDependency).filter(
        TaskDependency.predecessor_task_id.in_(task_ids),
        TaskDependency.successor_task_id.in_(task_ids)
    ).all()
    
    engine_tasks = []
    for t in db_tasks:
        engine_tasks.append(EngineTask(
            id=t.id,
            planned_start=t.planned_start,
            planned_end=t.planned_end,
            duration=t.duration,
            status=t.status,
            progress=t.progress,
            actual_start=t.actual_start,
            actual_end=t.actual_end
        ))
        
    engine_deps = [EngineDependency(d.predecessor_task_id, d.successor_task_id, d.lag_days) for d in db_deps]
    
    project_forecast_end = compute_schedule(engine_tasks, engine_deps, today_date)
    
    # Identify previously delayed tasks to find what newly delayed tasks exist for downstream impact
    prev_delayed = {t.id: t.delay_days for t in db_tasks if t.delay_days and t.delay_days > 0}
    
    # Write back to DB
    for et, db_t in zip(engine_tasks, db_tasks):
        db_t.forecast_start = et.forecast_start
        db_t.forecast_end = et.forecast_end
        db_t.early_start = et.early_start
        db_t.early_finish = et.early_finish
        db_t.late_start = et.late_start
        db_t.late_finish = et.late_finish
        db_t.total_float = et.total_float
        db_t.is_critical = et.is_critical
        db_t.delay_days = et.delay_days

    # Update project
    project.forecast_end = project_forecast_end
    if project.baseline_end and project.forecast_end:
        project.delay_days = (project.forecast_end - project.baseline_end).days
    else:
        project.delay_days = 0

    # Project health calculation
    # Open high/critical issues
    open_critical_issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status == "OPEN",
        Issue.severity.in_(["HIGH", "CRITICAL"])
    ).count()
    
    # Are any critical tasks blocked?
    critical_task_ids = [t.id for t in engine_tasks if t.is_critical]
    blocked_critical_tasks = db.query(Task).filter(
        Task.id.in_(critical_task_ids),
        Task.status == "BLOCKED"
    ).count()
    
    any_task_delayed = any(t.is_delayed for t in engine_tasks)
    
    if project.delay_days >= 3 or blocked_critical_tasks > 0:
        project.health = "RED"
    elif project.delay_days > 0 or any_task_delayed or open_critical_issues > 0:
        project.health = "AMBER"
    else:
        project.health = "GREEN"

    # Generate Alerts
    generate_alerts(db, project_id, project, engine_tasks)
    
    db.commit()

def generate_alerts(db: Session, project_id: int, project: Project, engine_tasks: list[EngineTask]):
    # Get active alerts to deduplicate
    active_alerts = db.query(Alert).filter(Alert.project_id == project_id, Alert.status == "ACTIVE").all()
    alert_map = {(a.type, a.task_id): a for a in active_alerts}

    # PROJECT_DELAY
    if project.delay_days > 0:
        sev = "CRITICAL" if project.delay_days >= 3 else "WARNING"
        msg = f"Project delayed: forecast completion moved by {project.delay_days} days."
        if ("PROJECT_DELAY", None) in alert_map:
            alert_map[("PROJECT_DELAY", None)].message = msg
            alert_map[("PROJECT_DELAY", None)].severity = sev
        else:
            db.add(Alert(project_id=project_id, type="PROJECT_DELAY", severity=sev, message=msg))
    else:
        if ("PROJECT_DELAY", None) in alert_map:
            alert_map[("PROJECT_DELAY", None)].status = "RESOLVED"

    # TASK_DELAYED
    for t in engine_tasks:
        if t.is_delayed:
            sev = "CRITICAL" if t.is_critical else "WARNING"
            msg = f"Task is delayed by {t.delay_days} days."
            if not t.is_critical:
                msg += " (Absorbed by float)"
            
            if ("TASK_DELAYED", t.id) in alert_map:
                alert_map[("TASK_DELAYED", t.id)].message = msg
                alert_map[("TASK_DELAYED", t.id)].severity = sev
            else:
                db.add(Alert(project_id=project_id, task_id=t.id, type="TASK_DELAYED", severity=sev, message=msg))
        else:
            if ("TASK_DELAYED", t.id) in alert_map:
                alert_map[("TASK_DELAYED", t.id)].status = "RESOLVED"
                
    # TASK_BLOCKED
    for t in engine_tasks:
        if t.status == "BLOCKED":
            sev = "CRITICAL" if t.is_critical else "WARNING"
            msg = "Task is blocked."
            if ("TASK_BLOCKED", t.id) in alert_map:
                alert_map[("TASK_BLOCKED", t.id)].severity = sev
            else:
                db.add(Alert(project_id=project_id, task_id=t.id, type="TASK_BLOCKED", severity=sev, message=msg))
        else:
            if ("TASK_BLOCKED", t.id) in alert_map:
                alert_map[("TASK_BLOCKED", t.id)].status = "RESOLVED"
