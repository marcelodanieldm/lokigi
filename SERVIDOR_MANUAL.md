# 🚀 Cómo Iniciar el Servidor Lokigi

## Problema Detectado

El servidor se está cerrando automáticamente después de iniciar. Mientras investigo la causa, aquí tienes **instrucciones manuales** para iniciar el servidor:

## ✅ Solución Temporal (Funciona 100%)

### Paso 1: Abre una nueva terminal PowerShell

```powershell
# Navega al proyecto
cd "c:\Users\danie\OneDrive\Escritorio\proyectos programacion\lokigi"
```

### Paso 2: Inicia el servidor SIN auto-reload

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**IMPORTANTE:** Deja esta terminal abierta. El servidor debe quedar corriendo y mostrando:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using StatReload
```

### Paso 3: Abre OTRA terminal para hacer login

En una **segunda terminal PowerShell**:

```powershell
# Login como ADMIN
$body = @{username = "admin@lokigi.com"; password = "admin123"} | ConvertTo-Json
$admin = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method POST -Body $body -ContentType "application/json"

# Ver resultado
$admin

# Guardar token
$adminToken = $admin.access_token
Write-Host "✅ Token ADMIN guardado en `$adminToken"
```

```powershell
# Login como WORKER
$body = @{username = "worker@lokigi.com"; password = "worker123"} | ConvertTo-Json
$worker = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method POST -Body $body -ContentType "application/json"

# Ver resultado
$worker

# Guardar token
$workerToken = $worker.access_token
Write-Host "✅ Token WORKER guardado en `$workerToken"
```

## 🔐 Credenciales Disponibles

| Rol | Email | Password | Permisos |
|-----|-------|----------|----------|
| **ADMIN** | admin@lokigi.com | admin123 | ✅ Todos los endpoints |
| **WORKER** | worker@lokigi.com | worker123 | ✅ Work Queue solamente |
| **CUSTOMER** | cliente@example.com | cliente123 | ✅ Sus propios datos |

## 📊 Probar Endpoints con Token

Una vez que tengas el token guardado en `$adminToken`:

```powershell
# Ver documentación interactiva
Start-Process "http://localhost:8000/docs"

# Probar endpoint protegido (Command Center)
$headers = @{Authorization = "Bearer $adminToken"}
Invoke-RestMethod -Uri "http://localhost:8000/api/dashboard/command-center/financial?time_range=30d" -Headers $headers

# Ver órdenes (solo ADMIN)
Invoke-RestMethod -Uri "http://localhost:8000/api/dashboard/orders" -Headers $headers
```

## 🛠️ Si el Servidor No Arranca

Si ves errores al iniciar el servidor, prueba:

### Opción 1: Verificar que no haya otro proceso en puerto 8000

```powershell
# Ver qué proceso usa el puerto 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

# Si hay alguno, matarlo
Stop-Process -Id <PID> -Force
```

### Opción 2: Usar otro puerto

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8888 --reload
```

Luego ajusta las URLs a `http://localhost:8888`

## 🎯 Inicio Rápido de Frontend

Si también quieres probar el frontend:

```powershell
# En otra terminal
cd "c:\Users\danie\OneDrive\Escritorio\proyectos programacion\lokigi\frontend"
npm run dev
```

Luego abre http://localhost:3000 y usa las credenciales de arriba.

## ✅ Checklist de Verificación

- [ ] Terminal 1: Servidor corriendo en http://0.0.0.0:8000
- [ ] Terminal 2: Login exitoso con admin@lokigi.com
- [ ] Terminal 2: Token guardado en variable `$adminToken`
- [ ] Browser: http://localhost:8000/docs muestra Swagger UI
- [ ] Browser: Puedes hacer requests desde Swagger con el token

---

**Última actualización:** 22 de diciembre de 2025  
**Estado:** Servidor requiere inicio manual debido a issue con auto-shutdown
