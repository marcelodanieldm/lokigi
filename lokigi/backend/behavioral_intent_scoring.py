"""
Behavioral Intent Scoring Model for Lokigi
Chief Data Scientist Implementation

Objetivo: Calcular el score de intención de compra de un lead basado en su interacción con el reporte gratuito.

Entradas:
- tiempo_permanencia (float): Tiempo total en minutos que el usuario pasó en el reporte.
- num_clicks_competencia (int): Número de clics en la comparativa de competencia.
- descargo_pdf (bool): Si el usuario descargó el PDF gratuito.
- vistas_reporte (int): Número de veces que el usuario abrió el reporte en la última hora.
- ultima_compra (datetime | None): Fecha/hora de la última compra (None si no ha comprado).
- ultima_interaccion (datetime): Última vez que interactuó con el reporte.
- seccion_mas_vista (str): Sección donde pasó más tiempo ("heatmap", "comparativa", "alertas", etc).

Salidas:
- score (0-100): Nivel de intención de compra.
- alerta (bool): Si debe dispararse alerta de intención alta.
- motivo_alerta (str): Motivo personalizado según sección más vista.
- generar_cupon (bool): Si debe generarse cupón de descuento.
- descuento (float): Porcentaje de descuento (si aplica).
- expiracion_cupon (datetime): Fecha/hora de expiración del cupón (si aplica).

"""
from datetime import datetime, timedelta

def behavioral_intent_score(
    tiempo_permanencia: float,
    num_clicks_competencia: int,
    descargo_pdf: bool,
    vistas_reporte: int,
    ultima_compra: datetime | None,
    ultima_interaccion: datetime,
    seccion_mas_vista: str,
    ahora: datetime = None
):
    """
    Calcula el score de intención y acciones asociadas.
    """
    if ahora is None:
        ahora = datetime.utcnow()

    # Score base
    score = 0
    score += min(tiempo_permanencia, 30) * 1.5   # Máx 45 pts
    score += min(num_clicks_competencia, 10) * 3 # Máx 30 pts
    score += 10 if descargo_pdf else 0           # 10 pts
    score += min(vistas_reporte, 5) * 3          # Máx 15 pts
    score = min(score, 100)

    # Alerta de intención alta
    alerta = False
    motivo_alerta = ""
    if score > 80 and vistas_reporte >= 2 and (ahora - ultima_interaccion).total_seconds() < 3600:
        alerta = True
        motivos = {
            "heatmap": "Interés alto en visibilidad geográfica de tu negocio.",
            "comparativa": "Interés en comparativa con la competencia.",
            "alertas": "Atención a alertas de oportunidad.",
            "pdf": "Descargó el reporte para análisis detallado.",
        }
        motivo_alerta = motivos.get(seccion_mas_vista, "Interacción destacada en el reporte.")

    # Lógica de cupón de descuento
    generar_cupon = False
    descuento = 0.0
    expiracion_cupon = None
    if score > 80 and (ultima_compra is None or (ahora - ultima_compra).total_seconds() > 86400):
        # No compró en 24h tras score alto
        generar_cupon = True
        descuento = 15.0
        expiracion_cupon = ahora + timedelta(hours=4)

    return {
        "score": round(score, 2),
        "alerta": alerta,
        "motivo_alerta": motivo_alerta,
        "generar_cupon": generar_cupon,
        "descuento": descuento,
        "expiracion_cupon": expiracion_cupon,
    }

# Ejemplo de uso
if __name__ == "__main__":
    resultado = behavioral_intent_score(
        tiempo_permanencia=18.5,
        num_clicks_competencia=7,
        descargo_pdf=True,
        vistas_reporte=3,
        ultima_compra=None,
        ultima_interaccion=datetime.utcnow(),
        seccion_mas_vista="heatmap"
    )
    print("Resultado scoring:", resultado)
