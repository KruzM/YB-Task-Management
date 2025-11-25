
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import User, Role, Permission, RolePermission
from backend.app.utils.security import hash_password


DEFAULT_PERMISSIONS = [
    ("manage_users", "Can manage users"),
    ("manage_roles", "Can manage roles"),
    ("manage_permissions", "Can manage permissions"),
    ("manage_tasks", "Can manage all tasks"),
    ("manage_clients", "Can manage clients"),
    ("view_audit_logs", "Can view audit logs"),
    ("manage_documents", "Can manage documents"),
    ("view_reports", "Can view reports"),
]


ADMIN_EMAIL = "kruz@yecnybooks.com"
ADMIN_PASSWORD = "YecnyBKruz2025"


def seed_data():
    db: Session = SessionLocal()

    print("🔄 Running startup seed...")

    # -----------------------------
    # 1️⃣ Ensure permissions exist
    # -----------------------------
    permission_objects = {}
    for name, desc in DEFAULT_PERMISSIONS:
        perm = db.query(Permission).filter_by(name=name).first()
        if not perm:
            perm = Permission(name=name, description=desc)
            db.add(perm)
            db.commit()
            db.refresh(perm)
        permission_objects[name] = perm

    # -----------------------------
    # 2️⃣ Ensure Admin role exists
    # -----------------------------
    admin_role = db.query(Role).filter_by(name="Admin").first()
    if not admin_role:
        admin_role = Role(name="Admin")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)

    # -----------------------------
    # 3️⃣ Assign ALL permissions to Admin
    # -----------------------------
    existing_links = {
        (rp.role_id, rp.permission_id)
        for rp in db.query(RolePermission).all()
    }

    for perm in permission_objects.values():
        link_key = (admin_role.id, perm.id)
        if link_key not in existing_links:
            link = RolePermission(role_id=admin_role.id, permission_id=perm.id)
            db.add(link)

    db.commit()

    # -----------------------------
    # 4️⃣ Ensure admin user exists
    # -----------------------------
    admin_user = db.query(User).filter_by(email=ADMIN_EMAIL).first()

    if not admin_user:
        admin_user = User(
            email=ADMIN_EMAIL,
            full_name="System Administrator",
            hashed_password=hash_password(ADMIN_PASSWORD),
            is_active=True,
            role_id=admin_role.id,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    else:
        # Ensure admin has admin role
        if admin_user.role_id != admin_role.id:
            admin_user.role_id = admin_role.id
            db.commit()

    print("✅ Startup seed completed.\n")