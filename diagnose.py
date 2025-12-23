"""
Script de diagnóstico para encontrar el error que cierra el servidor
"""
import sys
import traceback

print("="*60)
print("🔍 DIAGNÓSTICO DEL SERVIDOR LOKIGI")
print("="*60)

try:
    print("\n1️⃣  Importando módulo main...")
    from main import app
    print("✅ main.app importado correctamente")
    
    print("\n2️⃣  Verificando configuración de la app...")
    print(f"   - App title: {app.title}")
    print(f"   - App version: {app.version}")
    print(f"   - Routers registrados: {len(app.routes)}")
    
    print("\n3️⃣  Intentando iniciar servidor uvicorn...")
    import uvicorn
    
    print("\n🚀 Iniciando servidor en http://127.0.0.1:8000")
    print("⚠️  Presiona CTRL+C para detener\n")
    
    uvicorn.run(
        app,  # Pasar el objeto app directamente, no el string
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
    
except KeyboardInterrupt:
    print("\n\n✅ Servidor detenido por el usuario")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERROR CAPTURADO:")
    print(f"   Tipo: {type(e).__name__}")
    print(f"   Mensaje: {str(e)}")
    print("\n📋 Traceback completo:")
    traceback.print_exc()
    sys.exit(1)
