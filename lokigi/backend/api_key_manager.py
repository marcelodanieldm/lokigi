"""
API Key Management Endpoints
- Crear, revocar, listar y ver consumo de API Keys
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from supabase import create_client, Client
import os
from utils.api_key_utils import generate_api_key, hash_api_key

router = APIRouter()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

class ApiKeyCreateRequest(BaseModel):
    user_id: str
    label: str = None
    tier: str = "tier1"

@router.post("/api-keys/generate")
def create_api_key(data: ApiKeyCreateRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    api_key, key_hash = generate_api_key()
    res = supabase.table("api_keys").insert({
        "user_id": data.user_id,
        "key_hash": key_hash,
        "label": data.label,
        "tier": data.tier
    }).execute()
    if res.get("error"):
        raise HTTPException(status_code=500, detail="Error creating API Key")
    return {"api_key": api_key}

@router.get("/api-keys/list/{user_id}")
def list_api_keys(user_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    res = supabase.table("api_keys").select("id, label, is_active, created_at, usage_count, tier").eq("user_id", user_id).execute()
    return res.data

@router.post("/api-keys/revoke/{key_id}")
def revoke_api_key(key_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    res = supabase.table("api_keys").update({"is_active": False}).eq("id", key_id).execute()
    if res.get("error"):
        raise HTTPException(status_code=500, detail="Error revoking API Key")
    return {"status": "revoked"}
