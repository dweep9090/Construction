from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.router import get_current_user
from app.models.users import User
from app.models.projects import ProjectMember

def get_current_user_project_role(project_id: int, db: Session, user: User):
    if user.role == "AUDITOR":
        return "AUDITOR"
        
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id
    ).first()
    
    return member.role if member else None

class RequireProjectRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        role = get_current_user_project_role(project_id, db, current_user)
        
        if not role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this project")
            
        if role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{role}' is not authorized to perform this action")
            
        return role
