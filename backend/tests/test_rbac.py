import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.users import User
from app.models.projects import Project, ProjectMember
from app.models.tasks import Task
from app.auth.security import create_access_token, get_password_hash

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Create users
    pm1 = User(name="PM 1", email="pm1@test.com", password_hash=get_password_hash("test"), role="PROJECT_MANAGER")
    pm2 = User(name="PM 2", email="pm2@test.com", password_hash=get_password_hash("test"), role="PROJECT_MANAGER")
    director = User(name="Director", email="director@test.com", password_hash=get_password_hash("test"), role="PROJECT_DIRECTOR")
    se1 = User(name="SE 1", email="se1@test.com", password_hash=get_password_hash("test"), role="SITE_ENGINEER")
    
    db.add_all([pm1, pm2, director, se1])
    db.commit()
    
    # Create projects
    p1 = Project(name="Project A", status="ACTIVE", created_by=pm1.id)
    p2 = Project(name="Project B", status="ACTIVE", created_by=pm2.id)
    db.add_all([p1, p2])
    db.commit()
    
    # Assign members (pm1 -> p1, pm2 -> p2, se1 -> p1)
    db.add(ProjectMember(project_id=p1.id, user_id=pm1.id, role="PROJECT_MANAGER"))
    db.add(ProjectMember(project_id=p1.id, user_id=se1.id, role="SITE_ENGINEER"))
    db.add(ProjectMember(project_id=p2.id, user_id=pm2.id, role="PROJECT_MANAGER"))
    db.commit()
    
    # Create task
    t1 = Task(project_id=p1.id, name="Task 1", duration=1, status="NOT_STARTED")
    db.add(t1)
    db.commit()
    
    yield
    
    Base.metadata.drop_all(bind=engine)

def get_token(user_id, email, role):
    return create_access_token({"sub": str(user_id), "email": email, "role": role})

def test_pm1_can_access_project_a():
    token = get_token(1, "pm1@test.com", "PROJECT_MANAGER")
    res = client.get("/api/projects/1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_pm1_cannot_access_project_b():
    token = get_token(1, "pm1@test.com", "PROJECT_MANAGER")
    res = client.get("/api/projects/2/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_director_can_access_any_project():
    token = get_token(3, "director@test.com", "PROJECT_DIRECTOR")
    res1 = client.get("/api/projects/1/dashboard", headers={"Authorization": f"Bearer {token}"})
    res2 = client.get("/api/projects/2/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200
    assert res2.status_code == 200

def test_site_engineer_cannot_generate_ai():
    token = get_token(4, "se1@test.com", "SITE_ENGINEER")
    res = client.post("/api/projects/1/ai-summary", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_pm_can_generate_ai():
    token = get_token(1, "pm1@test.com", "PROJECT_MANAGER")
    # Should get 501 (not configured) or 503 (unavailable) but NOT 403
    res = client.post("/api/projects/1/ai-summary", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code in [501, 503]
