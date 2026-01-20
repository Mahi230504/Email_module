from app.database import SessionLocal
from models.user import User

db = SessionLocal()
users = db.query(User).all()

print(f"Total users: {len(users)}")
for user in users:
    print(f"User: {user.email}, ID: {user.id}")

db.close()
