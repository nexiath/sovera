#!/usr/bin/env python3
"""
Script to create a super admin user
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from database.session import engine
from models.user import User, UserRole
from auth.security import get_password_hash

def create_super_admin():
    """Create a super admin user"""
    
    admin_email = "admin@sovera.local"
    admin_password = "admin123"  # Change this in production!
    
    with Session(engine) as session:
        # Check if admin already exists
        existing_admin = session.exec(
            select(User).where(User.email == admin_email)
        ).first()
        
        if existing_admin:
            print(f"Admin user {admin_email} already exists")
            print(f"Current role: {existing_admin.role}")
            
            # Update to super admin if needed
            if existing_admin.role != UserRole.SUPER_ADMIN:
                existing_admin.role = UserRole.SUPER_ADMIN
                session.add(existing_admin)
                session.commit()
                print(f"Updated {admin_email} to SUPER_ADMIN")
            return
        
        # Create new super admin
        hashed_password = get_password_hash(admin_password)
        admin_user = User(
            email=admin_email,
            hashed_password=hashed_password,
            is_active=True,
            role=UserRole.SUPER_ADMIN
        )
        
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        
        print(f"Created super admin user:")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")
        print(f"  Role: {admin_user.role}")
        print(f"  ID: {admin_user.id}")
        print("\n⚠️  IMPORTANT: Change the password after first login!")

if __name__ == "__main__":
    create_super_admin()