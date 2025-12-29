"""
Data Scientist: Algoritmo de Sentimiento y SEO en Reseñas
--------------------------------------------------------
- Extrae las 5 palabras clave más frecuentes de las reseñas.
- Clasifica reseñas en Positivas, Neutrales y Negativas.
- Prepara prompt para IA Gemini, inyectando keywords para SEO local.
- Soporta español, portugués e inglés nativamente.
"""
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

from textblob import TextBlob
from textblob.exceptions import NotTranslated

# Idiomas soportados: 'es', 'pt', 'en'
LANGUAGE_POLARITY = {
    'es': {'pos': 0.2, 'neg': -0.2},
    'pt': {'pos': 0.2, 'neg': -0.2},
    'en': {'pos': 0.2, 'neg': -0.2},
}


def extract_keywords(reviews: List[str], top_n: int = 5) -> List[str]:
    """
    Extrae las top_n frases/palabras clave más frecuentes de las reseñas.
    """
    # Tokenización simple por frases de 1-3 palabras
    ngrams = []
    for review in reviews:
        tokens = re.findall(r'\w+', review.lower())
        for n in [2, 3, 1]:
            ngrams += [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
    # Filtrar ngrams triviales
    ngrams = [ng for ng in ngrams if len(ng.split()) > 1 or len(ng) > 4]
    most_common = Counter(ngrams).most_common(top_n)
    return [kw for kw, _ in most_common]


def sentiment_analysis(reviews: List[str], lang: str = 'es') -> Dict[str, List[str]]:
    """
    Clasifica reseñas en Positivas, Neutrales y Negativas usando TextBlob (multilenguaje).
    """
    result = defaultdict(list)
    for review in reviews:
        try:
            blob = TextBlob(review)
            polarity = blob.sentiment.polarity
        except NotTranslated:
            polarity = 0
        if polarity > LANGUAGE_POLARITY[lang]['pos']:
            result['Positivas'].append(review)
        elif polarity < LANGUAGE_POLARITY[lang]['neg']:
            result['Negativas'].append(review)
        else:
            result['Neutrales'].append(review)
    return result


def build_gemini_prompt(keywords: List[str], lang: str = 'es') -> str:
    """
    Construye el prompt para la IA Gemini, inyectando las palabras clave para reforzar SEO local.
    """
    if not keywords:
        return "Genera una respuesta personalizada para el cliente."
    if lang == 'es':
        return f"Incluye en la respuesta las siguientes palabras clave para SEO local: {', '.join(keywords)}."
    elif lang == 'pt':
        return f"Inclua na resposta as seguintes palavras-chave para SEO local: {', '.join(keywords)}."
    elif lang == 'en':
        return f"Include the following keywords for local SEO in your answer: {', '.join(keywords)}."
    else:
        return f"Include keywords: {', '.join(keywords)}."


if __name__ == "__main__":
    # Ejemplo de uso
    corpus = [
        "La pizza crujiente y el servicio rápido me encantaron.",
        "Pizza crujiente, ambiente agradable.",
        "El servicio fue lento pero la pizza estaba deliciosa.",
        "No me gustó la pizza, pero el postre sí.",
        "Servicio rápido y pizza excelente.",
    ]
    lang = 'es'
    keywords = extract_keywords(corpus)
    print("Palabras clave:", keywords)
    sentiments = sentiment_analysis(corpus, lang)
    print("Sentimientos:", {k: len(v) for k, v in sentiments.items()})
    prompt = build_gemini_prompt(keywords, lang)
    print("Prompt para Gemini:", prompt)
