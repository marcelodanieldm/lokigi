import os
from supabase import create_client, Client
from typing import Optional

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def upload_pdf_to_supabase(pdf_bytes: bytes, filename: str, bucket: str = "reports") -> Optional[str]:
    """
    Sube un archivo PDF a Supabase Storage y retorna la URL pública.
    """
    if not supabase:
        return None
    # Sube el archivo
    res = supabase.storage().from_(bucket).upload(filename, pdf_bytes, {"content-type": "application/pdf", "upsert": True})
    if res.get("error"):
        return None
    # Obtiene la URL pública
    public_url = supabase.storage().from_(bucket).get_public_url(filename)
    return public_url.get("publicURL") if public_url else None
