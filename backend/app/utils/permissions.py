from fastapi import Security, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.utils.security import get_current_user
from backend.app.models import Permission
from fastapi.security.api_key import APIKeyHeader
def require_permission(permission_name: str):
    """
    Dependency generator: use as Depends(require_permission("some.permission"))
    """
    def wrapper(user = Security(get_current_user), db: Session = Security(get_db)):
        # Lookup the permission object
        permission = db.query(Permission).filter(Permission.name == permission_name).first()
        if not permission:
            # permission doesn't exist yet — treat as server error so admin can create it
            raise HTTPException(status_code=500, detail="Permission not found")

        # If user has no role, user.role may be None; treat as "no permissions"
        if not getattr(user, "role", None):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

        role_permissions = {rp.permission_id for rp in user.role.permissions or []}

        if permission.id not in role_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

        return True
    return wrapper