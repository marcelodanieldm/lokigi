"""
Servicio de análisis SEO Local - El Consultor de IA
Transforma datos técnicos en impacto económico real
Ahora con Google Gemini (GRATIS) y soporte i18n
"""

from datetime import datetime
from typing import List, Dict
import random
from audit_schemas import BusinessData, AuditResponse, FODAAnalysis, CompetitorData
from gemini_service import GeminiAIService
from i18n_service import I18nService, Language
import os
import json


class SEOLocalAnalyzer:
    """Consultor de SEO Local con IA (Gemini) que habla en términos de dinero"""
    
    def __init__(self, language: Language = Language.ENGLISH):
        # Usar Google Gemini (gratis) en lugar de OpenAI
        self.ai_service = GeminiAIService(language)
        self.i18n = I18nService(language)
        self.language = language
    
    def analyze(self, business: BusinessData, use_ai: bool = True) -> AuditResponse:
        """
        Analiza el negocio y genera reporte completo
        """
        # 1. Calcular score
        score = self._calculate_score(business)
        
        # 2. Identificar problema crítico
        critical_fix = self._identify_critical_fix(business)
        
        # 3. Calcular impacto económico
        economic_impact = self._calculate_economic_impact(business)
        
        # 4. Generar competidores simulados
        competitors = self._generate_competitors(business)
        
        # 5. Análisis FODA con Gemini (o reglas si no está disponible)
        if use_ai and self.ai_service.is_available():
            # Usar Gemini para análisis más sofisticado
            foda = self.ai_service.generate_foda_analysis(business, score, competitors)
            detailed_analysis = self.ai_service.generate_detailed_analysis(business, score, critical_fix, economic_impact)
            action_plan = self.ai_service.generate_action_plan(business, critical_fix)
        else:
            # Análisis basado en reglas (sin IA)
            foda = self._generate_foda_rule_based(business, score)
            detailed_analysis = self._generate_detailed_analysis_rule_based(business, score, critical_fix, economic_impact)
            action_plan = self._generate_action_plan_rule_based(business)
        
        return AuditResponse(
            score=score,
            critical_fix=critical_fix,
            economic_impact=economic_impact,
            foda=foda,
            competitors=competitors,
            detailed_analysis=detailed_analysis,
            action_plan=action_plan
        )
    
    def _calculate_score(self, business: BusinessData) -> int:
        """
        Calcula score de 0 a 100 basado en lógica de deducción de puntos
        """
        score = 100
        
        # Rating bajo (-30 puntos max)
        if business.rating < 3.0:
            score -= 30
        elif business.rating < 3.5:
            score -= 20
        elif business.rating < 4.0:
            score -= 10
        
        # Pocas reseñas (-25 puntos max)
        if business.review_count < 10:
            score -= 25
        elif business.review_count < 30:
            score -= 15
        elif business.review_count < 50:
            score -= 10
        elif business.review_count < 100:
            score -= 5
        
        # Sin sitio web (-20 puntos)
        if not business.has_website:
            score -= 20
        
        # Negocio no reclamado (-25 puntos) - CRÍTICO
        if not business.is_claimed:
            score -= 25
        
        # Fotos desactualizadas (-15 puntos max)
        days_since_photo = self._calculate_days_since_photo(business.last_photo_date)
        if days_since_photo > 365:
            score -= 15
        elif days_since_photo > 180:
            score -= 10
        elif days_since_photo > 90:
            score -= 5
        
        return max(0, min(100, score))
    
    def _calculate_days_since_photo(self, last_photo_date: str) -> int:
        """Calcula días desde la última foto"""
        try:
            photo_date = datetime.strptime(last_photo_date, "%Y-%m-%d")
            today = datetime.now()
            return (today - photo_date).days
        except:
            return 365  # Asumir 1 año si hay error
    
    def _identify_critical_fix(self, business: BusinessData) -> str:
        """
        Identifica el problema MÁS urgente a resolver (con i18n)
        """
        i18n = self.i18n
        
        if not business.is_claimed:
            return i18n.t("critical_fix_unclaimed")
        
        if not business.has_website:
            return i18n.t("critical_fix_no_website")
        
        if business.rating < 3.0:
            return i18n.t("critical_fix_low_rating")
        
        if business.review_count < 10:
            return i18n.t("critical_fix_few_reviews", business.review_count)
        
        days_since_photo = self._calculate_days_since_photo(business.last_photo_date)
        if days_since_photo > 365:
            return i18n.t("critical_fix_old_photos", days_since_photo)
        
        return i18n.t("critical_fix_general")
    
    def _calculate_economic_impact(self, business: BusinessData) -> str:
        """
        Transforma problemas técnicos en DINERO PERDIDO (con i18n)
        """
        i18n = self.i18n
        monthly_loss = 0
        loss_breakdown = []
        
        # Sin sitio web: -30% conversiones
        if not business.has_website:
            monthly_loss += 1800
            loss_breakdown.append(i18n.t("economic_impact_no_website", 1800))
        
        # No reclamado: -40% visibilidad
        if not business.is_claimed:
            monthly_loss += 2400
            loss_breakdown.append(i18n.t("economic_impact_unclaimed", 2400))
        
        # Rating bajo
        if business.rating < 3.5:
            monthly_loss += 1200
            loss_breakdown.append(i18n.t("economic_impact_low_rating", 1200))
        
        # Pocas reseñas
        if business.review_count < 30:
            monthly_loss += 900
            loss_breakdown.append(i18n.t("economic_impact_few_reviews", 900))
        
        # Fotos desactualizadas
        days_since_photo = self._calculate_days_since_photo(business.last_photo_date)
        if days_since_photo > 180:
            monthly_loss += 600
            loss_breakdown.append(i18n.t("economic_impact_old_photos", 600))
        
        if monthly_loss == 0:
            return i18n.t("economic_impact_good")
        
        annual_loss = monthly_loss * 12
        
        impact = i18n.t("economic_impact_losing", monthly_loss, annual_loss) + "\n\n"
        impact += i18n.t("economic_impact_breakdown") + "\n"
        for item in loss_breakdown:
            impact += f"• {item}\n"
        
        impact += f"\nEso son {monthly_loss // 50} clientes perdidos cada mes que van a tu competencia."
        
        return impact
    
    def _generate_competitors(self, business: BusinessData) -> List[CompetitorData]:
        """
        Genera 3 competidores simulados (en producción vendría de Google Places API)
        """
        base_names = [
            "Restaurante La Competencia",
            "Café Premium Zone",
            "Negocio Rival Pro",
            "Local Top Rated",
            "Business Elite Center"
        ]
        
        competitors = []
        for i in range(3):
            # Simular competidores mejores para motivar acción
            competitors.append(CompetitorData(
                name=base_names[i],
                rating=round(random.uniform(4.2, 4.8), 1),
                review_count=random.randint(120, 350),
                has_website=True,
                distance_km=round(random.uniform(0.5, 9.5), 1),
                estimated_monthly_revenue=f"${random.randint(15, 45):,}k"
            ))
        
        return competitors
    
    def _generate_foda_with_ai(self, business: BusinessData, score: int, competitors: List[CompetitorData]) -> FODAAnalysis:
        """
        Genera análisis FODA usando OpenAI
        """
        prompt = f"""Eres un consultor experto en Marketing Local y SEO. Analiza este negocio:

DATOS DEL NEGOCIO:
- Nombre: {business.name}
- Rating: {business.rating}/5.0
- Reseñas: {business.review_count}
- Sitio web: {"Sí" if business.has_website else "No"}
- Reclamado en Google: {"Sí" if business.is_claimed else "No"}
- Última foto: {business.last_photo_date}
- Score actual: {score}/100

COMPETENCIA (3 negocios en 10km):
{self._format_competitors(competitors)}

Genera un análisis FODA en JSON con este formato:
{{
    "fortalezas": ["punto 1", "punto 2", "punto 3"],
    "oportunidades": ["oportunidad 1", "oportunidad 2", "oportunidad 3"],
    "debilidades": ["debilidad 1", "debilidad 2", "debilidad 3"],
    "amenazas": ["amenaza 1", "amenaza 2"]
}}

Sé específico, habla en términos de dinero y clientes. Tono directo y agresivo."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un consultor de negocios experto en SEO Local que habla en términos de impacto económico."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            foda_dict = json.loads(response.choices[0].message.content)
            return FODAAnalysis(**foda_dict)
        except Exception as e:
            # Fallback a reglas
            return self._generate_foda_rule_based(business, score)
    
    def _generate_foda_rule_based(self, business: BusinessData, score: int) -> FODAAnalysis:
        """
        Genera FODA basado en reglas (sin IA)
        """
        fortalezas = []
        oportunidades = []
        debilidades = []
        amenazas = []
        
        # Fortalezas
        if business.rating >= 4.0:
            fortalezas.append(f"Rating sólido de {business.rating}/5.0 genera confianza")
        if business.review_count > 50:
            fortalezas.append(f"{business.review_count} reseñas te dan credibilidad")
        if business.is_claimed:
            fortalezas.append("Negocio reclamado: tienes control total de tu información")
        if business.has_website:
            fortalezas.append("Sitio web activo captura clientes que investigan")
        
        if not fortalezas:
            fortalezas.append("Presencia online existente: hay donde construir")
        
        # Oportunidades
        oportunidades.append("Aumentar reseñas 5 estrellas = +35% de conversión")
        oportunidades.append("Fotos profesionales recientes = +42% de clics")
        if not business.has_website:
            oportunidades.append("Lanzar sitio web captura $1,800/mes adicionales")
        oportunidades.append("Optimizar Google Business Profile = +200% visibilidad")
        
        # Debilidades
        if not business.is_claimed:
            debilidades.append("SIN RECLAMAR: Pierdes $2,400/mes en negocio robado")
        if not business.has_website:
            debilidades.append("Sin web: 30% de clientes potenciales van a competencia")
        if business.rating < 4.0:
            debilidades.append(f"Rating {business.rating} espanta al 60% de clientes")
        if business.review_count < 50:
            debilidades.append(f"Solo {business.review_count} reseñas: falta prueba social")
        
        days_since_photo = self._calculate_days_since_photo(business.last_photo_date)
        if days_since_photo > 180:
            debilidades.append(f"Fotos antiguas ({days_since_photo} días) = negocio muerto")
        
        # Amenazas
        amenazas.append("Competidores con mejor presencia online capturan TU mercado")
        amenazas.append("Clientes buscan alternativas si no encuentras información clara")
        if score < 50:
            amenazas.append("Score bajo te hace INVISIBLE en búsquedas locales")
        amenazas.append("Reseñas negativas sin respuesta destruyen reputación")
        
        return FODAAnalysis(
            fortalezas=fortalezas[:3],
            oportunidades=oportunidades[:3],
            debilidades=debilidades[:3],
            amenazas=amenazas[:2]
        )
    
    def _generate_detailed_analysis_with_ai(self, business: BusinessData, score: int, critical_fix: str) -> str:
        """
        Genera análisis detallado con OpenAI
        """
        prompt = f"""Eres un consultor experto en Marketing Local. Analiza este negocio y genera un reporte directo:

NEGOCIO: {business.name}
Score: {score}/100
Rating: {business.rating} ({business.review_count} reseñas)
Web: {"Sí" if business.has_website else "No"}
Reclamado: {"Sí" if business.is_claimed else "No"}

Problema Crítico Identificado:
{critical_fix}

Genera un análisis de 3-4 párrafos que:
1. Explique la situación actual en términos de DINERO perdido
2. Compare con competidores exitosos
3. Explique las consecuencias de no actuar
4. Motive a la acción inmediata

Tono: Directo, agresivo, basado en datos. Habla de dinero y clientes concretos."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un consultor de negocios que habla en términos de impacto económico real."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            
            return response.choices[0].message.content
        except:
            return self._generate_detailed_analysis_rule_based(business, score, critical_fix, "")
    
    def _generate_detailed_analysis_rule_based(self, business: BusinessData, score: int, critical_fix: str, economic_impact: str) -> str:
        """
        Genera análisis detallado sin IA
        """
        analysis = f"""**DIAGNÓSTICO DE {business.name.upper()}**

Tu negocio tiene un score de {score}/100 en presencia local. Esto NO es suficiente en 2025.

**LA REALIDAD DURA:**
{economic_impact}

**POR QUÉ ESTÁS PERDIENDO:**
Tus competidores directos tienen ratings de 4.5+, más de 200 reseñas, sitios web optimizados y actualizan contenido semanalmente. Mientras tú lees esto, ellos están capturando a TUS clientes potenciales.

**EL COSTO DE LA INACCIÓN:**
Cada mes que pasa sin optimizar tu presencia local, tu competencia se fortalece. Los clientes que no te encuentran o no confían en tu perfil van a otro lado. Y no vuelven.

**LO QUE DEBES HACER YA:**
{critical_fix}

El mercado local es una guerra. O atacas agresivamente tu visibilidad, o desapareces."""

        return analysis
    
    def _generate_action_plan_with_ai(self, business: BusinessData, critical_fix: str) -> List[str]:
        """
        Genera plan de acción con IA
        """
        prompt = f"""Genera un plan de acción de 5 pasos específicos y accionables para este negocio.

Problema crítico: {critical_fix}

Cada paso debe ser:
- Específico y accionable
- Con timeframe claro
- Explicando el impacto

Formato JSON: {{"action_plan": ["paso 1", "paso 2", ...]}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un consultor que genera planes de acción concretos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("action_plan", [])
        except:
            return self._generate_action_plan_rule_based(business)
    
    def _generate_action_plan_rule_based(self, business: BusinessData) -> List[str]:
        """
        Plan de acción basado en reglas
        """
        plan = []
        
        if not business.is_claimed:
            plan.append("PASO 1 (HOY): Reclama tu negocio en Google My Business. Toma 15 minutos.")
        
        if not business.has_website:
            plan.append("PASO 2 (Esta semana): Crea una landing page simple con tu info y CTA claro.")
        
        if business.review_count < 30:
            plan.append("PASO 3 (Próximos 7 días): Pide reseñas a tus 20 mejores clientes. Envía email/WhatsApp.")
        
        days_since_photo = self._calculate_days_since_photo(business.last_photo_date)
        if days_since_photo > 90:
            plan.append("PASO 4 (Este fin de semana): Toma 30 fotos profesionales de tu negocio, equipo y productos.")
        
        plan.append("PASO 5 (Próximas 2 semanas): Responde TODAS las reseñas (buenas y malas). Muestra que te importa.")
        
        return plan[:5]
    
    def _format_competitors(self, competitors: List[CompetitorData]) -> str:
        """Formatea competidores para prompt"""
        result = ""
        for i, comp in enumerate(competitors, 1):
            result += f"{i}. {comp.name}: {comp.rating}★ ({comp.review_count} reseñas), "
            result += f"Web: {'Sí' if comp.has_website else 'No'}, "
            result += f"{comp.distance_km}km, Revenue: {comp.estimated_monthly_revenue}\n"
        return result


# Instancia global del analizador
analyzer = SEOLocalAnalyzer()
