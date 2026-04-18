"""
Script para mantener el servidor corriendo DEFINITIVAMENTE
"""
import sys
import signal
import asyncio
from contextlib import asynccontextmanager

# Deshabilitar KeyboardInterrupt automático
signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGTERM, signal.SIG_IGN)

print("="*60)
print("🚀 SERVIDOR LOKIGI - MODO PERSISTENTE")
print("="*60)

try:
    from main import app
    import uvicorn
    
    print("\n✅ App cargada correctamente")
    print(f"📊 {len(app.routes)} rutas registradas")
    
    print("\n🌐 Servidor iniciando en http://127.0.0.1:8000")
    print("📚 Documentación: http://127.0.0.1:8000/docs")
    print("\n🔐 Credenciales:")
    print("   • ADMIN: admin@lokigi.com / admin123")
    print("   • WORKER: worker@lokigi.com / worker123")
    print("\n⚠️  Para detener el servidor: Cierra esta ventana\n")
    print("="*60)
    
    # Configuración de uvicorn con keep-alive largo
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True,
        timeout_keep_alive=300,  # 5 minutos de keep-alive
        timeout_graceful_shutdown=10,
        limit_concurrency=1000,
        backlog=2048
    )
    
    server = uvicorn.Server(config)
    
    # Restaurar handlers de señales para que uvicorn pueda manejarlas
    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    
    # Ejecutar servidor de forma síncrona
    server.run()
    
except KeyboardInterrupt:
    print("\n\n✅ Servidor detenido manualmente")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n👋 Hasta luego!")
