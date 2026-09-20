from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.projects import Project
from app.models.tasks import Task
from app.models.issues import Issue
from app.models.alerts import Alert
from app.projects.router import get_schedule
from app.auth.router import get_current_user
from app.auth.dependencies import get_current_user_project_role
from app.models.users import User
from app.core.config import settings
from pydantic import BaseModel
import json
import logging
from app.audit.service import record_audit

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])

@router.get("/api/projects/{project_id}/dashboard")
def get_dashboard(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if not role and current_user.role not in ["PROJECT_DIRECTOR", "AUDITOR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_summary == False).all()
    issues = db.query(Issue).filter(Issue.project_id == project_id).all()
    alerts = db.query(Alert).filter(Alert.project_id == project_id, Alert.status == "ACTIVE").all()

    total_tasks = len(tasks)
    completed = sum(1 for t in tasks if t.status == "COMPLETED")
    in_progress = sum(1 for t in tasks if t.status == "IN_PROGRESS")
    blocked = sum(1 for t in tasks if t.status == "BLOCKED")
    not_started = sum(1 for t in tasks if t.status in ["NOT_STARTED", "ASSIGNED"])
    
    # Calculate overall progress as simple average
    overall_progress = sum(t.progress for t in tasks) / total_tasks if total_tasks > 0 else 0

    open_issues = [i for i in issues if i.status == "OPEN"]
    high_issues = sum(1 for i in open_issues if i.severity == "HIGH")
    critical_issues = sum(1 for i in open_issues if i.severity == "CRITICAL")

    # Get schedule data
    schedule_data = get_schedule(project_id, db, current_user)

    return {
        "project": {
            "id": project.id,
            "name": project.name
        },
        "progress": {
            "overall": round(overall_progress, 1),
            "completed": completed,
            "in_progress": in_progress,
            "blocked": blocked,
            "not_started": not_started
        },
        "schedule": {
            "planned_completion": project.baseline_end,
            "forecast_completion": project.forecast_end,
            "delay_days": project.delay_days
        },
        "health": {
            "status": project.health,
            "reason": "" # Could extract from alerts
        },
        "critical_path": schedule_data["critical_path"],
        "issues": {
            "open": len(open_issues),
            "high": high_issues,
            "critical": critical_issues
        },
        "alerts": [
            {
                "id": a.id,
                "type": a.type,
                "severity": a.severity,
                "message": a.message
            } for a in alerts
        ]
    }

class AIAnalysisResponse(BaseModel):
    summary: str
    risks: list[str]
    impact: str
    recommended_attention: list[str]

@router.post("/api/projects/{project_id}/ai-summary", response_model=AIAnalysisResponse)
def generate_ai_summary(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = get_current_user_project_role(project_id, db, current_user)
    if role not in ["PROJECT_MANAGER", "PROJECT_DIRECTOR", "AUDITOR"] and current_user.role != "PROJECT_DIRECTOR":
        raise HTTPException(status_code=403, detail="Not authorized to run AI analysis")
        
    import os
    from dotenv import load_dotenv
    load_dotenv() # Force load .env from current directory just in case
    
    provider = settings.AI_PROVIDER or os.getenv("AI_PROVIDER") or "huggingface"
    hf_token = settings.HF_TOKEN or os.getenv("HF_TOKEN")
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    ai_model = settings.AI_MODEL or os.getenv("AI_MODEL") or "openai/gpt-oss-120b:fastest"
    
    if provider == "huggingface":
        if not hf_token:
            raise HTTPException(status_code=501, detail="AI Analysis is not configured (missing HF token).")
        if not openai:
            raise HTTPException(status_code=501, detail="OpenAI SDK not installed.")
    else:
        if not api_key:
            raise HTTPException(status_code=501, detail="AI Analysis is not configured (missing API key).")
        if not genai:
            raise HTTPException(status_code=501, detail="AI SDK not installed.")

    # Get the current state
    dashboard_data = get_dashboard(project_id, db, current_user)
    
    # Get delayed tasks explicitly to add to context
    tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_summary == False).all()
    delayed_tasks = []
    for t in tasks:
        if t.delay_days > 0:
            delayed_tasks.append({
                "name": t.name,
                "delay_days": t.delay_days,
                "is_critical": t.name in dashboard_data["critical_path"]
            })
            
    # Figure out affected downstream tasks roughly based on what's incomplete
    affected_tasks = [t.name for t in tasks if t.status not in ["COMPLETED"] and t.name != "Foundation"] # Simple mock logic or just list incomplete

    context = {
        "project": dashboard_data["project"],
        "health": dashboard_data["health"],
        "schedule": dashboard_data["schedule"],
        "progress": dashboard_data["progress"]["overall"],
        "critical_path": dashboard_data["critical_path"],
        "delayed_tasks": delayed_tasks,
        "affected_tasks": [t.name for t in tasks if t.status not in ["COMPLETED"] and t.delay_days == 0],
        "open_issues": dashboard_data["issues"]["open"],
        "alerts": [a["message"] for a in dashboard_data["alerts"]]
    }

    system_instruction = """
You are a construction project monitoring assistant.

Analyze ONLY the project information provided in the context.

Do not invent:
- dates
- delays
- tasks
- dependencies
- causes
- project statistics

Do not recalculate the critical path.

Do not claim that an event caused a delay unless the supplied
project data explicitly establishes that relationship.

If information is unavailable, state that it is unavailable.

Clearly distinguish observed project data from recommendations.

Keep the response concise and suitable for a project manager.
"""

    record_audit(db, project_id, "GENERATE", "AISummary", project_id, user=current_user, role=role)

    try:
        if provider == "huggingface":
            client = openai.OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=hf_token
            )
            
            schema = AIAnalysisResponse.model_json_schema()
            schema["additionalProperties"] = False
            
            # Using JSON schema for OpenAI compatible
            response = client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": json.dumps(context, default=str)}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "analysis_response",
                        "strict": True,
                        "schema": schema
                    }
                },
                temperature=0.2,
            )
            result = json.loads(response.choices[0].message.content)
            
            # Validate through pydantic
            validated = AIAnalysisResponse(**result)
            return validated

        else:
            client = genai.Client(api_key=api_key)
            
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash",
                contents=json.dumps(context, default=str),
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=AIAnalysisResponse,
                    temperature=0.2,
                ),
            )
            
            result = json.loads(response.text)
            return AIAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"AI Generation failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"AI Service is currently unavailable. Error: {str(e)}")
