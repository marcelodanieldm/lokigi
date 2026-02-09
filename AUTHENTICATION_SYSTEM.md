# 🔐 Sistema de Autenticación - Backoffice

## 📋 Resumen

Sistema completo de autenticación con **JWT tokens** y **roles de usuario** para proteger el acceso al dashboard.

---

## 👥 Roles de Usuario

### 1. **Superusuario** (`superuser`)
- Acceso completo al dashboard
- Puede ver todas las órdenes
- Puede ver estadísticas y revenue
- Puede crear nuevos usuarios
- Ruta: `/dashboard`

### 2. **Trabajador** (`worker`)
- Acceso solo al Work Queue
- Puede gestionar tareas de órdenes
- No puede ver estadísticas generales
- Ruta: `/dashboard/work`

---

## 🏗️ Arquitectura

### Backend (FastAPI + JWT)

```
┌─────────────────────────────────────────┐
│ models.py                               │
│ ├─ User (email, hashed_password, role) │
│ └─ UserRole enum (SUPERUSER, WORKER)   │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ auth.py                                 │
│ ├─ Password hashing (bcrypt)           │
│ ├─ JWT token creation/validation       │
│ ├─ get_current_user() dependency       │
│ └─ require_role() guards               │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ api_auth.py                             │
│ ├─ POST /api/auth/login                │
│ ├─ GET /api/auth/me                    │
│ ├─ POST /api/auth/create-user          │
│ └─ GET /api/auth/users                 │
└─────────────────────────────────────────┘
```

### Frontend (Next.js + localStorage)

```
┌─────────────────────────────────────────┐
│ /backoffice (Login Page)               │
│ ├─ Email + Password form              │
│ ├─ Calls POST /api/auth/login         │
│ ├─ Stores token in localStorage       │
│ └─ Redirects by role                  │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ AuthGuard Component                     │
│ ├─ Checks token existence              │
│ ├─ Validates with GET /api/auth/me    │
│ ├─ Redirects if invalid/expired       │
│ └─ Enforces role requirements          │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Protected Routes                        │
│ ├─ /dashboard (superuser only)        │
│ └─ /dashboard/work (any role)         │
└─────────────────────────────────────────┘
```

---

## 🚀 Setup Inicial

### Paso 1: Recrear Base de Datos

```bash
cd c:\Users\danie\OneDrive\Escritorio\proyectos programacion\lokigi
python recreate_db.py
```

Esto crea la tabla `users` con los campos necesarios.

### Paso 2: Crear Usuarios Iniciales

```bash
python create_users.py
```

**Output:**
```
✅ Superusuario creado:
   Email: admin@lokigi.com
   Password: admin123
   Rol: superuser

✅ Trabajador creado:
   Email: trabajo@lokigi.com
   Password: trabajo123
   Rol: worker
```

### Paso 3: Iniciar Backend

```bash
python main.py
```

### Paso 4: Iniciar Frontend

```bash
cd frontend
npm run dev
```

---

## 🔌 API Endpoints

### 1. Login

**POST** `/api/auth/login`

**Request:**
```json
{
  "email": "admin@lokigi.com",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@lokigi.com",
    "full_name": "Administrador",
    "role": "superuser",
    "is_active": true
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Email o contraseña incorrectos"
}
```

---

### 2. Get Current User

**GET** `/api/auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "admin@lokigi.com",
  "full_name": "Administrador",
  "role": "superuser",
  "is_active": true,
  "last_login": "2024-12-19T10:30:00"
}
```

---

### 3. Create User (Superuser Only)

**POST** `/api/auth/create-user`

**Headers:**
```
Authorization: Bearer <superuser_token>
```

**Request:**
```json
{
  "email": "nuevo@lokigi.com",
  "password": "password123",
  "full_name": "Nuevo Trabajador",
  "role": "worker"
}
```

**Response (200 OK):**
```json
{
  "id": 3,
  "email": "nuevo@lokigi.com",
  "full_name": "Nuevo Trabajador",
  "role": "worker",
  "is_active": true,
  "last_login": null
}
```

---

### 4. List Users (Superuser Only)

**GET** `/api/auth/users`

**Headers:**
```
Authorization: Bearer <superuser_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "email": "admin@lokigi.com",
    "full_name": "Administrador",
    "role": "superuser",
    "is_active": true,
    "last_login": "2024-12-19T10:30:00"
  },
  {
    "id": 2,
    "email": "trabajo@lokigi.com",
    "full_name": "Usuario Trabajo",
    "role": "worker",
    "is_active": true,
    "last_login": "2024-12-19T09:15:00"
  }
]
```

---

## 🎨 Frontend Flow

### 1. Login Page (`/backoffice`)

```tsx
User visits /backoffice
  ↓
Enters email + password
  ↓
Clicks "Iniciar Sesión"
  ↓
Frontend: POST /api/auth/login
  ↓
Success?
  ├─ Yes → Store token + user in localStorage
  │        ├─ Superuser? → Redirect to /dashboard
  │        └─ Worker? → Redirect to /dashboard/work
  │
  └─ No → Show error message
```

### 2. Protected Routes

```tsx
User visits /dashboard or /dashboard/work
  ↓
AuthGuard checks localStorage
  ↓
Token exists?
  ├─ No → Redirect to /backoffice
  │
  └─ Yes → Validate with GET /api/auth/me
           ↓
           Valid?
           ├─ No → Redirect to /backoffice
           │
           └─ Yes → Check role requirement
                    ↓
                    Correct role?
                    ├─ Yes → Show dashboard
                    └─ No → Redirect to correct dashboard
```

### 3. Logout

```tsx
User clicks "Cerrar Sesión"
  ↓
localStorage.removeItem('auth_token')
localStorage.removeItem('user')
  ↓
Redirect to /backoffice
```

---

## 🔒 Security Features

### 1. Password Hashing
```python
# Usando bcrypt con salt automático
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

### 2. JWT Tokens
```python
# Token expira en 8 horas
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Payload incluye:
{
  "sub": user_id,
  "email": user.email,
  "role": user.role,
  "exp": expiration_timestamp
}
```

### 3. Role-Based Access Control (RBAC)
```python
# Dependency para requerir rol específico
@router.get("/admin-only")
def admin_route(user: User = Depends(require_superuser)):
    return {"message": "Admin access"}
```

### 4. Token Validation
```python
# Cada request verifica:
1. Token existe en header Authorization
2. Token no está expirado
3. Usuario existe en DB
4. Usuario está activo (is_active=True)
5. Rol del usuario cumple requisitos
```

---

## 🎯 Casos de Uso

### Caso 1: Superusuario Login

```
1. Admin abre http://localhost:3000/backoffice
2. Ingresa: admin@lokigi.com / admin123
3. Click "Iniciar Sesión"
4. Sistema valida credenciales ✅
5. Recibe token JWT válido por 8 horas
6. Redirect automático a /dashboard
7. Ve: Stats, órdenes, revenue, todo
```

### Caso 2: Trabajador Login

```
1. Worker abre http://localhost:3000/backoffice
2. Ingresa: trabajo@lokigi.com / trabajo123
3. Click "Iniciar Sesión"
4. Sistema valida credenciales ✅
5. Recibe token JWT válido por 8 horas
6. Redirect automático a /dashboard/work
7. Ve: Solo Work Queue con tareas
```

### Caso 3: Trabajador Intenta Acceder a Dashboard de Admin

```
1. Worker logueado intenta abrir /dashboard
2. AuthGuard detecta role="worker"
3. Redirect automático a /dashboard/work
4. Worker solo puede acceder a su área
```

### Caso 4: Token Expirado

```
1. Usuario con token de hace 9 horas (expirado)
2. Intenta abrir /dashboard
3. AuthGuard valida con GET /api/auth/me
4. Backend responde 401 Unauthorized
5. Frontend elimina token
6. Redirect a /backoffice
7. Usuario debe hacer login nuevamente
```

---

## 📝 Credenciales por Defecto

### Desarrollo/Testing

| Rol          | Email                | Password   | Acceso               |
|--------------|---------------------|------------|----------------------|
| Superuser    | admin@lokigi.com    | admin123   | Todo el dashboard    |
| Worker       | trabajo@lokigi.com  | trabajo123 | Solo Work Queue      |

**⚠️ IMPORTANTE:** Cambiar estas credenciales en producción.

---

## 🔧 Configuración

### Backend (auth.py)

```python
# TODO: Mover a variables de entorno
SECRET_KEY = "lokigi-secret-key-change-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas
```

**Para producción:**
```bash
# .env
JWT_SECRET_KEY=<random-secure-key-here>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=480
```

### Frontend (API URL)

```typescript
// Cambiar en producción
const API_URL = "http://localhost:8000";
```

---

## 🧪 Testing

### Test 1: Login Exitoso

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@lokigi.com",
    "password": "admin123"
  }'
```

### Test 2: Get Current User

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your_token>"
```

### Test 3: Create New User (Superuser)

```bash
curl -X POST http://localhost:8000/api/auth/create-user \
  -H "Authorization: Bearer <superuser_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@lokigi.com",
    "password": "password123",
    "full_name": "Nuevo Usuario",
    "role": "worker"
  }'
```

---

## 🚨 Troubleshooting

### Error: "Token inválido o expirado"

**Causa:** Token JWT expiró (>8 horas) o es inválido.

**Solución:** Hacer logout y login nuevamente.

---

### Error: "Se requiere rol superuser"

**Causa:** Usuario worker intenta acceder a endpoint de superuser.

**Solución:** Verificar que el usuario tiene el rol correcto.

---

### Error: "Usuario inactivo"

**Causa:** Usuario tiene `is_active=False` en la base de datos.

**Solución:** Activar usuario desde la base de datos:
```sql
UPDATE users SET is_active = true WHERE email = 'usuario@email.com';
```

---

## 🔐 Best Practices

### 1. Nunca exponer tokens en logs
```typescript
// ❌ MAL
console.log('Token:', token);

// ✅ BIEN
console.log('User authenticated');
```

### 2. Usar HTTPS en producción
```python
# Solo permitir cookies seguras en producción
if os.getenv('ENV') == 'production':
    cookie_secure = True
```

### 3. Refresh tokens (TODO)
Implementar refresh tokens para renovar sin re-login:
```python
# Token de acceso: 15 minutos
# Refresh token: 7 días
```

### 4. Rate limiting (TODO)
Limitar intentos de login:
```python
# Máximo 5 intentos por minuto por IP
```

---

## 📦 Archivos Creados

### Backend
- `models.py` - User model + UserRole enum
- `auth.py` - JWT + password hashing utils
- `api_auth.py` - Auth endpoints
- `create_users.py` - Script para crear usuarios

### Frontend
- `app/backoffice/page.tsx` - Login page
- `components/AuthGuard.tsx` - Route protection
- `components/LogoutButton.tsx` - Logout functionality

---

## ✅ Checklist de Implementación

- [x] Modelo User con roles
- [x] Password hashing con bcrypt
- [x] JWT token creation/validation
- [x] Login endpoint
- [x] Get current user endpoint
- [x] Create user endpoint (superuser only)
- [x] List users endpoint (superuser only)
- [x] Frontend login page
- [x] AuthGuard component
- [x] Role-based redirects
- [x] Logout functionality
- [x] Protected dashboard routes
- [x] Script para crear usuarios iniciales

---

**Sistema de autenticación completo y listo para usar! 🎉**
