from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.database import get_db
from backend.app.schemas.permissions import RoleCreate, RoleOut, PermissionBase, PermissionOut, PermissionCreate, PermissionRead
from backend.app.models import Role, Permission, RolePermission, User
from backend.app.utils.permissions import require_permission
from backend.app.utils.security import get_current_user
from backend.app.schemas.roles import RoleCreate, RoleOut, RoleUpdate
from typing import List, Dict
from backend.app.crud_utils.audit import log_permission_action

router = APIRouter()  # no prefix here — main.py will attach prefix="/admin"

# Protected endpoints use the require_permission dependency
@router.post("/roles", response_model=RoleOut, tags=["Admin Permissions"])
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_roles")),
):
    # Allow first-time bootstrap (no roles exist)
    role_count = db.query(Role).count()
    if role_count > 0 and current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Admin only")

    new_role = Role(name=role.name)
    db.add(new_role)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Role name already exists")

    db.refresh(new_role)

    # Attach permissions (if provided)
    for perm_id in role.permissions:
        rp = RolePermission(role_id=new_role.id, permission_id=perm_id)
        db.add(rp)

    db.commit()
    db.refresh(new_role)

    # Return role (SQLAlchemy model) — response_model will convert via ORM mode
    return new_role

@router.get("/roles", response_model=List[RoleOut], tags=["Admin Permissions"])
def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_roles"))
):
    roles = db.query(Role).all()

    output = []
    for role in roles:
        permission_objects = [
            PermissionOut(
                id=rp.permission.id,
                name=rp.permission.name,
                description=rp.permission.description
            )
            for rp in role.permissions
        ]

        output.append(
            RoleOut(
                id=role.id,
                name=role.name,
                permissions=permission_objects
            )
        )

    return output
@router.post("/permissions", tags=["Admin Permissions"])
def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_roles")),
):
    role_count = db.query(Role).count()
    existing = db.query(Permission).filter(Permission.name == permission.name).first()
    if existing:
        raise HTTPException(
        status_code=400,
        detail=f"Permission '{permission.name}' already exists."
    )
    # Allow bootstrap (first permission creation)
    if role_count > 0 and current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Admin only")

    db_permission = Permission(
        name=permission.name,
        description=permission.description
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    
    # Log permission creation (only if user exists and has ID)
    if current_user and hasattr(current_user, 'id'):
        log_permission_action(
            db=db,
            action="permission_created",
            entity_id=db_permission.id,
            performed_by=current_user.id,
            details={"permission_name": db_permission.name, "description": db_permission.description},
        )
    
    return db_permission

@router.get("/permissions", response_model=List[PermissionRead])
def get_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_roles"))
):
   
    role_count = db.query(Role).count()

    # Allow bootstrap
    if role_count > 0:
        require_permission("manage_roles")(current_user, db)

    return db.query(Permission).all()

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

@router.patch("/roles/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    updates: RoleUpdate,
    current_user: User = Depends(require_permission("manage_roles")),
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(404, "Role not found")

    # Update name
    if updates.name:
        exists = db.query(Role).filter(Role.name == updates.name).first()
        if exists:
            raise HTTPException(400, "A role with this name already exists")
        role.name = updates.name

    # Add permissions
    if updates.add_permissions:
        for perm_id in updates.add_permissions:
            exists = db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm_id
            ).first()
            if not exists:
                db.add(RolePermission(role_id=role.id, permission_id=perm_id))

    # Remove permissions
    if updates.remove_permissions:
        db.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id.in_(updates.remove_permissions)
        ).delete(synchronize_session=False)

    db.commit()
    db.refresh(role)

    # Log role update
    log_permission_action(
        db=db,
        action="role_updated",
        entity_id=role.id,
        performed_by=current_user.id,
        details={
            "role_name": role.name if updates.name else None,
            "added_permissions": updates.add_permissions,
            "removed_permissions": updates.remove_permissions,
        },
    )
    
    permission_objects = [
        PermissionOut(
            id=rp.permission.id,
            name=rp.permission.name,
            description=rp.permission.description
        )
        for rp in role.permissions
    ]

    return RoleOut(
        id=role.id,
        name=role.name,
        permissions=permission_objects
    )

@router.patch("/users/{user_id}/role", response_model=Dict)
def set_user_role(
    user_id: int,
    payload: Dict,   # e.g. { "role_id": 2 }
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # very small guard: require admin (or replace with require_permission)
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    role_id = payload.get("role_id")
    if role_id is None:
        raise HTTPException(status_code=400, detail="role_id required")

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role_id = user.role_id
    user.role_id = role_id
    db.commit()
    db.refresh(user)

    # Log role assignment
    log_permission_action(
        db=db,
        action="user_role_changed",
        entity_id=user.id,
        performed_by=current_user.id,
        details={
            "user_email": user.email,
            "old_role_id": old_role_id,
            "new_role_id": role_id,
            "role_name": role.name,
        },
    )

    return {"id": user.id, "email": user.email, "role_id": user.role_id, "role_name": role.name}
