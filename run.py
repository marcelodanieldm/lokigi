"""
Script para ejecutar el servidor FastAPI de forma persistente
"""
if __name__ == "__main__":
    import uvicorn
    import sys
    
    print("🚀 Iniciando servidor Lokigi en http://127.0.0.1:8000")
    print("📋 Endpoints disponibles:")
    print("   - POST /api/auth/login - Login de usuarios")
    print("   - GET /docs - Documentación interactiva")
    print("\n⚠️  Presiona CTRL+C para detener el servidor\n")
    
    try:
        uvicorn.run(
            "main:app", 
            host="127.0.0.1", 
            port=8000, 
            reload=True,  # Auto-reload en desarrollo
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\n✅ Servidor detenido correctamente")
        sys.exit(0)
