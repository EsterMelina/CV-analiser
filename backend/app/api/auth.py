from datetime import datetime, timezone
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.models.refresh_session import RefreshSession
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserRead
from app.api.deps import get_current_user, validate_company

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


def issue_tokens(db: Session, user: User):
    refresh = create_refresh_token(subject=str(user.id))
    data = decode_token(refresh)
    db.add(RefreshSession(token_hash=hashlib.sha256(refresh.encode()).hexdigest(),
        user_id=user.id, company_id=user.company_id,
        expires_at=datetime.fromtimestamp(data["exp"], timezone.utc)))
    db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id), {"role": user.role.value}),
                         refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou palavra-passe inválidos")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada")
    validate_company(user, db)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data is None or data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()
    session = db.get(RefreshSession, token_hash)
    if session is None or session.revoked:
        raise HTTPException(status_code=401, detail="Sessão expirada ou revogada")
    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilizador inválido")
    validate_company(user, db)
    if session.company_id != user.company_id:
        raise HTTPException(status_code=401, detail="Empresa alterada; inicie nova sessão")
    changed = db.query(RefreshSession).filter(RefreshSession.token_hash == token_hash,
        RefreshSession.revoked.is_(False)).update({"revoked": True}, synchronize_session=False)
    if changed != 1:
        db.rollback()
        raise HTTPException(status_code=401, detail="Sessão já renovada")
    return issue_tokens(db, user)


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()
    db.query(RefreshSession).filter(RefreshSession.token_hash == token_hash).update({"revoked": True})
    db.commit()
    return {"detail": "Sessão terminada"}


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
