from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserRead
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou palavra-passe inválidos")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    extra = {"role": user.role.value}
    return TokenResponse(
        access_token=create_access_token(subject=str(user.id), extra_claims=extra),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data is None or data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    user = db.get(User, int(data["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilizador inválido")

    extra = {"role": user.role.value}
    return TokenResponse(
        access_token=create_access_token(subject=str(user.id), extra_claims=extra),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


@router.post("/logout")
def logout():
    # Com JWT stateless, o "logout" é tratado no cliente (descartar tokens).
    # Numa evolução futura, manter uma blacklist/allowlist de refresh tokens em BD ou Redis.
    return {"detail": "Sessão terminada. Descarte os tokens no cliente."}


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
