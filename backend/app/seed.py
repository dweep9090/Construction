import argparse
from datetime import datetime, timedelta, date, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.users import User
from app.models.projects import Project
from app.models.tasks import Task, TaskDependency, TaskProgress
from app.models.issues import Issue
from app.models.alerts import Alert
from app.auth.security import get_password_hash

def clear_db(db: Session):
    from app.models.workflow import ChangeRequest, AuditLog
    from app.models.projects import ProjectMember
    db.query(AuditLog).delete()
    db.query(ChangeRequest).delete()
    db.query(Alert).delete()
    db.query(Issue).delete()
    db.query(TaskProgress).delete()
    db.query(TaskDependency).delete()
    db.query(Task).delete()
    db.query(ProjectMember).delete()
    db.query(Project).delete()
    db.query(User).delete()
    db.commit()

def seed(scenario: str, reset: bool):
    db = SessionLocal()
    try:
        if reset:
            clear_db(db)
            print("Database reset.")
        
        # Check if users exist
        if not db.query(User).first():
            director = User(name="Project Director", email="director@demo.com", password_hash=get_password_hash("demo1234"), role="PROJECT_DIRECTOR")
            pm = User(name="Project Manager", email="pm@demo.com", password_hash=get_password_hash("demo1234"), role="PROJECT_MANAGER")
            se = User(name="Site Engineer", email="se@demo.com", password_hash=get_password_hash("demo1234"), role="SITE_ENGINEER")
            qi = User(name="Quality Inspector", email="qi@demo.com", password_hash=get_password_hash("demo1234"), role="QUALITY_INSPECTOR")
            contractor = User(name="Contractor", email="contractor@demo.com", password_hash=get_password_hash("demo1234"), role="CONTRACTOR")
            store = User(name="Store Keeper", email="store@demo.com", password_hash=get_password_hash("demo1234"), role="STORE_KEEPER")
            finance = User(name="Finance Officer", email="finance@demo.com", password_hash=get_password_hash("demo1234"), role="FINANCE_OFFICER")
            auditor = User(name="Auditor", email="auditor@demo.com", password_hash=get_password_hash("demo1234"), role="AUDITOR")
            
            db.add_all([director, pm, se, qi, contractor, store, finance, auditor])
            db.commit()
            print("Users seeded.")
        
        pm = db.query(User).filter_by(email="pm@demo.com").first()
        se = db.query(User).filter_by(email="se@demo.com").first()
        contractor = db.query(User).filter_by(email="contractor@demo.com").first()
        
        if db.query(Project).filter_by(name="Riverfront Bridge Construction").first():
            print("Demo project already exists.")
            return

        today = date.today()
        project_start = today - timedelta(days=15)
        
        project = Project(
            name="Riverfront Bridge Construction",
            description="Construction of Riverfront Bridge",
            location="Ahmedabad, Gujarat",
            start_date=project_start,
            created_by=pm.id,
            status="ACTIVE",
            budget="₹45 crore",
            is_public=1,
            baseline_status="APPROVED"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print("Project seeded.")
        
        from app.models.projects import ProjectMember
        for user in db.query(User).all():
            if user.role not in ["PROJECT_DIRECTOR", "AUDITOR"]:
                db.add(ProjectMember(project_id=project.id, user_id=user.id, role=user.role))
        db.commit()
        print("Project members seeded.")

        # WBS tasks
        g1 = Task(project_id=project.id, name="Site Preparation", is_summary=True)
        g2 = Task(project_id=project.id, name="Structure", is_summary=True)
        g3 = Task(project_id=project.id, name="MEP & Finishing", is_summary=True)
        db.add_all([g1, g2, g3])
        db.commit()

        tasks_data = [
            # id_temp, parent, name, duration, start_offset, assignee
            (1, g1, "Site Survey & Mobilisation", 5, 0, se),
            (2, g1, "Excavation", 6, 5, se),
            (3, g1, "Steel Procurement", 12, 0, contractor),
            (4, g1, "Drainage Works", 8, 11, contractor),
            (5, g2, "Foundation", 10, 11, se),
            (6, g2, "Columns", 8, 21, se),
            (7, g2, "Beams", 7, 29, contractor),
            (8, g2, "Slab", 9, 36, contractor),
            (9, g3, "Electrical Rough-in", 7, 45, contractor),
            (10, g3, "Plumbing", 5, 45, se),
            (11, g3, "Finishing", 10, 52, se),
        ]
        
        task_objs = {}
        for temp_id, parent, name, duration, offset, assignee in tasks_data:
            p_start = project_start + timedelta(days=offset)
            p_end = p_start + timedelta(days=duration)
            t = Task(
                project_id=project.id,
                parent_id=parent.id,
                name=name,
                duration=duration,
                planned_start=p_start,
                planned_end=p_end,
                assignee_id=assignee.id,
                status="NOT_STARTED"
            )
            db.add(t)
            task_objs[temp_id] = t
        
        db.commit()
        for t in task_objs.values():
            db.refresh(t)

        deps = [
            (2, 1), # Exc -> Survey
            (4, 2), # Drain -> Exc
            (5, 2), # Found -> Exc
            (6, 5), (6, 3), # Col -> Found, Steel
            (7, 6), # Beams -> Col
            (8, 7), # Slab -> Beams
            (9, 8), # Elec -> Slab
            (10, 8), # Plumb -> Slab
            (11, 9), (11, 10), (11, 4) # Fin -> Elec, Plumb, Drain
        ]

        for succ_temp, pred_temp in deps:
            td = TaskDependency(
                predecessor_task_id=task_objs[pred_temp].id,
                successor_task_id=task_objs[succ_temp].id,
                lag_days=0
            )
            db.add(td)
        
        db.commit()
        print("Tasks and dependencies seeded.")

        # Set baseline scenario data
        # Site Survey
        task_objs[1].status = "COMPLETED"
        task_objs[1].progress = 100
        task_objs[1].actual_start = task_objs[1].planned_start
        task_objs[1].actual_end = task_objs[1].planned_end

        # Excavation
        task_objs[2].status = "COMPLETED"
        task_objs[2].progress = 100
        task_objs[2].actual_start = task_objs[2].planned_start
        task_objs[2].actual_end = task_objs[2].planned_end

        # Steel Procurement
        task_objs[3].status = "COMPLETED"
        task_objs[3].progress = 100
        task_objs[3].actual_start = task_objs[3].planned_start
        task_objs[3].actual_end = task_objs[3].planned_end

        # Drainage
        task_objs[4].status = "IN_PROGRESS"
        task_objs[4].progress = 50
        task_objs[4].actual_start = task_objs[4].planned_start

        # Foundation
        if scenario == "delayed":
            task_objs[5].status = "COMPLETED"
            task_objs[5].progress = 100
            task_objs[5].actual_start = task_objs[5].planned_start
            task_objs[5].actual_end = task_objs[5].planned_end + timedelta(days=4)
        else:
            task_objs[5].status = "IN_PROGRESS"
            task_objs[5].progress = 40
            task_objs[5].actual_start = task_objs[5].planned_start

        db.commit()
        print(f"Scenario '{scenario}' data seeded.")
        
        # Add a couple of issues
        i1 = Issue(project_id=project.id, title="Crane availability next week", severity="LOW", reported_by=se.id)
        i2 = Issue(project_id=project.id, task_id=task_objs[5].id, title="Minor water seepage in pit", severity="MEDIUM", reported_by=contractor.id)
        db.add_all([i1, i2])
        db.commit()

        from app.scheduling.service import recalculate_project
        recalculate_project(db, project.id, today)
        print("Project recalculated. Forecast dates, health and alerts generated.")
        
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["baseline", "delayed"], default="baseline")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    seed(args.scenario, args.reset)
