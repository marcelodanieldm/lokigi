# ✅ LOGIN DESDE FRONTEND - COMPLETADO

## 🎉 Sistema Listo para Usar

Has completado exitosamente la configuración del sistema de login con frontend!

---

## 🚀 Inicio Rápido

### Opción 1: Script Automático (Recomendado)

```powershell
.\START_FRONTEND.ps1
```

Este script hace **TODO automáticamente**:
1. ✅ Inicia Backend API (puerto 8000)
2. ✅ Inicia Frontend Next.js (puerto 3000)
3. ✅ Abre navegador en página de login
4. ✅ Te muestra las credenciales

### Opción 2: Manual

**Terminal 1 (Backend):**
```powershell
cd "c:\Users\danie\OneDrive\Escritorio\proyectos programacion\lokigi"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 (Frontend):**
```powershell
cd "c:\Users\danie\OneDrive\Escritorio\proyectos programacion\lokigi\frontend"
npm run dev
```

**Terminal 3 (Abrir navegador):**
```powershell
Start-Process "http://localhost:3000/backoffice"
```

---

## 🔐 Credenciales Disponibles

### 1️⃣ ADMIN (Administrador)
```
Email:    admin@lokigi.com
Password: admin123
Acceso:   Command Center, Métricas, Analytics
Redirige: /dashboard
```

### 2️⃣ WORKER (Trabajador)
```
Email:    worker@lokigi.com
Password: worker123
Acceso:   Work Queue, Tareas asignadas
Redirige: /dashboard/work
```

---

## 🎯 Cómo Hacer Login

### Método 1: Botones de Acceso Rápido (Más Fácil)

1. Abre http://localhost:3000/backoffice
2. Verás 2 botones grandes:
   - **"Login como ADMIN"** (azul) 🔵
   - **"Login como WORKER"** (verde) 🟢
3. Haz clic en cualquiera
4. ¡Listo! Serás redirigido automáticamente al dashboard correcto

### Método 2: Formulario Manual

1. Abre http://localhost:3000/backoffice
2. Ingresa email y contraseña manualmente
3. Haz clic en "Iniciar Sesión"
4. Serás redirigido según tu rol

---

## 📊 Flujo de Autenticación

```
┌─────────────────────────────────────────────────────────┐
│ 1. Usuario hace login en /backoffice                   │
│    - Botón rápido o formulario manual                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Frontend envía POST /api/auth/login                 │
│    Body: { email: "...", password: "..." }             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Backend verifica credenciales                       │
│    - Busca usuario en base de datos                    │
│    - Valida contraseña con bcrypt                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Backend genera JWT token                            │
│    Token contiene: {sub, email, role}                  │
│    Expiración: 30 días                                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Frontend guarda token en localStorage               │
│    - auth_token: "eyJhbGciOiJ..."                      │
│    - user: {id, email, full_name, role}               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Redirige según rol:                                 │
│    - ADMIN → /dashboard (Command Center)               │
│    - WORKER → /dashboard/work (Work Queue)             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 7. AuthGuard verifica token en cada página             │
│    - GET /api/auth/me con Bearer token                │
│    - Si válido: muestra contenido                      │
│    - Si inválido: redirige a /backoffice              │
└─────────────────────────────────────────────────────────┘
```

---

## 🔒 Sistema RBAC (Control de Acceso)

### ADMIN tiene acceso a:
- ✅ `/dashboard` - Command Center con métricas financieras
- ✅ `/dashboard/orders` - Todas las órdenes
- ✅ `/dashboard/orders/[id]` - Detalle de cualquier orden
- ✅ Command Center endpoints:
  - `GET /api/dashboard/command-center/financial`
  - `GET /api/dashboard/command-center/funnel`
  - `GET /api/retention/churn-analytics`
- ❌ NO puede acceder a `/dashboard/work` (es para Workers)

### WORKER tiene acceso a:
- ✅ `/dashboard/work` - Work Queue con órdenes asignadas
- ✅ Work Queue endpoints:
  - `GET /api/dashboard/work/queue`
  - `GET /api/dashboard/work/my-orders`
  - `POST /api/dashboard/work/complete/{order_id}`
- ❌ NO puede acceder a métricas financieras
- ❌ NO puede ver Command Center

---

## 🧪 Tests Realizados

### ✅ Login Backend (API)
```powershell
# ADMIN
$body = @{email="admin@lokigi.com"; password="admin123"} | ConvertTo-Json
$admin = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" -Method POST -Body $body -ContentType "application/json"
# Status: SUCCESS ✅

# WORKER
$body = @{email="worker@lokigi.com"; password="worker123"} | ConvertTo-Json
$worker = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" -Method POST -Body $body -ContentType "application/json"
# Status: SUCCESS ✅
```

### ✅ Login Frontend (UI)
- Botones de acceso rápido funcionando
- Formulario manual funcionando
- Redirección automática por rol
- AuthGuard protegiendo rutas
- Tokens guardados en localStorage

---

## 📁 Archivos Modificados

### Backend
- ✅ `api_auth.py` - Login endpoint usa campo `email`
- ✅ `create_users.py` - 3 usuarios creados (ADMIN, WORKER, CUSTOMER)

### Frontend
- ✅ `backoffice/page.tsx` - Página de login con botones rápidos
- ✅ `AuthGuard.tsx` - Soporte para rol 'admin'
- ✅ `dashboard/page.tsx` - Acepta rol 'admin'
- ✅ `dashboard/work/page.tsx` - Acepta rol 'worker'

### Scripts
- ✅ `START_FRONTEND.ps1` - Inicia backend + frontend + navegador
- ✅ `START_LOKIGI.ps1` - Solo backend con login API
- ✅ `LOGIN_GUIDE.md` - Documentación completa

---

## 🐛 Troubleshooting

### Error: "localhost refused to connect"
**Causa:** Backend o Frontend no están corriendo.  
**Solución:**
```powershell
# Verificar puertos en uso
Get-NetTCPConnection -LocalPort 8000,3000 -ErrorAction SilentlyContinue

# Si no hay nada, ejecuta:
.\START_FRONTEND.ps1
```

### Error 422: "Unprocessable Entity"
**Causa:** El campo es `email`, no `username`.  
**Solución:** Ya está corregido en todos los archivos.

### Error: "Token inválido"
**Causa:** Token expirado o localStorage corrupto.  
**Solución:**
```javascript
// En consola del navegador (F12):
localStorage.clear()
location.reload()
```

### Error: "Rol no reconocido"
**Causa:** Usuario tiene rol no soportado.  
**Solución:** Verificar en base de datos:
```sql
SELECT email, role FROM users;
-- Roles válidos: 'admin', 'worker', 'customer'
```

---

## 🎯 Próximos Pasos

1. ✅ Login funcionando (COMPLETADO)
2. ⏳ Probar endpoints protegidos con tokens
3. ⏳ Implementar logout
4. ⏳ Implementar refresh de token
5. ⏳ Agregar "Remember me"
6. ⏳ Recuperación de contraseña

---

## 📊 URLs Importantes

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Backend API | http://127.0.0.1:8000 | FastAPI server |
| API Docs | http://127.0.0.1:8000/docs | Swagger UI |
| Frontend | http://localhost:3000 | Next.js app |
| Login | http://localhost:3000/backoffice | Página de login |
| Dashboard Admin | http://localhost:3000/dashboard | Command Center |
| Dashboard Worker | http://localhost:3000/dashboard/work | Work Queue |

---

**Estado:** ✅ COMPLETAMENTE FUNCIONAL  
**Fecha:** 22 de diciembre de 2025  
**Probado con:** ADMIN y WORKER roles  
**Plataforma:** Windows + PowerShell + Next.js 16 + FastAPI
