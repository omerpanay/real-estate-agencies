"""
Bootstrap script to initialize database and create demo tenant/user.
"""
import asyncio
import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.models.tenant import Tenant, User
from app.core.security import hash_password
import uuid


async def create_test_data():
    print("=" * 50)
    print("Multi-Tenant CRM - Database Bootstrap")
    print("=" * 50)
    
    print("\n1. Initializing database tables...")
    try:
        await init_db()
        print("   ✅ Database tables created/verified.")
    except Exception as e:
        print(f"   ❌ Error initializing DB: {e}")
        return

    async with AsyncSessionLocal() as db:
        # Check if demo tenant already exists
        print("\n2. Checking for existing demo tenant...")
        result = await db.execute(
            select(Tenant).where(Tenant.slug == "demo-company")
        )
        existing_tenant = result.scalar_one_or_none()
        
        if existing_tenant:
            print(f"   ℹ️  Demo tenant already exists: {existing_tenant.name} (ID: {existing_tenant.id})")
            tenant = existing_tenant
        else:
            print("   Creating new demo tenant...")
            tenant = Tenant(
                id=uuid.uuid4(),
                name="Demo Company",
                slug="demo-company",
                is_active=True
            )
            try:
                db.add(tenant)
                await db.commit()
                await db.refresh(tenant)
                print(f"   ✅ Demo Tenant Created: {tenant.name} (ID: {tenant.id})")
            except Exception as e:
                print(f"   ❌ Tenant creation failed: {e}")
                await db.rollback()
                return

        # Check if admin user already exists
        print("\n3. Checking for existing admin user...")
        result = await db.execute(
            select(User).where(
                User.email == "admin@demo.com",
                User.tenant_id == tenant.id
            )
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"   ℹ️  Admin user already exists: {existing_user.email}")
        else:
            print("   Creating admin user...")
            user = User(
                id=uuid.uuid4(),
                email="admin@demo.com",
                hashed_password=hash_password("password123"),
                full_name="Admin User",
                is_active=True,
                tenant_id=tenant.id
            )
            try:
                db.add(user)
                await db.commit()
                print("   ✅ Admin User Created!")
            except Exception as e:
                print(f"   ❌ User creation failed: {e}")
                await db.rollback()
                return

    print("\n" + "=" * 50)
    print("Bootstrap Complete!")
    print("=" * 50)
    print("\nLogin credentials:")
    print("   Email:    admin@demo.com")
    print("   Password: password123")
    print("\nStart the server with:")
    print("   .\\venv\\Scripts\\uvicorn app.main:app --reload")
    print("\nThen visit: http://localhost:8000/docs")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(create_test_data())
