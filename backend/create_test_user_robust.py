
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.database import SessionLocal
from models.user import User
from utils.encryption import get_encryption

def create_test_user():
    db = SessionLocal()
    try:
        email = "test@example.com"
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User {email} already exists. Deleting...")
            db.delete(existing_user)
            db.commit()
            print("Deleted existing user.")

        # Create new user
        encryption = get_encryption()
        
        # Valid dummy tokens
        access_token_raw = "test_access_token_" + datetime.utcnow().isoformat()
        refresh_token_raw = "test_refresh_token_" + datetime.utcnow().isoformat()
        
        test_user = User(
            email=email,
            first_name="Test",
            last_name="User",
            role="admin",
            is_active=True,
            access_token=encryption.encrypt(access_token_raw),
            refresh_token=encryption.encrypt(refresh_token_raw),
            token_expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ Test user created!")
        print(f"📋 User ID: {test_user.id}")
        print(f"📧 Email: {test_user.email}")
        print(f"")
        print(f"🔑 Use this as your Auth Token in Streamlit: {test_user.id}")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
