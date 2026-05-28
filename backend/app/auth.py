from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.config import get_settings

_settings = get_settings()
SECRET_KEY = _settings.jwt_secret_key
ALGORITHM = _settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = _settings.jwt_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return user

def require_creator(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.creator:
        raise HTTPException(status_code=403, detail="Se requiere rol creator")
    return current_user

def require_approver_1(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.approver_1:
        raise HTTPException(status_code=403, detail="Se requiere rol approver_1 (Ángela)")
    return current_user

def require_approver_2(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.approver_2:
        raise HTTPException(status_code=403, detail="Se requiere rol approver_2 (Juan Pablo VP)")
    return current_user

def require_approver_any(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.approver_1, UserRole.approver_2]:
        raise HTTPException(status_code=403, detail="Se requiere rol de aprobador")
    return current_user
