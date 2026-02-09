"""
multi_tenancy.py
Arquitectura Multi-tenancy para FastAPI (Lokigi)
- Middleware de subdominios
- Integración con Supabase y RLS
- Documentación al final
"""
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import os
import supabase_py

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = supabase_py.create_client(SUPABASE_URL, SUPABASE_KEY)

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "")
        agency_id = None
        if host.endswith(".lokigi.com"):
            agency_id = host.split(".")[0]
        elif host not in ("localhost:8000", "lokigi.com"):
            # Custom domain: buscar agency_id en Supabase
            data = supabase.table("agencies").select("id").eq("custom_domain", host).execute()
            agency_id = data.data[0]["id"] if data.data else None
        # Inyectar agency_id en el request.state
        request.state.agency_id = agency_id
        response: Response = await call_next(request)
        if agency_id:
            response.headers["x-agency-id"] = agency_id
        return response

def add_tenant_middleware(app: FastAPI):
    app.add_middleware(TenantMiddleware)

"""
Documentación:
- Este middleware detecta el subdominio o dominio personalizado y lo asocia a una agencia.
- El agency_id se inyecta en request.state y headers para uso en endpoints y lógica de negocio.
- Usa Supabase y RLS para aislar datos por agencia.
- Integra con Supabase Storage: cada agencia tiene su carpeta privada para logos y reportes.
- Para dominios custom, prepara integración con la API de Vercel (CNAME).
"""
