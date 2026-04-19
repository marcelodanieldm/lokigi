

from backend.celery_app import celery
from loguru import logger
import ollama
import json

LLAMA_MODEL = "llama3"

PROMPT_TEMPLATE = """
Analiza la siguiente reseña y responde en JSON:\n- sentiment: float (-1=negativo, 0=neutral, 1=positivo)\n- entities: lista de entidades mencionadas (ej: comida, servicio, limpieza)\n- competitive_gaps: lista de brechas competitivas detectadas\n\nReseña:\n"""

@celery.task(name="tasks.ai_insights.run_ai")
def run_ai(data: dict):
    review_text = data.get("review_text", "")
    prompt = PROMPT_TEMPLATE + review_text
    try:
        response = ollama.chat(model=LLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        result = response["message"]["content"] if "message" in response else response["content"]
        analysis = json.loads(result)
    except Exception as e:
        logger.error(f"Ollama/Llama3 error: {e}, raw: {locals().get('result', '')}")
        analysis = {"sentiment": 0, "entities": [], "competitive_gaps": []}
    logger.success(f"[AIWorker] AI analysis: {analysis}")
    return analysis
