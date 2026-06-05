from core.database import SessionLocal
from models.user import User

db = SessionLocal()
users = db.query(User).all()
print(f"Total: {len(users)}")
for u in users:
    print(f"  {u.email}")
db.close()
