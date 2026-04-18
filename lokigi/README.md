# Lokigi

Backend para integrar Google Business Profile con OAuth2, vincular una unica ubicacion por usuario y recibir webhooks de nuevas resenas para persistirlas en PostgreSQL.

## Estado actual

El repositorio contiene una base backend enfocada en estos flujos:

- OAuth2 con Google Business Profile
- Vinculacion de una sola `location_id` por usuario
- Recepcion de webhooks `NEW_REVIEW`
- Persistencia de resenas con integridad por `review_id`
- Cifrado de tokens OAuth en base de datos
- Migraciones Alembic para esquema productivo
- Flujo local para Windows PowerShell
- Artefactos de despliegue con Docker Compose y Caddy

## Stack

- Python 3
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Google OAuth / Google Business Profile APIs
- Docker Compose + Caddy para despliegue

## Estructura

```text
backend/
  app/
    config.py
    database.py
    google_client.py
    main.py
    models.py
    services.py
  alembic/
  deploy/
  scripts/
  sql/
  tests/
  LOCAL_DEV.md
  Dockerfile
  requirements.txt
```

## Endpoints

- `GET /health`
- `GET /oauth/google/start?user_id=<UUID>&location_id=<LOCATION_ID>`
- `GET /oauth/google/callback`
- `POST /webhooks/google/reviews`

## Reglas de negocio implementadas

- Un usuario solo puede vincular una ubicacion de Google Business Profile.
- Una `location_id` no puede quedar vinculada a mas de un usuario.
- Cada resena se guarda con unicidad por `review_id`.
- Si llega el mismo `review_id` con payload diferente, el backend responde conflicto `409`.
- El webhook valida bearer token OIDC de Google Pub/Sub.
- Puede usarse un secreto adicional por cabecera `X-Webhook-Secret` como defensa extra.

## Ejecucion local

### 1. Preparar variables

Usa `backend/.env` para desarrollo local. Ya existe una plantilla local funcional; solo debes completar:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

Si usas `ngrok`, actualiza tambien:

- `GOOGLE_REDIRECT_URI`
- `GOOGLE_PUBSUB_AUDIENCE`
- `ALLOWED_HOSTS`

### 2. Arranque rapido en Windows PowerShell

Desde `backend/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```

Ese script hace lo siguiente:

- instala dependencias
- ejecuta migraciones Alembic
- crea o reutiliza un usuario local `local@example.com`
- arranca Uvicorn en `http://localhost:8000`

### 3. Crear o recuperar un usuario local manualmente

```powershell
python .\scripts\create_local_user.py local@example.com
```

El comando imprime el `user_id` que luego puedes usar en el flujo OAuth.

## Pruebas locales de endpoints

### Healthcheck

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/health"
```

### Inicio de OAuth

```powershell
Invoke-WebRequest -Method Get -Uri "http://localhost:8000/oauth/google/start?user_id=<USER_ID>&location_id=<LOCATION_ID>" -MaximumRedirection 0
```

### Webhook sin credenciales reales

```powershell
Invoke-WebRequest -Method Post -Uri "http://localhost:8000/webhooks/google/reviews" -ContentType "application/json" -Body "{}"
```

Una respuesta `400` o `401` es esperable si no estas enviando autenticacion real de Pub/Sub.

## Uso con ngrok

Para probar callbacks reales de Google contra tu entorno local:

```powershell
ngrok http 8000
```

Con la URL publica de `ngrok`, actualiza `backend/.env` con:

- `GOOGLE_REDIRECT_URI=https://<NGROK_HOST>/oauth/google/callback`
- `GOOGLE_PUBSUB_AUDIENCE=https://<NGROK_HOST>/webhooks/google/reviews`
- `ALLOWED_HOSTS=localhost,127.0.0.1,<NGROK_HOST>`

Despues reinicia Uvicorn.

## Google Cloud

Para configurar OAuth client y Pub/Sub push correctamente, revisa:

- `backend/deploy/DEPLOYMENT.md`
- `backend/LOCAL_DEV.md`

Valores clave que deben coincidir exactamente con Google Cloud:

- `GOOGLE_REDIRECT_URI`
- `GOOGLE_PUBSUB_AUDIENCE`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

## Despliegue

El backend incluye despliegue productivo con Docker Compose y Caddy.

Desde `backend/` en un servidor Linux:

```bash
chmod +x deploy/deploy-prod.sh deploy/verify-post-deploy.sh
./deploy/deploy-prod.sh
```

Verificacion post-deploy:

```bash
./deploy/verify-post-deploy.sh
```

## Pruebas

Las pruebas de integracion viven en `backend/tests/integration/`.

Ejecucion:

```powershell
python -m pytest tests/integration -q --tb=no
```

Si Docker no esta disponible, esas pruebas quedan en `skipped` en lugar de fallar.

## Seguridad

- Tokens OAuth cifrados con Fernet
- `state` OAuth firmado
- Validacion de JWT OIDC para Pub/Sub push
- Restricciones de integridad en PostgreSQL
- `TrustedHostMiddleware` para hosts permitidos

## Archivos clave

- `backend/app/main.py`: API y endpoints
- `backend/app/services.py`: logica de OAuth, webhook e integridad
- `backend/app/models.py`: modelo de datos
- `backend/alembic/`: migraciones
- `backend/deploy/`: despliegue y verificacion
- `backend/scripts/`: utilidades locales
