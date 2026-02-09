# REVIEW_RESPONSE_ENGINE_README.md

# Review Response Engine (Backend)

**Ubicación:** backend/review_response_engine.py

## Objetivo
Conectar reseñas de clientes con Gemini y devolver sugerencias de respuesta según tono y temperatura, asegurando acceso solo a usuarios WORKER o ADMIN.

## Endpoint
- **POST /worker/generate-replies**
  - **Body:**
    ```json
    {
      "reviews": ["La pizza estaba deliciosa...", "Great service!"],
      "temperature": 0.7,
      "tone": "Professional", // o "Casual", "Grateful"
      "lang": "es" // "en", "pt"
    }
    ```
  - **Response:**
    ```json
    {
      "suggestions": ["Respuesta profesional: Gracias por tu comentario sobre 'La pizza est...'"]
    }
    ```

## Seguridad
- Solo usuarios con rol WORKER o ADMIN (validado por Supabase/JWT) pueden acceder.

## Prompt Engineering
- El tono de la respuesta se ajusta según el parámetro `tone`.
- El parámetro `temperature` controla la creatividad (pasado a Gemini).


## Tests Automáticos
- Archivo: `tests/test_review_response_engine.py`
- Valida:
  - Seguridad: solo WORKER/ADMIN pueden acceder
  - Generación de sugerencias Gemini para lote de reseñas
  - Integración de tono y temperatura

Ejecuta:
```bash
pytest tests/test_review_response_engine.py
```

## Integración
- El router se importa y se incluye en el backend principal (`main.py`).

---

**Autor:** Full Stack Developer, Lokigi
**Fecha:** 2025-12-29
