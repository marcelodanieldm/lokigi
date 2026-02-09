import os
import requests

def send_success_email(to_email: str, report_url: str, lang: str = "es") -> bool:
    """
    Envía un email de éxito con el enlace al reporte usando SendGrid (free tier).
    """
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
    FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@lokigi.com")
    if not SENDGRID_API_KEY:
        return False
    subjects = {
        "es": "¡Tu Certificado de Éxito Lokigi está listo!",
        "pt": "Seu Certificado de Sucesso Lokigi está pronto!",
        "en": "Your Lokigi Success Certificate is ready!"
    }
    bodies = {
        "es": f"Hola,\n\nTu reporte de impacto está listo. Descárgalo aquí: {report_url}\n\n¡Gracias por confiar en Lokigi!",
        "pt": f"Olá,\n\nSeu relatório de impacto está pronto. Baixe aqui: {report_url}\n\nObrigado por confiar na Lokigi!",
        "en": f"Hello,\n\nYour impact report is ready. Download it here: {report_url}\n\nThank you for trusting Lokigi!"
    }
    data = {
        "personalizations": [
            {"to": [{"email": to_email}], "subject": subjects.get(lang, subjects["en"])}
        ],
        "from": {"email": FROM_EMAIL},
        "content": [
            {"type": "text/plain", "value": bodies.get(lang, bodies["en"])}
        ]
    }
    resp = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        json=data
    )
    return resp.status_code == 202
