import redis
from fastapi import APIRouter

router = APIRouter()

@router.get("/health/redis")
def health_redis():
    try:
        r = redis.Redis.from_url("redis://localhost:6379/0", socket_connect_timeout=1)
        r.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
