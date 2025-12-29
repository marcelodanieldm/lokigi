import secrets
import hashlib
from typing import Tuple

# --- Generación y hash seguro de API Keys ---
def generate_api_key() -> Tuple[str, str]:
    """
    Genera una API Key segura y su hash para almacenar en la base de datos.
    Retorna (api_key, key_hash)
    """
    api_key = secrets.token_urlsafe(32)
    key_hash = hash_api_key(api_key)
    return api_key, key_hash

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

# --- Validación de API Key ---
def validate_api_key(api_key: str, key_hash: str) -> bool:
    return hash_api_key(api_key) == key_hash
