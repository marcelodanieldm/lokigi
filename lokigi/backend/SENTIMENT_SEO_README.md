# SENTIMENT_SEO_README.md

# Algoritmo de Sentimiento y SEO en Reseñas

**Ubicación:** backend/sentiment_seo_reviews.py

## Objetivo
Extraer palabras clave de las reseñas de clientes y clasificar el sentimiento, para reinyectarlas en las respuestas de la IA y mejorar el SEO local en Google.

## Funcionalidades

- **Extracción de Keywords:**
  - Identifica las 5 frases/palabras clave más mencionadas en el corpus de reseñas.
  - Soporta n-gramas (frases de 2-3 palabras) y filtra términos triviales.

- **Análisis de Sentimiento:**
  - Clasifica reseñas en Positivas, Neutrales y Negativas.
  - Funciona nativamente en Español, Portugués e Inglés (sin traductores externos).

- **Prompt Engineering para IA Gemini:**
  - Genera un prompt que incluye las palabras clave detectadas para reforzar el SEO local en la respuesta de la IA.
  - El prompt se adapta al idioma detectado.

## Ejemplo de uso

```python
from sentiment_seo_reviews import extract_keywords, sentiment_analysis, build_gemini_prompt

corpus = [
    "La pizza crujiente y el servicio rápido me encantaron.",
    "Pizza crujiente, ambiente agradable.",
    "El servicio fue lento pero la pizza estaba deliciosa.",
    "No me gustó la pizza, pero el postre sí.",
    "Servicio rápido y pizza excelente."
]
lang = 'es'
keywords = extract_keywords(corpus)
sentiments = sentiment_analysis(corpus, lang)
prompt = build_gemini_prompt(keywords, lang)
print("Palabras clave:", keywords)
print("Sentimientos:", {k: len(v) for k, v in sentiments.items()})
print("Prompt para Gemini:", prompt)
```

## Requisitos
- Python 3.10+
- textblob (`pip install textblob`)

## Internacionalización
- El análisis de sentimiento y la extracción de keywords funcionan nativamente en español, portugués e inglés.
- No se utilizan traductores externos ni dependencias de pago.

---

**Autor:** Chief Data Scientist, Lokigi
**Fecha:** 2025-12-29
