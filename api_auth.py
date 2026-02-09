"""
API de Autenticación - Login y gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from typing import Optional

from database import get_db
from models import User, UserRole
from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    require_superuser,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# ==========================================
# Schemas
# ==========================================

class LoginRequest(BaseModel):
    """Request para login"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response del login exitoso"""
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    """Schema de usuario (sin password)"""
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[str]
    
    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    """Request para crear usuario (solo superuser)"""
    email: EmailStr
    password: str
    full_name: str
    role: UserRole


# ==========================================
# Endpoints
# ==========================================

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login con email y contraseña
    
    Retorna un JWT token válido por 8 horas
    """
    user = authenticate_user(request.email, request.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active
        }
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Obtiene la información del usuario actual
    
    Requiere estar autenticado (token en header Authorization: Bearer <token>)
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )


@router.post("/create-user", response_model=UserResponse)
def create_user_endpoint(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """
    Crea un nuevo usuario (solo superusuarios)
    
    El superusuario puede crear workers o más superusuarios
    """
    from auth import create_user
    
    try:
        new_user = create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            role=request.role,
            db=db
        )
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role.value,
            is_active=new_user.is_active,
            last_login=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """
    Lista todos los usuarios (solo superusuarios)
    """
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            last_login=user.last_login.isoformat() if user.last_login else None
        )
        for user in users
    ]
