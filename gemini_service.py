"""
Servicio de IA con Google Gemini (GRATIS)
Reemplaza OpenAI con Gemini que tiene límites gratuitos generosos
"""

import os
from typing import Optional, Dict, Any
import google.generativeai as genai
from audit_schemas import BusinessData, FODAAnalysis
from i18n_service import I18nService, Language


class GeminiAIService:
    """Servicio de IA usando Google Gemini (gratis)"""
    
    def __init__(self, language: Language = Language.ENGLISH):
        # Configurar Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.available = True
        else:
            self.model = None
            self.available = False
        
        self.i18n = I18nService(language)
    
    def is_available(self) -> bool:
        """Verifica si Gemini está disponible"""
        return self.available
    
    def generate_foda_analysis(
        self,
        business: BusinessData,
        score: int,
        competitors: list
    ) -> FODAAnalysis:
        """
        Genera análisis FODA usando Gemini
        Si Gemini no está disponible, usa análisis basado en reglas
        """
        if not self.available:
            return self._generate_foda_rule_based(business, score)
        
        try:
            # Preparar el prompt
            prompt = self._build_foda_prompt(business, score, competitors)
            
            # Generar con Gemini
            response = self.model.generate_content(prompt)
            
            # Parsear la respuesta
            return self._parse_foda_response(response.text)
            
        except Exception as e:
            print(f"Error con Gemini, usando análisis basado en reglas: {e}")
            return self._generate_foda_rule_based(business, score)
    
    def generate_detailed_analysis(
        self,
        business: BusinessData,
        score: int,
        critical_fix: str,
        economic_impact: str
    ) -> str:
        """Genera análisis detallado del negocio"""
        if not self.available:
            return self._generate_analysis_rule_based(business, score, critical_fix, economic_impact)
        
        try:
            prompt = self._build_analysis_prompt(business, score, critical_fix, economic_impact)
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error con Gemini: {e}")
            return self._generate_analysis_rule_based(business, score, critical_fix, economic_impact)
    
    def generate_action_plan(
        self,
        business: BusinessData,
        critical_fix: str
    ) -> list[str]:
        """Genera plan de acción priorizado"""
        if not self.available:
            return self._generate_action_plan_rule_based(business)
        
        try:
            prompt = self._build_action_plan_prompt(business, critical_fix)
            response = self.model.generate_content(prompt)
            
            # Parsear respuesta en lista
            lines = response.text.strip().split('\n')
            return [line.strip() for line in lines if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-'))]
            
        except Exception as e:
            print(f"Error con Gemini: {e}")
            return self._generate_action_plan_rule_based(business)
    
    # ========== PROMPT BUILDERS ==========
    
    def _build_foda_prompt(self, business: BusinessData, score: int, competitors: list) -> str:
        """Construye el prompt para análisis FODA"""
        lang_name = {
            Language.PORTUGUESE: "Português",
            Language.SPANISH: "Español",
            Language.ENGLISH: "English"
        }[self.i18n.language]
        
        return f"""Você é um consultor de SEO Local especializado em Google My Business.

Analise este negócio e gere um análisis FODA (SWOT) em {lang_name}:

NEGÓCIO:
- Nome: {business.name}
- Rating: {business.rating}/5
- Reseñas: {business.review_count}
- Website: {'Sí' if business.has_website else 'No'}
- Reclamado: {'Sí' if business.is_claimed else 'No'}
- Última foto: {business.last_photo_date}
- Score atual: {score}/100

COMPETIDORES:
{self._format_competitors(competitors)}

Gere um análisis FODA conciso (3-4 pontos por categoria) em {lang_name}.
Formato:
FORTALEZAS:
- [ponto 1]
- [ponto 2]

OPORTUNIDADES:
- [ponto 1]
- [ponto 2]

DEBILIDADES:
- [ponto 1]
- [ponto 2]

AMENAZAS:
- [ponto 1]
- [ponto 2]
"""
    
    def _build_analysis_prompt(self, business: BusinessData, score: int, critical_fix: str, economic_impact: str) -> str:
        """Construye el prompt para análisis detallado"""
        lang_name = {
            Language.PORTUGUESE: "Português",
            Language.SPANISH: "Español",
            Language.ENGLISH: "English"
        }[self.i18n.language]
        
        return f"""Você é um consultor de SEO Local que fala em termos de impacto económico.

Analise este negócio em {lang_name}:

DADOS:
- Nome: {business.name}
- Score: {score}/100
- Rating: {business.rating}/5
- Reseñas: {business.review_count}
- Problema crítico: {critical_fix}
- Impacto económico: {economic_impact}

Gere um análisis detalhado (2-3 parágrafos) em {lang_name} que:
1. Explique o estado atual do negócio
2. Identifique os maiores problemas
3. Explique o impacto em clientes perdidos
4. Motive à ação

Tom: Direto, baseado em dados, foca em dinheiro perdido.
"""
    
    def _build_action_plan_prompt(self, business: BusinessData, critical_fix: str) -> str:
        """Construye el prompt para plan de acción"""
        lang_name = {
            Language.PORTUGUESE: "Português",
            Language.SPANISH: "Español",
            Language.ENGLISH: "English"
        }[self.i18n.language]
        
        return f"""Gere um plano de ação priorizado para este negócio em {lang_name}:

DADOS:
- Nome: {business.name}
- Rating: {business.rating}/5
- Reseñas: {business.review_count}
- Website: {'Sí' if business.has_website else 'No'}
- Reclamado: {'Sí' if business.is_claimed else 'No'}
- Problema crítico: {critical_fix}

Gere 5-7 acciones priorizadas em {lang_name}.
Formato:
1. [Acción más urgente]
2. [Segunda acción]
...

Cada acción deve ser:
- Específica e accionável
- Com impacto económico claro
- Fácil de entender
"""
    
    def _format_competitors(self, competitors: list) -> str:
        """Formatea competidores para el prompt"""
        if not competitors:
            return "Sin datos de competidores"
        
        result = []
        for comp in competitors[:3]:
            result.append(f"- {comp.name}: {comp.rating}/5, {comp.review_count} reseñas")
        return "\n".join(result)
    
    # ========== FALLBACK: ANÁLISIS BASADO EN REGLAS ==========
    
    def _generate_foda_rule_based(self, business: BusinessData, score: int) -> FODAAnalysis:
        """Análisis FODA basado en reglas cuando Gemini no está disponible"""
        i18n = self.i18n
        
        fortalezas = []
        debilidades = []
        oportunidades = []
        amenazas = []
        
        # Fortalezas
        if business.rating >= 4.5:
            fortalezas.append("Excelente reputación online con rating superior a 4.5")
        if business.review_count >= 50:
            fortalezas.append(f"Gran cantidad de reseñas ({business.review_count}) genera confianza")
        if business.is_claimed:
            fortalezas.append("Negocio verificado y reclamado en Google")
        if business.has_website:
            fortalezas.append("Presencia web establecida con sitio propio")
        
        # Debilidades
        if not business.is_claimed:
            debilidades.append("Negocio NO reclamado - vulnerabilidad crítica")
        if business.rating < 4.0:
            debilidades.append(f"Rating bajo ({business.rating}) afecta conversiones")
        if business.review_count < 30:
            debilidades.append("Pocas reseñas limitan credibilidad")
        if not business.has_website:
            debilidades.append("Sin sitio web propio - pierdes conversiones")
        
        # Oportunidades
        if business.review_count < 50:
            oportunidades.append("Conseguir más reseñas puede mejorar visibilidad dramáticamente")
        if business.rating < 4.5:
            oportunidades.append("Mejora en servicio puede aumentar rating y CTR")
        oportunidades.append("Optimización de fotos y descripción puede atraer más clientes")
        oportunidades.append("Implementar estrategia de respuesta a reseñas")
        
        # Amenazas
        amenazas.append("Competidores con mejor optimización capturan tus clientes")
        if not business.is_claimed:
            amenazas.append("Información puede ser editada por terceros")
        amenazas.append("Algoritmo de Google favorece perfiles más completos")
        if business.rating < 3.5:
            amenazas.append("Rating bajo aleja al 78% de clientes potenciales")
        
        # Asegurar al menos 3 puntos por categoría
        if len(fortalezas) < 3:
            fortalezas.append("Potencial de crecimiento con optimizaciones básicas")
        if len(debilidades) < 3:
            debilidades.append("Espacio para mejora en visibilidad online")
        if len(oportunidades) < 3:
            oportunidades.append("Mercado local en crecimiento")
        if len(amenazas) < 3:
            amenazas.append("Cambios constantes en algoritmo de Google")
        
        return FODAAnalysis(
            fortalezas=fortalezas[:4],
            oportunidades=oportunidades[:4],
            debilidades=debilidades[:4],
            amenazas=amenazas[:4]
        )
    
    def _generate_analysis_rule_based(
        self,
        business: BusinessData,
        score: int,
        critical_fix: str,
        economic_impact: str
    ) -> str:
        """Análisis detallado basado en reglas"""
        
        if score >= 80:
            status = "excelente posición"
        elif score >= 60:
            status = "posición competitiva pero con espacio de mejora"
        elif score >= 40:
            status = "posición débil con problemas significativos"
        else:
            status = "situación crítica que requiere atención inmediata"
        
        analysis = f"""Su negocio '{business.name}' tiene un score de {score}/100, indicando una {status} en Google Maps.

{critical_fix}

{economic_impact}

La optimización de su perfil de Google My Business no es opcional - es dinero directo en su bolsillo. Cada día que pasa sin optimizar es dinero que va a sus competidores."""
        
        return analysis
    
    def _generate_action_plan_rule_based(self, business: BusinessData) -> list[str]:
        """Plan de acción basado en reglas"""
        actions = []
        
        if not business.is_claimed:
            actions.append(self.i18n.t("rec_claim_business"))
        
        if business.review_count < 30:
            actions.append(self.i18n.t("rec_get_reviews"))
        
        actions.append(self.i18n.t("rec_complete_profile"))
        actions.append(self.i18n.t("rec_upload_photos"))
        actions.append(self.i18n.t("rec_optimize_categories"))
        
        return actions[:7]
    
    def _parse_foda_response(self, text: str) -> FODAAnalysis:
        """Parsea la respuesta de Gemini en FODAAnalysis"""
        # Implementación simple - en producción mejorar parsing
        lines = text.strip().split('\n')
        
        fortalezas = []
        oportunidades = []
        debilidades = []
        amenazas = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_upper = line.upper()
            if 'FORTALEZA' in line_upper or 'STRENGTH' in line_upper or 'FORÇA' in line_upper:
                current_section = 'fortalezas'
            elif 'OPORTUNIDADE' in line_upper or 'OPPORTUNIT' in line_upper:
                current_section = 'oportunidades'
            elif 'DEBILIDAD' in line_upper or 'WEAKNESS' in line_upper or 'FRAQUEZA' in line_upper:
                current_section = 'debilidades'
            elif 'AMENAZA' in line_upper or 'THREAT' in line_upper or 'AMEAÇA' in line_upper:
                current_section = 'amenazas'
            elif line.startswith('-') or line.startswith('•'):
                point = line[1:].strip()
                if current_section == 'fortalezas':
                    fortalezas.append(point)
                elif current_section == 'oportunidades':
                    oportunidades.append(point)
                elif current_section == 'debilidades':
                    debilidades.append(point)
                elif current_section == 'amenazas':
                    amenazas.append(point)
        
        # Fallback si el parsing falla
        if not fortalezas and not debilidades:
            return self._generate_foda_rule_based(BusinessData(
                name="", rating=0, review_count=0, has_website=False,
                is_claimed=False, last_photo_date=""
            ), 50)
        
        return FODAAnalysis(
            fortalezas=fortalezas[:4] if fortalezas else ["N/A"],
            oportunidades=oportunidades[:4] if oportunidades else ["N/A"],
            debilidades=debilidades[:4] if debilidades else ["N/A"],
            amenazas=amenazas[:4] if amenazas else ["N/A"]
        )
