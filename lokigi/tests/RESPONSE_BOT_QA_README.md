# RESPONSE_BOT_QA_README.md

# QA Automation: Bot de Respuestas

**Ubicación:** tests/test_response_bot_qa.py

## Objetivo
Asegurar que la IA nunca invente servicios, responda en el idioma correcto y soporte carga masiva de aprobaciones.

## Pruebas Incluidas

### 1. Test de Alucinaciones
- Verifica que la IA no mencione servicios/productos que no existen en la descripción del negocio (cruza con la DB simulada).

### 2. Test de Idioma
- Simula reseñas en Portugués y valida que la respuesta sea Portugués nativo (no Portuñol).

### 3. Test de Estrés de UI
- Simula la aprobación masiva de 50 reseñas en menos de 10 segundos para validar la robustez del backend y la cola de procesamiento.

## Ejecución
```bash
pytest tests/test_response_bot_qa.py
```

## Notas
- La DB de negocio es simulada para el test de alucinaciones.
- El test de idioma busca palabras típicas de español y portugués.
- El test de estrés puede ser adaptado para escenarios reales de concurrencia.

---

**Autor:** QA Automation, Lokigi
**Fecha:** 2025-12-29
