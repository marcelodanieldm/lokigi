# Lokigi - Local SEO Auditor 🚀

Sistema de auditoría automática de SEO Local usando IA para negocios en Google Maps.

## 🎯 Características

- Análisis automático de datos de Google Maps
- Consultor SEO Local agresivo powered by OpenAI
- Detección de 3 fallos críticos con impacto económico
- Score de visibilidad de 1 a 100
- API REST con FastAPI

## 🛠️ Instalación

1. **Clona el repositorio e instala dependencias:**

```bash
pip install -r requirements.txt
```

2. **Configura tu API Key de OpenAI:**

```bash
cp .env.example .env
# Edita .env y añade tu OPENAI_API_KEY
```

3. **Ejecuta el servidor:**

```bash
python main.py
```

O con uvicorn directamente:

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

## 📡 Endpoints

### GET `/audit/test`
Endpoint de prueba que simula datos de un negocio y genera un reporte automático.

**Respuesta:**
```json
{
  "success": true,
  "datos_analizados": {
    "nombre": "Restaurante El Sabor Local",
    "rating": 3.8,
    "numero_resenas": 47,
    "tiene_sitio_web": false,
    "fecha_ultima_foto": "2023-08-15"
  },
  "reporte": {
    "fallos_criticos": [
      {
        "titulo": "Fallo detectado",
        "descripcion": "Descripción del problema",
        "impacto_economico": "Pérdida estimada"
      }
    ],
    "score_visibilidad": 45
  },
  "timestamp": "2025-12-19T..."
}
```

### POST `/audit/custom`
Audita datos personalizados de un negocio.

**Body:**
```json
{
  "nombre": "Mi Negocio",
  "rating": 4.2,
  "numero_resenas": 120,
  "tiene_sitio_web": true,
  "fecha_ultima_foto": "2024-12-01"
}
```

### GET `/docs`
Documentación interactiva de la API (Swagger UI)

## 🧪 Prueba rápida

```bash
# Ejecuta el test
curl http://localhost:8000/audit/test
```

## 🔧 Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **OpenAI GPT-4**: Motor de análisis de SEO Local
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI de alto rendimiento

## 📝 Estructura del Proyecto

```
lokigi/
├── main.py              # Aplicación principal
├── requirements.txt     # Dependencias
├── .env.example        # Ejemplo de variables de entorno
└── README.md           # Este archivo
```

## 🚀 Próximas Funcionalidades

- [ ] Integración real con Google Maps API
- [ ] Base de datos para historial de auditorías
- [ ] Dashboard web
- [ ] Notificaciones automáticas
- [ ] Comparativa con competidores

## 📄 Licencia

MIT
