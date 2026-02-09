"""
Generador de PDF profesional para el Certificado de Éxito Lokigi.
Soporta ES, PT, EN. Usa ReportLab.
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
import io

def generate_success_certificate_pdf(data: dict, lang: str = "es") -> bytes:
    """
    data: {
        'name': str,
        'address': str,
        'final_score': float,
        'improvements': list,
        'photos': list,
        'ranking': list,
        'radar_labels': list,
        'radar_before': list,
        'radar_after': list
    }
    """
    texts = {
        "es": {
            "title": "Certificado de Éxito Lokigi",
            "score": "Score Final",
            "improvements": "Mejoras Realizadas",
            "photos": "Fotos Optimizadas con Geo-tag",
            "ranking": "Ranking de Competencia",
            "radar": "Tu Radar de Protección"
        },
        "pt": {
            "title": "Certificado de Sucesso Lokigi",
            "score": "Score Final",
            "improvements": "Melhorias Realizadas",
            "photos": "Fotos Otimizadas com Geo-tag",
            "ranking": "Ranking de Competidores",
            "radar": "Seu Radar de Proteção"
        },
        "en": {
            "title": "Lokigi Success Certificate",
            "score": "Final Score",
            "improvements": "Improvements",
            "photos": "Geo-tagged Optimized Photos",
            "ranking": "Competitor Ranking",
            "radar": "Your Protection Radar"
        }
    }
    t = texts.get(lang, texts["en"])
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    # Título
    c.setFillColor(colors.HexColor("#39FF14"))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height-40, t["title"])
    # Score
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.HexColor("#39FF14"))
    c.drawString(40, height-80, f"{t['score']}: {data.get('final_score','N/A')}")
    # Mejoras
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height-120, t["improvements"])
    c.setFont("Helvetica", 12)
    y = height-140
    for imp in data.get("improvements", []):
        c.drawString(60, y, f"- {imp}")
        y -= 16
    # Fotos
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y-10, t["photos"])
    c.setFont("Helvetica", 12)
    y -= 30
    for p in data.get("photos", []):
        c.drawString(60, y, f"Lat: {p.get('lat')}, Lon: {p.get('lon')}")
        y -= 14
    # Ranking
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y-10, t["ranking"])
    c.setFont("Helvetica", 12)
    y -= 30
    for i, r in enumerate(data.get("ranking", [])):
        c.drawString(60, y, f"{i+1}. {r.get('name')} - {r.get('score')}")
        y -= 14
    # Radar
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y-10, t["radar"])
    c.setFont("Helvetica", 12)
    y -= 30
    labels = data.get("radar_labels", [])
    before = data.get("radar_before", [])
    after = data.get("radar_after", [])
    for i, label in enumerate(labels):
        c.drawString(60, y, f"{label}: {before[i]} → {after[i]}")
        y -= 14
    c.save()
    return buffer.getvalue()
