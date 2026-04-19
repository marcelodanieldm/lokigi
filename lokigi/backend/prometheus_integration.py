# Ejemplo de integración Prometheus para FastAPI
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.routing import APIRoute

REQUEST_COUNT = Counter('fastapi_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'http_status'])

class PrometheusRoute(APIRoute):
    def get_route_handler(self):
        original_route_handler = super().get_route_handler()
        async def custom_route_handler(request: Request):
            response: Response = await original_route_handler(request)
            REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
            return response
        return custom_route_handler

def setup_prometheus(app):
    from fastapi import APIRouter
    router = APIRouter()
    @router.get("/metrics")
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    app.router.route_class = PrometheusRoute
    app.include_router(router)
