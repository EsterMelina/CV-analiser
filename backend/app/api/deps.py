"""
Dependências reutilizáveis pelos routers: obter utilizador autenticado
e restringir acesso por papel (admin / recruiter).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.models.company import Company

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def validate_company(user: User, db: Session):
    if user.role == UserRole.RECRUITER or user.company_id is not None:
        company = db.get(Company, user.company_id) if user.company_id else None
        if company is None or not company.is_active:
            raise HTTPException(status_code=403, detail="É necessária uma empresa activa associada à conta")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user = db.get(User, int(user_id))
    except (ValueError, TypeError):
        raise credentials_exception
    if user is None or not user.is_active:
        raise credentials_exception
    validate_company(user, db)
    return user


def require_roles(*allowed_roles: UserRole):
    """Fábrica de dependências para restringir um endpoint a papéis específicos."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Não tem permissão para aceder a este recurso",
            )
        return current_user

    return dependency


require_admin = require_roles(UserRole.ADMIN)
require_recruiter = require_roles(UserRole.RECRUITER, UserRole.ADMIN)
