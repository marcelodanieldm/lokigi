"""
Email Service - Notificaciones por email usando SMTP gratuito
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from jinja2 import Template


class EmailService:
    """Servicio de envío de emails"""
    
    def __init__(self):
        # Configuración SMTP (usar Gmail, Mailgun, o Brevo/SendinBlue - GRATIS)
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "Lokigi SEO Team")
        
        # Verificar configuración
        self.is_configured = bool(self.smtp_user and self.smtp_password)
    
    def send_completion_email(
        self,
        to_email: str,
        client_name: str,
        business_name: str,
        score_before: int,
        score_after: Optional[int],
        changes_summary: str,
        report_url: Optional[str] = None,
        language: str = "es"
    ) -> bool:
        """
        Envía email de notificación cuando se completa una optimización
        """
        if not self.is_configured:
            print("⚠️ Email service not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
            return False
        
        try:
            # Generar HTML del email
            html_content = self._generate_completion_html(
                client_name=client_name,
                business_name=business_name,
                score_before=score_before,
                score_after=score_after or score_before + 15,  # Estimación conservadora
                changes_summary=changes_summary,
                report_url=report_url,
                language=language
            )
            
            # Configurar email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self._get_subject(language, business_name)
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Adjuntar HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Enviar via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def _get_subject(self, language: str, business_name: str) -> str:
        """Genera asunto del email según idioma"""
        subjects = {
            "es": f"✅ ¡{business_name} ha sido optimizado por Lokigi!",
            "pt": f"✅ {business_name} foi otimizado pela Lokigi!",
            "en": f"✅ {business_name} has been optimized by Lokigi!"
        }
        return subjects.get(language, subjects["es"])
    
    def _generate_completion_html(
        self,
        client_name: str,
        business_name: str,
        score_before: int,
        score_after: int,
        changes_summary: str,
        report_url: Optional[str],
        language: str
    ) -> str:
        """
        Genera HTML del email de finalización
        """
        # Template HTML multilingüe
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 20px auto;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #00ff41 0%, #00cc33 100%);
            padding: 40px 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            color: #0a0a0a;
            font-size: 28px;
            font-weight: bold;
        }
        .content {
            padding: 40px 30px;
        }
        .greeting {
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
        }
        .score-container {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            margin: 30px 0;
            text-align: center;
        }
        .score-row {
            display: flex;
            justify-content: space-around;
            align-items: center;
            margin: 20px 0;
        }
        .score-box {
            text-align: center;
        }
        .score-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .score-value {
            font-size: 36px;
            font-weight: bold;
            color: #00ff41;
        }
        .score-arrow {
            font-size: 32px;
            color: #00cc33;
        }
        .improvement {
            background: #00ff41;
            color: #0a0a0a;
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
            margin-top: 10px;
        }
        .changes-section {
            background: #f8f9fa;
            border-left: 4px solid #00ff41;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .changes-section h3 {
            margin-top: 0;
            color: #00cc33;
        }
        .cta-button {
            display: inline-block;
            background: #00ff41;
            color: #0a0a0a;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            margin: 20px 0;
        }
        .footer {
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }
        .footer a {
            color: #00cc33;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ header_title }}</h1>
        </div>
        
        <div class="content">
            <p class="greeting">{{ greeting }},</p>
            
            <p>{{ intro_text }}</p>
            
            <div class="score-container">
                <h3 style="margin-top:0; color:#333;">{{ score_title }}</h3>
                <div class="score-row">
                    <div class="score-box">
                        <div class="score-label">{{ before_label }}</div>
                        <div class="score-value" style="color:#ff6b6b;">{{ score_before }}/100</div>
                    </div>
                    <div class="score-arrow">→</div>
                    <div class="score-box">
                        <div class="score-label">{{ after_label }}</div>
                        <div class="score-value">{{ score_after }}/100</div>
                    </div>
                </div>
                <div class="improvement">
                    🚀 +{{ improvement }} {{ points_label }}
                </div>
            </div>
            
            <div class="changes-section">
                <h3>{{ changes_title }}</h3>
                <p>{{ changes_summary }}</p>
            </div>
            
            {% if report_url %}
            <div style="text-align: center;">
                <a href="{{ report_url }}" class="cta-button">{{ cta_text }}</a>
            </div>
            {% endif %}
            
            <p style="margin-top: 30px;">{{ next_steps_text }}</p>
            
            <p>{{ outro_text }}</p>
            <p style="margin-top: 20px;"><strong>Lokigi Team</strong><br>{{ tagline }}</p>
        </div>
        
        <div class="footer">
            <p>{{ footer_text }}</p>
            <p><a href="https://lokigi.com">lokigi.com</a> | <a href="mailto:support@lokigi.com">support@lokigi.com</a></p>
        </div>
    </div>
</body>
</html>
        """
        
        # Textos según idioma
        translations = {
            "es": {
                "header_title": f"✅ {business_name} Optimizado",
                "greeting": f"Hola {client_name}",
                "intro_text": f"¡Excelentes noticias! Hemos completado la optimización de <strong>{business_name}</strong> en Google My Business.",
                "score_title": "Mejora en Visibilidad Local",
                "before_label": "Antes",
                "after_label": "Después",
                "points_label": "puntos",
                "changes_title": "🔧 Cambios Realizados",
                "cta_text": "📊 Ver Reporte Completo",
                "next_steps_text": "Tu negocio ahora aparecerá mejor posicionado en las búsquedas locales de Google. Esto significa más clientes potenciales encontrando tu negocio.",
                "outro_text": "Si tienes alguna pregunta o necesitas asistencia adicional, no dudes en contactarnos.",
                "tagline": "SEO Local que genera resultados",
                "footer_text": "Este email fue enviado porque completamos la optimización de tu negocio en Google My Business."
            },
            "pt": {
                "header_title": f"✅ {business_name} Otimizado",
                "greeting": f"Olá {client_name}",
                "intro_text": f"Ótimas notícias! Concluímos a otimização de <strong>{business_name}</strong> no Google Meu Negócio.",
                "score_title": "Melhoria em Visibilidade Local",
                "before_label": "Antes",
                "after_label": "Depois",
                "points_label": "pontos",
                "changes_title": "🔧 Alterações Realizadas",
                "cta_text": "📊 Ver Relatório Completo",
                "next_steps_text": "Seu negócio agora aparecerá melhor posicionado nas buscas locais do Google. Isso significa mais clientes em potencial encontrando seu negócio.",
                "outro_text": "Se tiver alguma dúvida ou precisar de assistência adicional, não hesite em nos contatar.",
                "tagline": "SEO Local que gera resultados",
                "footer_text": "Este email foi enviado porque concluímos a otimização do seu negócio no Google Meu Negócio."
            },
            "en": {
                "header_title": f"✅ {business_name} Optimized",
                "greeting": f"Hi {client_name}",
                "intro_text": f"Great news! We've completed the optimization of <strong>{business_name}</strong> on Google My Business.",
                "score_title": "Local Visibility Improvement",
                "before_label": "Before",
                "after_label": "After",
                "points_label": "points",
                "changes_title": "🔧 Changes Made",
                "cta_text": "📊 View Full Report",
                "next_steps_text": "Your business will now rank better in local Google searches. This means more potential customers finding your business.",
                "outro_text": "If you have any questions or need additional assistance, don't hesitate to contact us.",
                "tagline": "Local SEO that generates results",
                "footer_text": "This email was sent because we completed the optimization of your business on Google My Business."
            }
        }
        
        texts = translations.get(language, translations["es"])
        improvement = score_after - score_before
        
        # Renderizar template
        template = Template(template_str)
        return template.render(
            **texts,
            score_before=score_before,
            score_after=score_after,
            improvement=improvement,
            changes_summary=changes_summary,
            report_url=report_url
        )


# Instancia global
email_service = EmailService()
