# 🚀 SCRIPT COMPLETO DE LOGIN - LOKIGI
# Ejecuta este script cada vez que necesites iniciar el servidor y hacer login

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          🚀 LOKIGI - Inicio Completo del Sistema         ║" -ForegroundColor Cyan  
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Paso 1: Iniciar servidor en ventana separada
Write-Host "1️⃣  Iniciando servidor..." -ForegroundColor Yellow
$serverPath = "$PSScriptRoot"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$serverPath'; Write-Host '🚀 SERVIDOR LOKIGI' -ForegroundColor Green; Write-Host 'http://127.0.0.1:8000' -ForegroundColor Yellow; Write-Host 'Docs: http://127.0.0.1:8000/docs' -ForegroundColor Gray; Write-Host ''; python -m uvicorn main:app --host 127.0.0.1 --port 8000"
Write-Host "   ✅ Servidor iniciado en ventana separada" -ForegroundColor Green

# Paso 2: Esperar a que el servidor esté listo
Write-Host "`n2️⃣  Esperando a que el servidor esté listo..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Paso 3: Verificar que el servidor responde
Write-Host "`n3️⃣  Verificando conexión..." -ForegroundColor Yellow
try {
    $null = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -UseBasicParsing -TimeoutSec 3
    Write-Host "   ✅ Servidor respondiendo correctamente" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Servidor no responde aún, esperando 5 segundos más..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Paso 4: Login como ADMIN
Write-Host "`n4️⃣  Login como ADMIN..." -ForegroundColor Yellow
try {
    $body = @{email="admin@lokigi.com"; password="admin123"} | ConvertTo-Json
    $admin = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" -Method POST -Body $body -ContentType "application/json"
    
    Write-Host "`n   ✅ LOGIN ADMIN EXITOSO" -ForegroundColor Green
    Write-Host "   📧 Email: $($admin.user.email)" -ForegroundColor Cyan
    Write-Host "   👤 Nombre: $($admin.user.full_name)" -ForegroundColor Cyan
    Write-Host "   🎭 Rol: $($admin.user.role.ToUpper())" -ForegroundColor Yellow
    Write-Host "   🎫 Token: $($admin.access_token.Substring(0,60))..." -ForegroundColor Gray
    
    # Guardar en variable global
    $global:adminToken = $admin.access_token
    $global:adminUser = $admin.user
    
} catch {
    Write-Host "   ❌ Error en login ADMIN: $_" -ForegroundColor Red
}

# Paso 5: Login como WORKER  
Write-Host "`n5️⃣  Login como WORKER..." -ForegroundColor Yellow
try {
    $body = @{email="worker@lokigi.com"; password="worker123"} | ConvertTo-Json
    $worker = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" -Method POST -Body $body -ContentType "application/json"
    
    Write-Host "`n   ✅ LOGIN WORKER EXITOSO" -ForegroundColor Green
    Write-Host "   📧 Email: $($worker.user.email)" -ForegroundColor Cyan
    Write-Host "   👤 Nombre: $($worker.user.full_name)" -ForegroundColor Cyan
    Write-Host "   🎭 Rol: $($worker.user.role.ToUpper())" -ForegroundColor Yellow
    Write-Host "   🎫 Token: $($worker.access_token.Substring(0,60))..." -ForegroundColor Gray
    
    # Guardar en variable global
    $global:workerToken = $worker.access_token
    $global:workerUser = $worker.user
    
} catch {
    Write-Host "   ❌ Error en login WORKER: $_" -ForegroundColor Red
}

# Paso 6: Login como CUSTOMER
Write-Host "`n6️⃣  Login como CUSTOMER..." -ForegroundColor Yellow
try {
    $body = @{email="cliente@example.com"; password="cliente123"} | ConvertTo-Json
    $customer = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" -Method POST -Body $body -ContentType "application/json"
    
    Write-Host "`n   ✅ LOGIN CUSTOMER EXITOSO" -ForegroundColor Green
    Write-Host "   📧 Email: $($customer.user.email)" -ForegroundColor Cyan
    Write-Host "   👤 Nombre: $($customer.user.full_name)" -ForegroundColor Cyan
    Write-Host "   🎭 Rol: $($customer.user.role.ToUpper())" -ForegroundColor Yellow
    Write-Host "   🎫 Token: $($customer.access_token.Substring(0,60))..." -ForegroundColor Gray
    
    # Guardar en variable global
    $global:customerToken = $customer.access_token
    $global:customerUser = $customer.user
    
} catch {
    Write-Host "   ❌ Error en login CUSTOMER: $_" -ForegroundColor Red
}

# Resumen final
Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              ✅ Sistema Iniciado Correctamente            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "🌐 Servidor corriendo: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "📚 Documentación: http://127.0.0.1:8000/docs`n" -ForegroundColor Yellow

Write-Host "🔑 Tokens disponibles:" -ForegroundColor Cyan
Write-Host "   • `$adminToken    - Token de ADMIN" -ForegroundColor White
Write-Host "   • `$workerToken   - Token de WORKER" -ForegroundColor White
Write-Host "   • `$customerToken - Token de CUSTOMER`n" -ForegroundColor White

Write-Host "📋 Ejemplos de uso:" -ForegroundColor Cyan
Write-Host @"
   # Ver Command Center (solo ADMIN):
   `$headers = @{Authorization = "Bearer `$adminToken"}
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/dashboard/command-center/financial?time_range=30d" -Headers `$headers

   # Ver Work Queue (WORKER):
   `$headers = @{Authorization = "Bearer `$workerToken"}
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/dashboard/work/queue" -Headers `$headers

   # Ver perfil (CUSTOMER):
   `$headers = @{Authorization = "Bearer `$customerToken"}
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/customer/me" -Headers `$headers
"@ -ForegroundColor Gray

Write-Host "`n🎯 Todo listo para trabajar!" -ForegroundColor Green
Write-Host "="*62 -ForegroundColor Cyan
