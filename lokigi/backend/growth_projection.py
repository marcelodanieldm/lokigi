from typing import Dict, List

# --- Core Growth Projection Engine ---
def project_growth(initial_score: float, final_score: float, initial_metrics: Dict[str, float], final_metrics: Dict[str, float],
                   daily_revenue: float, currency: str = "USD") -> Dict:
    """
    Compara métricas antes/después y proyecta la ganancia para 6 meses.
    initial_score, final_score: 0-100
    initial_metrics, final_metrics: dict con claves [reputation, seo, visual, nap]
    daily_revenue: ingreso promedio diario
    currency: ARS, BRL, USD
    """
    # Proyección de visibilidad
    score_delta = max(final_score - initial_score, 0)
    visibility_gain_pct = min(score_delta * 1.2, 100)  # 1 punto score = 1.2% visibilidad
    # Proyección de ganancia
    projected_gain = daily_revenue * (visibility_gain_pct / 100) * 180
    # Ajuste de moneda
    currency_map = {"ARS": "$", "BRL": "R$", "USD": "$"}
    symbol = currency_map.get(currency, "$")
    # Dataset para radar chart
    radar_labels = ["Reputación", "SEO Local", "Contenido Visual", "Consistencia NAP"]
    radar_before = [initial_metrics.get(k, 0) for k in ["reputation", "seo", "visual", "nap"]]
    radar_after = [final_metrics.get(k, 0) for k in ["reputation", "seo", "visual", "nap"]]
    radar_data = {
        "labels": radar_labels,
        "datasets": [
            {"label": "Antes", "data": radar_before},
            {"label": "Después", "data": radar_after}
        ]
    }
    return {
        "visibility_gain_pct": round(visibility_gain_pct, 2),
        "projected_gain": round(projected_gain, 2),
        "currency": currency,
        "currency_symbol": symbol,
        "radar": radar_data
    }

# --- Ejemplo de uso ---
if __name__ == "__main__":
    initial = {"reputation": 60, "seo": 55, "visual": 50, "nap": 70}
    final = {"reputation": 80, "seo": 75, "visual": 85, "nap": 90}
    result = project_growth(
        initial_score=58,
        final_score=82,
        initial_metrics=initial,
        final_metrics=final,
        daily_revenue=120,
        currency="ARS"
    )
    print(result)
