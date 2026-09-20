import json
from app.core.database import SessionLocal
from app.dashboard.router import generate_ai_summary
from app.models.users import User

db = SessionLocal()
user = User()
try:
    generate_ai_summary(1, db, user)
except Exception as e:
    import traceback
    traceback.print_exc()
