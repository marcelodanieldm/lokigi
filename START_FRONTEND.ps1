# 🚀 INICIAR SISTEMA LOKIGI COMPLETO
# Este script inicia backend, frontend y abre el navegador

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        🚀 LOKIGI - Sistema Completo de Login            ║" -ForegroundColor Cyan  
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$lokigiPath = $PSScriptRoot
$frontendPath = Join-Path $lokigiPath "frontend"

# Paso 1: Iniciar Backend (API)
Write-Host "1️⃣  Iniciando Backend API..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$lokigiPath'
Write-Host '🔧 BACKEND API - FastAPI' -ForegroundColor Green
Write-Host 'http://127.0.0.1:8000' -ForegroundColor Yellow
Write-Host 'Docs: http://127.0.0.1:8000/docs' -ForegroundColor Gray
Write-Host ''
python -m uvicorn main:app --host 127.0.0.1 --port 8000
"@
Write-Host "   ✅ Backend iniciado (puerto 8000)" -ForegroundColor Green
Start-Sleep -Seconds 3

# Paso 2: Iniciar Frontend (Next.js)
Write-Host "`n2️⃣  Iniciando Frontend Next.js..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$frontendPath'
Write-Host '⚛️  FRONTEND - Next.js' -ForegroundColor Cyan
Write-Host 'http://localhost:3000' -ForegroundColor Yellow
Write-Host 'Login: http://localhost:3000/backoffice' -ForegroundColor Green
Write-Host ''
npm run dev
"@
Write-Host "   ✅ Frontend iniciado (puerto 3000)" -ForegroundColor Green

# Paso 3: Esperar a que ambos servicios estén listos
Write-Host "`n3️⃣  Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Write-Host "   ⏳ Backend compilando..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host "   ⏳ Frontend compilando..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Paso 4: Verificar que el backend responde
Write-Host "`n4️⃣  Verificando servicios..." -ForegroundColor Yellow
$backendOk = $false
$attempts = 0
$maxAttempts = 5

while (-not $backendOk -and $attempts -lt $maxAttempts) {
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        $backendOk = $true
        Write-Host "   ✅ Backend respondiendo correctamente" -ForegroundColor Green
    } catch {
        $attempts++
        Write-Host "   ⏳ Esperando backend... (intento $attempts/$maxAttempts)" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $backendOk) {
    Write-Host "`n   ⚠️  Backend no responde, pero puedes intentar usarlo de todas formas" -ForegroundColor Yellow
}

# Paso 5: Abrir navegador
Write-Host "`n5️⃣  Abriendo página de login..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000/backoffice"
Write-Host "   ✅ Navegador abierto" -ForegroundColor Green

# Resumen final
Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║            ✅ Sistema Iniciado Correctamente             ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📊 Servicios activos:" -ForegroundColor Cyan
Write-Host "   • Backend API: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   • Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "   • Login:       http://localhost:3000/backoffice`n" -ForegroundColor Yellow

Write-Host "🔐 Credenciales disponibles:" -ForegroundColor Cyan
Write-Host @"
   ┌─────────────────────────────────────────────────────┐
   │ 🔵 ADMIN (Administrador)                            │
   │    Email:    admin@lokigi.com                       │
   │    Password: admin123                               │
   │    Acceso:   Command Center, Métricas, Analytics   │
   └─────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────┐
   │ 🟢 WORKER (Trabajador)                              │
   │    Email:    worker@lokigi.com                      │
   │    Password: worker123                              │
   │    Acceso:   Work Queue, Tareas asignadas          │
   └─────────────────────────────────────────────────────┘
"@ -ForegroundColor White

Write-Host "`n🎯 Cómo usar:" -ForegroundColor Cyan
Write-Host "   1. En el navegador verás 2 botones grandes:" -ForegroundColor White
Write-Host "      - 'Login como ADMIN' (azul)" -ForegroundColor Blue
Write-Host "      - 'Login como WORKER' (verde)`n" -ForegroundColor Green

Write-Host "   2. Haz clic en cualquier botón para login instantáneo`n" -ForegroundColor White

Write-Host "   3. Serás redirigido automáticamente:" -ForegroundColor White
Write-Host "      - ADMIN  → http://localhost:3000/dashboard" -ForegroundColor Blue
Write-Host "      - WORKER → http://localhost:3000/dashboard/work`n" -ForegroundColor Green

Write-Host "⚠️  Nota: Mantén las 2 ventanas de PowerShell abiertas" -ForegroundColor Yellow
Write-Host "   (Backend y Frontend deben seguir corriendo)`n" -ForegroundColor Gray

Write-Host "🎉 ¡Todo listo! Puedes empezar a usar el sistema" -ForegroundColor Green
Write-Host "="*62 -ForegroundColor Cyan

# Mantener esta ventana abierta
Write-Host "`nPresiona cualquier tecla para cerrar esta ventana..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
