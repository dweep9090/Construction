from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(title="Construction Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.auth.router import router as auth_router
from app.tasks.router import router as tasks_router
from app.projects.router import router as projects_router
from app.dashboard.router import router as dashboard_router
from app.issues.router import router as issues_router
from app.alerts.router import router as alerts_router
from app.workflow.router import router as workflow_router

app.include_router(auth_router, prefix="/api")
app.include_router(tasks_router)
app.include_router(projects_router)
app.include_router(dashboard_router)
app.include_router(issues_router)
app.include_router(alerts_router)
app.include_router(workflow_router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "db": "ok"} # For now, simple health check
