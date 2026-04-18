# Guía de Setup - Lokigi

## 🚀 Setup Completo (15 minutos)

### 1. Backend Setup

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Editar .env y añadir:
# OPENAI_API_KEY=sk-...
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...

# 4. Iniciar backend
python main.py
```

✅ Backend corriendo en `http://localhost:8000`

### 2. Frontend Setup

```bash
# 1. Entrar a la carpeta frontend
cd frontend

# 2. Instalar dependencias
npm install

# 3. Iniciar desarrollo
npm run dev
```

✅ Frontend corriendo en `http://localhost:3000`

### 3. Stripe Setup

#### Opción A: Testing sin webhook (rápido)
```bash
# Usa las test keys de Stripe Dashboard
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_dummy  # Dummy para testing
```

#### Opción B: Con webhook local (completo)
```bash
# 1. Instalar Stripe CLI
# Windows: scoop install stripe
# Mac: brew install stripe/stripe-cli/stripe

# 2. Login
stripe login

# 3. Forward webhooks
stripe listen --forward-to localhost:8000/api/stripe/webhook

# 4. Copiar webhook secret que aparece
# whsec_... → .env
```

### 4. Test del Flujo Completo

1. **Abrir** `http://localhost:3000`
2. **Rellenar** formulario con datos de prueba
3. **Ver auditoría** generada
4. **Click** en "Arreglar por $9" (si score < 50)
5. **Usar tarjeta** de prueba: `4242 4242 4242 4242`
6. **Confirmar** pago → Redirect a `/success`

## 🗄️ Base de Datos

La base de datos SQLite se crea automáticamente en `lokigi.db` al iniciar el backend.

### Ver datos
```bash
# Instalar sqlite3 (si no lo tienes)
# Windows: incluido
# Mac: brew install sqlite

# Abrir DB
sqlite3 lokigi.db

# Ver leads
SELECT * FROM leads;

# Ver estructura
.schema leads
```

### Reset DB
```bash
# Borrar y recrear
rm lokigi.db
python main.py  # Se recrea automáticamente
```

## 🧪 Testing

### Test Backend API
```bash
# Crear lead
curl -X POST http://localhost:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "telefono": "+34612345678",
    "nombre_negocio": "Restaurante Test"
  }'

# Obtener auditoría (usa el ID del response anterior)
curl http://localhost:8000/api/leads/1/audit
```

### Test Stripe
```bash
# Tarjetas de prueba
✅ Éxito: 4242 4242 4242 4242
❌ Declined: 4000 0000 0000 0002
```

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY not found"
```bash
# Asegúrate que .env existe y tiene la key
cat .env  # Linux/Mac
type .env  # Windows

# Si no existe
cp .env.example .env
# Editar y añadir la key
```

### Error: "Module not found"
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### Error: CORS en frontend
```bash
# Verifica que el backend tenga CORS configurado en main.py
# allow_origins=["http://localhost:3000"]
```

### Base de datos locked
```bash
# Matar procesos Python
# Windows: taskkill /F /IM python.exe
# Mac/Linux: killall python

# Borrar DB y reiniciar
rm lokigi.db
python main.py
```

## 📊 Monitoreo

### Ver logs backend
```bash
# El servidor muestra logs en consola
# Ctrl+C para detener
```

### Ver requests
```bash
# Abrir http://localhost:8000/docs
# Swagger UI interactivo
```

### Ver DB en tiempo real
```bash
# Instalar DB Browser for SQLite
# https://sqlitebrowser.org/
# Abrir lokigi.db
```

## 🚀 Deploy

### Backend (Railway/Render)
```bash
# 1. Cambiar DATABASE_URL en .env a PostgreSQL
DATABASE_URL=postgresql://...

# 2. Añadir variables de entorno en plataforma
OPENAI_API_KEY=...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...

# 3. Deploy
git push
```

### Frontend (Vercel)
```bash
# 1. Instalar Vercel CLI
npm i -g vercel

# 2. Deploy
cd frontend
vercel

# 3. Actualizar CORS en backend con URL de producción
```

## ✅ Checklist Pre-Deploy

- [ ] .env configurado con todas las keys
- [ ] Base de datos en producción (PostgreSQL)
- [ ] Stripe webhooks configurados con URL pública
- [ ] CORS actualizado con dominio de producción
- [ ] Email transaccional configurado (SendGrid/Mailgun)
- [ ] Backup automático de DB
- [ ] Monitoring (Sentry/DataDog)

---

¿Problemas? Abre un issue en GitHub o contacta al equipo.
