import logging
from sqlalchemy.orm import Session
from app.models.workflow import AuditLog
from app.models.users import User

logger = logging.getLogger(__name__)

def record_audit(
    db: Session,
    project_id: int,
    action: str,
    entity: str,
    entity_id: int = None,
    previous_value: str = None,
    new_value: str = None,
    user: User = None,
    role: str = None
):
    try:
        log = AuditLog(
            project_id=project_id,
            user_id=user.id if user else None,
            role=role,
            action=action,
            entity=entity,
            entity_id=entity_id,
            previous_value=str(previous_value) if previous_value is not None else None,
            new_value=str(new_value) if new_value is not None else None
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
        db.rollback()
