"""
Sistema de Autenticación con JWT para el Backoffice
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole

# Configuración
SECRET_KEY = "lokigi-secret-key-change-in-production-2024"  # TODO: Mover a .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()


# ==========================================
# Password Utils
# ==========================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña coincida con el hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashea una contraseña"""
    return pwd_context.hash(password)


# ==========================================
# JWT Token Utils
# ==========================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decodifica un JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==========================================
# Authentication Functions
# ==========================================

def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    """
    Autentica un usuario por email y contraseña
    
    Returns:
        User si las credenciales son válidas, None si no
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    
    # Actualizar último login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obtener el usuario actual desde el token JWT
    
    Uso:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    return user


def require_role(required_role: UserRole):
    """
    Dependency para requerir un rol específico
    
    Uso:
        @router.get("/admin")
        def admin_only(current_user: User = Depends(require_role(UserRole.SUPERUSER))):
            return {"message": "Admin access"}
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol {required_role.value}"
            )
        return current_user
    return role_checker


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Shortcut para requerir superusuario"""
    if current_user.role != UserRole.SUPERUSER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo superusuarios pueden acceder"
        )
    return current_user


def require_worker_or_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Permite acceso a workers y superusers"""
    if current_user.role not in [UserRole.WORKER, UserRole.SUPERUSER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )
    return current_user


# ==========================================
# User Management Functions
# ==========================================

def create_user(
    email: str,
    password: str,
    full_name: str,
    role: UserRole,
    db: Session
) -> User:
    """
    Crea un nuevo usuario en la base de datos
    
    Args:
        email: Email único del usuario
        password: Contraseña en texto plano (será hasheada)
        full_name: Nombre completo
        role: Rol del usuario (SUPERUSER o WORKER)
        db: Sesión de base de datos
    
    Returns:
        Usuario creado
    """
    # Verificar que no exista
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError(f"El email {email} ya está registrado")
    
    # Crear usuario
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user
