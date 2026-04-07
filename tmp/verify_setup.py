
import sys
import os

# Set PYTHONPATH to the current directory
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

try:
    from app import app, db, User, init_database
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def verify():
    with app.app_context():
        # Clear DB first to ensure a clean run of init_database
        # (Be careful in production, but here it's fine)
        db.drop_all()
        init_database()
        
        # 1. Check if AD001 exists
        admin = User.query.filter_by(readable_id='AD001').first()
        if admin:
            print(f"✅ Admin AD001 found: {admin.full_name} ({admin.email})")
            
            # 2. Check password verification
            if admin.check_password('admin123'):
                print("✅ Password verification successful")
            else:
                print("❌ Password verification failed")
                
            # 3. Check role
            print(f"✅ Role: {admin.role}")
            
        else:
            print("❌ Admin AD001 not found")

if __name__ == "__main__":
    verify()
