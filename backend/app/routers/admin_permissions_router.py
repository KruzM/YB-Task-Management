from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.permissions import RoleCreate, RoleOut, PermissionBase, PermissionOut
from backend.app.models import Role, Permission, RolePermission
from backend.app.utils.permissions import require_permission
from backend.app.utils.security import get_current_user

router = APIRouter()  # no prefix here — main.py will attach prefix="/admin"

# Protected endpoints use the require_permission dependency
@router.post("/roles", response_model=RoleOut, dependencies=[Depends(require_permission("roles.manage"))])
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    new_role = Role(name=role.name)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    for perm_id in role.permissions:
        db.add(RolePermission(role_id=new_role.id, permission_id=perm_id))

    db.commit()
    db.refresh(new_role)
    return new_role


@router.get("/roles", response_model=list[RoleOut])
def get_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()


@router.post("/permissions", response_model=PermissionOut, dependencies=[Depends(require_permission("roles.manage"))])
def create_permission(permission: PermissionBase, db: Session = Depends(get_db)):
    p = Permission(name=permission.name, description=permission.description)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/debug/me")
def debug_me(user = Depends(get_current_user)):
    # safe debug output; role may be None
    role = user.role
    return {
        "id": user.id,
        "email": user.email,
        "role_id": getattr(user, "role_id", None),
        "role_name": role.name if role else None,
        "role_permissions": [rp.permission_id for rp in (role.permissions or [])] if role else []
    }
