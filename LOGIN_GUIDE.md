# 🔐 GUÍA DE LOGIN - LOKIGI

## ✅ SOLUCIÓN VERIFICADA Y FUNCIONANDO

**Problema resuelto:** El servidor necesita ejecutarse en ventana separada y el campo de login es `email` (no `username`).

## 🚀 Inicio Rápido (1 Comando)

```powershell
# Ejecuta este script que lo hace todo automáticamente
.\START_LOKIGI.ps1
```

Este script:
1. ✅ Inicia el servidor en ventana separada
2. ✅ Hace login como ADMIN, WORKER y CUSTOMER
3. ✅ Guarda los tokens en variables `$adminToken`, `$workerToken`, `$customerToken`

---

## Usuarios Disponibles

### 1️⃣ ADMIN (Acceso Total)
- **Email:** admin@lokigi.com
- **Password:** admin123
- **Dashboard:** http://localhost:3000/dashboard
- **Permisos:** ✅ Métricas ✅ Command Center ✅ Exportar ✅ Pagos ✅ Usuarios

### 2️⃣ WORKER (Work Queue)
- **Email:** worker@lokigi.com
- **Password:** worker123
- **Dashboard:** http://localhost:3000/dashboard/work
- **Permisos:** ✅ Work Queue ✅ Tareas ❌ Métricas Financieras

### 3️⃣ CUSTOMER (Portal Cliente)
- **Email:** cliente@example.com
- **Password:** cliente123
- **Portal:** http://localhost:3000/customer
- **Permisos:** ✅ Sus reportes ✅ Sus pagos ✅ Radar ❌ Datos de otros

---

## 🚀 Cómo Hacer Login (Manual)

### Opción 1: cURL (Terminal)

#### Login como ADMIN:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@lokigi.com",
    "password": "admin123"
  }'
```

**Respuesta esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@lokigi.com",
    "full_name": "Daniel - Administrador",
    "role": "admin"
  }
}
```

#### Login como WORKER:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "worker@lokigi.com",
    "password": "worker123"
  }'
```

**Respuesta esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "email": "worker@lokigi.com",
    "full_name": "Trabajador - Cola de Tareas",
    "role": "worker"
  }
}
```

---

### Opción 2: PowerShell (Windows)

#### Login como ADMIN:
```powershell
$body = @{
    email = "admin@lokigi.com"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Ver respuesta
$response

# Guardar token
$token = $response.access_token
Write-Host "Token guardado: $token"

# Usar token en siguiente request
$headers = @{
    Authorization = "Bearer $token"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/dashboard/orders" `
    -Method GET `
    -Headers $headers
```

#### Login como WORKER:
```powershell
$body = @{
    email = "worker@lokigi.com"
    password = "worker123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$token = $response.access_token
Write-Host "Token guardado: $token"
```

---

### Opción 3: Python (requests)

```python
import requests

# Login como ADMIN
def login_admin():
    url = "http://localhost:8000/api/auth/login"
    payload = {
        "email": "admin@lokigi.com",
        "password": "admin123"
    }
    response = requests.post(url, json=payload)
    data = response.json()
    
    print(f"✅ Login exitoso como {data['user']['role'].upper()}")
    print(f"Token: {data['access_token'][:50]}...")
    
    return data['access_token']

# Login como WORKER
def login_worker():
    url = "http://localhost:8000/api/auth/login"
    payload = {
        "email": "worker@lokigi.com",
        "password": "worker123"
    }
    response = requests.post(url, json=payload)
    data = response.json()
    
    print(f"✅ Login exitoso como {data['user']['role'].upper()}")
    print(f"Token: {data['access_token'][:50]}...")
    
    return data['access_token']

# Usar token
def get_orders(token):
    url = "http://localhost:8000/api/dashboard/orders"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()

# Ejecutar
if __name__ == "__main__":
    # Login como admin
    admin_token = login_admin()
    orders = get_orders(admin_token)
    print(f"Órdenes obtenidas: {len(orders)}")
```

---

### Opción 4: Postman / Insomnia

1. **Nueva Request:**
   - Method: `POST`
   - URL: `http://localhost:8000/api/auth/login`
   - Headers: `Content-Type: application/json`

2. **Body (raw JSON):**

**Para ADMIN:**
```json
{
  "email": "admin@lokigi.com",
  "password": "admin123"
}
```

**Para WORKER:**
```json
{
  "email": "worker@lokigi.com",
  "password": "worker123"
}
```

3. **Copiar el `access_token` de la respuesta**

4. **Usar en requests protegidas:**
   - Headers: `Authorization: Bearer <tu_token>`

---

### Opción 5: Frontend (React/Next.js)

```typescript
// utils/auth.ts
export async function login(email: string, password: string) {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password,
    }),
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const data = await response.json();
  
  // Guardar token en localStorage
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('user_role', data.user.role);
  
  return data;
}

// Login como ADMIN
const adminData = await login('admin@lokigi.com', 'admin123');
console.log('Logged in as:', adminData.user.role);

// Login como WORKER
const workerData = await login('worker@lokigi.com', 'worker123');
console.log('Logged in as:', workerData.user.role);

// Usar token en requests
async function getOrders() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/dashboard/orders', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  return response.json();
}
```

---

## 🔍 Verificar Permisos por Rol

### ADMIN puede acceder a:
```bash
# Command Center (BI Dashboard)
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/dashboard/command-center/financial

# Churn Analytics
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/retention/churn-analytics

# Todos los endpoints
```

### WORKER puede acceder a:
```bash
# Work Queue
curl -H "Authorization: Bearer $WORKER_TOKEN" \
  http://localhost:8000/api/dashboard/work/queue

# Órdenes asignadas
curl -H "Authorization: Bearer $WORKER_TOKEN" \
  http://localhost:8000/api/dashboard/work/my-orders

# ❌ NO puede acceder a métricas financieras
curl -H "Authorization: Bearer $WORKER_TOKEN" \
  http://localhost:8000/api/dashboard/command-center/financial
# Respuesta: 403 Forbidden
```

### CUSTOMER puede acceder a:
```bash
# Su perfil
curl -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  http://localhost:8000/api/customer/me

# Sus reportes
curl -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  http://localhost:8000/api/customer/reports

# ❌ NO puede ver reportes de otros clientes
curl -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  http://localhost:8000/api/customer/reports/999
# Respuesta: 403 Forbidden
```

---

## 📊 Endpoints por Rol

### 🔴 ADMIN Only
- `GET /api/dashboard/command-center/*` - BI Dashboard
- `GET /api/retention/churn-analytics` - Análisis de churn
- `GET /api/dashboard/orders` - Todas las órdenes
- `POST /api/auth/register` - Crear usuarios
- `DELETE /api/users/{id}` - Eliminar usuarios

### 🟡 WORKER Only
- `GET /api/dashboard/work/queue` - Cola de trabajo
- `GET /api/dashboard/work/my-orders` - Mis órdenes asignadas
- `POST /api/dashboard/work/complete/{order_id}` - Completar orden

### 🟢 CUSTOMER Only
- `GET /api/customer/me` - Mi perfil
- `GET /api/customer/reports` - Mis reportes
- `GET /api/customer/orders` - Mis pagos
- `GET /api/customer/radar/*` - Mi suscripción Radar

### 🔵 Public (Sin autenticación)
- `POST /api/v1/create-lead` - Crear lead
- `POST /api/v1/analyze` - Análisis de negocio
- `POST /api/auth/login` - Login
- `POST /api/payments/webhook` - Webhook de Stripe

---

## 🔧 Troubleshooting

### Error: "Invalid credentials"
```json
{
  "detail": "Incorrect email or password"
}
```
**Solución:** Verifica que el email y password sean correctos.

### Error: "Could not validate credentials"
```json
{
  "detail": "Could not validate credentials"
}
```
**Solución:** El token expiró o es inválido. Haz login nuevamente.

### Error: "Forbidden"
```json
{
  "detail": "Only admins can access this endpoint"
}
```
**Solución:** Tu rol no tiene permisos para ese endpoint. Usa credenciales de ADMIN.

### Error: "Token has expired"
```json
{
  "detail": "Token has expired"
}
```
**Solución:** Los tokens duran 30 días. Haz login nuevamente para obtener un token fresco.

---

## 🎯 Ejemplos Prácticos

### Workflow completo ADMIN:

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@lokigi.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Ver Command Center - Financial
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/dashboard/command-center/financial?time_range=30d" \
  | jq

# 3. Ver Churn Analytics
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/retention/churn-analytics?time_range=30d" \
  | jq

# 4. Ver todas las órdenes
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/dashboard/orders" \
  | jq
```

### Workflow completo WORKER:

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"worker@lokigi.com","password":"worker123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Ver mi cola de trabajo
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/dashboard/work/queue" \
  | jq

# 3. Ver mis órdenes asignadas
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/dashboard/work/my-orders" \
  | jq

# 4. Completar una orden (orden_id=1)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/dashboard/work/complete/1" \
  | jq
```

---

## 🔐 Seguridad

### Tokens JWT:
- **Algoritmo:** HS256
- **Expiración:** 30 días
- **Refresh:** No automático, requiere re-login
- **Storage:** localStorage (frontend) o variable de entorno (backend)

### Cambiar contraseñas:
```bash
# TODO: Implementar endpoint PUT /api/auth/change-password
```

### Crear nuevos usuarios:
```bash
# Solo ADMIN puede crear usuarios
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@lokigi.com",
    "password": "secure123",
    "full_name": "Nuevo Usuario",
    "role": "worker"
  }'
```

---

**Última actualización:** Diciembre 22, 2025  
**Sistema RBAC:** Admin, Worker, Customer  
**Autenticación:** JWT (30 días)
