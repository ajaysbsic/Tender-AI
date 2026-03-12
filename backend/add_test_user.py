"""
Add test user to database
Email: ajay.kumar@alfanar.com
Password: Ajay123#
"""
from app.core.database import SessionLocal
from app.models.tables import User
import bcrypt
import uuid

def add_test_user():
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "ajay.kumar@alfanar.com").first()
        if existing_user:
            print("✅ Test user already exists!")
            print(f"   Email: ajay.kumar@alfanar.com")
            print(f"   Password: Ajay123#")
            return
        
        # Create new user using bcrypt directly
        password_bytes = "Ajay123#".encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        new_user = User(
            id=uuid.uuid4(),
            email="ajay.kumar@alfanar.com",
            password_hash=hashed_password
        )
        db.add(new_user)
        db.commit()
        print("✅ Test user created successfully!")
        print(f"   Email: ajay.kumar@alfanar.com")
        print(f"   Password: Ajay123#")
        print("\n📝 You can now login with these credentials at http://localhost:60880")
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_user()
