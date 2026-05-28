"""
Router para la gestión de usuarios.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.auth import get_password_hash, get_current_user, require_admin

router = APIRouter(
    prefix="/api/users",
    tags=["Usuarios"]
)


@router.get("/", response_model=List[UserRead])
def list_users(
    role: Optional[UserRole] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Lista todos los usuarios. Solo accesible para administradores."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if not include_inactive:
        query = query.filter(User.is_active == True)
    return query.all()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Crea un nuevo usuario. Solo accesible para administradores."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    user_data = user.model_dump()
    password = user_data.pop("password")
    new_user = User(**user_data)
    new_user.hashed_password = get_password_hash(password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Obtiene un usuario por ID. Requiere autenticación."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return db_user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Actualiza datos de un usuario. Solo accesible para administradores."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    update_data = user_update.model_dump(exclude_unset=True)
    new_password = update_data.pop("new_password", None)
    if new_password:
        db_user.hashed_password = get_password_hash(new_password)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Desactiva un usuario (is_active = False). Solo accesible para administradores."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    if db_user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta"
        )

    db_user.is_active = False
    db.commit()
    return None
