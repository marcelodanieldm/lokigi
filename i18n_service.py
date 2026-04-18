"""
Servicio de Internacionalización (i18n)
Traducciones para PT, ES, EN
"""

from typing import Dict, Any
from ip_geolocation import Language


class I18nService:
    """Servicio de traducciones"""
    
    # Traducciones organizadas por idioma
    TRANSLATIONS = {
        Language.PORTUGUESE: {
            # Análisis general
            "critical_fix_unclaimed": "🚨 URGENTE: Seu negócio NÃO está reivindicado no Google. Qualquer pessoa pode editar suas informações e roubar clientes. Reivindique HOJE.",
            "critical_fix_no_website": "🌐 CRÍTICO: Sem site você perde 30% das conversões. Clientes buscam mais informações e vão para a concorrência.",
            "critical_fix_low_rating": "⭐ ALERTA VERMELHO: Avaliação abaixo de 3.0 afasta 78% dos clientes potenciais. Melhore sua reputação JÁ.",
            "critical_fix_few_reviews": "💬 PROBLEMA: Você tem apenas {} avaliações. Negócios com +50 avaliações têm 270% mais cliques.",
            "critical_fix_old_photos": "📸 ABANDONADO: Sua última foto tem {} dias. Negócios com fotos recentes obtêm 42% mais cliques.",
            "critical_fix_general": "📊 Otimização Geral: Melhoria contínua em todas as frentes para superar a concorrência.",
            
            # Impacto económico
            "economic_impact_losing": "💸 VOCÊ ESTÁ PERDENDO ${:,}/mês (${:,}/ano)",
            "economic_impact_breakdown": "Detalhamento:",
            "economic_impact_no_website": "${:,}/mês por falta de site",
            "economic_impact_unclaimed": "${:,}/mês por não reivindicar seu negócio",
            "economic_impact_low_rating": "${:,}/mês por avaliação baixa",
            "economic_impact_few_reviews": "${:,}/mês por falta de avaliações",
            "economic_impact_old_photos": "${:,}/mês por fotos desatualizadas",
            "economic_impact_clients_lost": "São {} clientes perdidos a cada mês que vão para sua concorrência.",
            "economic_impact_good": "✅ Bom trabalho. Perdas mínimas estimadas. Mantenha o ritmo.",
            
            # FODA
            "foda_strengths": "Fortalezas",
            "foda_opportunities": "Oportunidades",
            "foda_weaknesses": "Fraquezas",
            "foda_threats": "Ameaças",
            
            # Problemas críticos
            "issue_unclaimed": "🚨 CRÍTICO: Negócio NÃO REIVINDICADO - Qualquer pessoa pode editar suas informações. Isso está custando 40% da sua visibilidade.",
            "issue_low_rating": "⭐ CRÍTICO: Avaliação de {:.1f} afasta 78% dos clientes. Prioridade #1: melhorar reputação.",
            "issue_few_reviews": "💬 URGENTE: Apenas {} avaliações. Negócios com +50 avaliações recebem 270% mais cliques.",
            "issue_incomplete_nap": "📍 IMPORTANTE: Informações de contato incompletas (NAP). Você perde credibilidade e conversões.",
            "issue_no_category": "🏷️ IMPORTANTE: Você não tem categoria principal definida. O Google não sabe quando mostrá-lo nas buscas.",
            "issue_old_photos": "📸 Fotos desatualizadas ({} dias). Negócios com fotos recentes obtêm 42% mais engajamento.",
            "issue_no_hours": "🕐 Horários não configurados. Clientes não sabem quando visitá-lo.",
            
            # Recomendaciones
            "rec_claim_business": "1️⃣ AÇÃO IMEDIATA: Reivindique seu negócio no Google My Business. Isso leva apenas 5 minutos e aumenta sua visibilidade em 40%.",
            "rec_get_reviews": "2️⃣ URGENTE: Implemente um sistema para pedir avaliações. Objetivo: conseguir 3-5 avaliações novas por semana.",
            "rec_complete_profile": "3️⃣ PRIORIDADE: Complete seu perfil com telefone, endereço e horários corretos.",
            "rec_upload_photos": "4️⃣ Esta semana: Carregue 10 fotos profissionais (produtos, local, equipe). Atualize fotos a cada mês.",
            "rec_optimize_categories": "5️⃣ Otimize categorias: Defina sua categoria principal e adicione 2-3 secundárias relevantes.",
            "rec_potential": "🚀 POTENCIAL: Você pode subir {} posições no ranking implementando essas melhorias em 30-60 dias.",
            
            # Score labels
            "score_excellent": "🌟 Excelente",
            "score_good": "✅ Bom",
            "score_regular": "⚠️ Regular",
            "score_critical": "🔴 Crítico",
            "score_emergency": "🚨 Emergência",
            
            # Dimensiones
            "dimension_nap": "NAP (Nome, Endereço, Telefone)",
            "dimension_reviews": "Avaliações",
            "dimension_photos": "Fotos",
            "dimension_categories": "Categorias",
            "dimension_verification": "Verificação",
        },
        
        Language.SPANISH: {
            # Análisis general
            "critical_fix_unclaimed": "🚨 URGENTE: Tu negocio NO está reclamado en Google. Cualquiera puede editar tu información y robar clientes. Reclámalo HOY.",
            "critical_fix_no_website": "🌐 CRÍTICO: Sin sitio web pierdes el 30% de conversiones. Clientes buscan más info y van a la competencia.",
            "critical_fix_low_rating": "⭐ ALERTA ROJA: Rating por debajo de 3.0 espanta al 78% de clientes potenciales. Mejora tu reputación YA.",
            "critical_fix_few_reviews": "💬 PROBLEMA: Solo tienes {} reseñas. Negocios con +50 reseñas tienen 270% más clics.",
            "critical_fix_old_photos": "📸 ABANDONADO: Tu última foto tiene {} días. Negocios con fotos recientes obtienen 42% más clics.",
            "critical_fix_general": "📊 Optimización General: Mejora continua en todos los frentes para superar a la competencia.",
            
            # Impacto económico
            "economic_impact_losing": "💸 ESTÁS PERDIENDO ${:,}/mes (${:,}/año)",
            "economic_impact_breakdown": "Desglose:",
            "economic_impact_no_website": "${:,}/mes por falta de sitio web",
            "economic_impact_unclaimed": "${:,}/mes por no reclamar tu negocio",
            "economic_impact_low_rating": "${:,}/mes por rating bajo",
            "economic_impact_few_reviews": "${:,}/mes por falta de reseñas",
            "economic_impact_old_photos": "${:,}/mes por fotos desactualizadas",
            "economic_impact_clients_lost": "Eso son {} clientes perdidos cada mes que van a tu competencia.",
            "economic_impact_good": "✅ Buen trabajo. Pérdidas mínimas estimadas. Mantén el momentum.",
            
            # FODA
            "foda_strengths": "Fortalezas",
            "foda_opportunities": "Oportunidades",
            "foda_weaknesses": "Debilidades",
            "foda_threats": "Amenazas",
            
            # Problemas críticos
            "issue_unclaimed": "🚨 CRÍTICO: Negocio NO RECLAMADO - Cualquiera puede editar tu información. Esto te está costando el 40% de tu visibilidad.",
            "issue_low_rating": "⭐ CRÍTICO: Rating de {:.1f} espanta al 78% de clientes. Prioridad #1: mejorar reputación.",
            "issue_few_reviews": "💬 URGENTE: Solo {} reseñas. Negocios con +50 reseñas reciben 270% más clics.",
            "issue_incomplete_nap": "📍 IMPORTANTE: Información de contacto incompleta (NAP). Pierdes credibilidad y conversiones.",
            "issue_no_category": "🏷️ IMPORTANTE: No tienes categoría principal definida. Google no sabe cuándo mostrarte en búsquedas.",
            "issue_old_photos": "📸 Fotos desactualizadas ({} días). Negocios con fotos recientes obtienen 42% más engagement.",
            "issue_no_hours": "🕐 Horarios no configurados. Clientes no saben cuándo visitarte.",
            
            # Recomendaciones
            "rec_claim_business": "1️⃣ ACCIÓN INMEDIATA: Reclama tu negocio en Google My Business. Esto solo toma 5 minutos y aumenta tu visibilidad un 40%.",
            "rec_get_reviews": "2️⃣ URGENTE: Implementa un sistema para pedir reseñas. Objetivo: conseguir 3-5 reseñas nuevas por semana.",
            "rec_complete_profile": "3️⃣ PRIORIDAD: Completa tu perfil con teléfono, dirección y horarios correctos.",
            "rec_upload_photos": "4️⃣ Esta semana: Sube 10 fotos profesionales (productos, local, equipo). Actualiza fotos cada mes.",
            "rec_optimize_categories": "5️⃣ Optimiza categorías: Define tu categoría principal y agrega 2-3 secundarias relevantes.",
            "rec_potential": "🚀 POTENCIAL: Puedes subir {} posiciones en el ranking implementando estas mejoras en 30-60 días.",
            
            # Score labels
            "score_excellent": "🌟 Excelente",
            "score_good": "✅ Bueno",
            "score_regular": "⚠️ Regular",
            "score_critical": "🔴 Crítico",
            "score_emergency": "🚨 Emergencia",
            
            # Dimensiones
            "dimension_nap": "NAP (Nombre, Dirección, Teléfono)",
            "dimension_reviews": "Reseñas",
            "dimension_photos": "Fotos",
            "dimension_categories": "Categorías",
            "dimension_verification": "Verificación",
        },
        
        Language.ENGLISH: {
            # General analysis
            "critical_fix_unclaimed": "🚨 URGENT: Your business is NOT claimed on Google. Anyone can edit your information and steal customers. Claim it TODAY.",
            "critical_fix_no_website": "🌐 CRITICAL: Without a website you lose 30% of conversions. Customers look for more info and go to competitors.",
            "critical_fix_low_rating": "⭐ RED ALERT: Rating below 3.0 scares away 78% of potential customers. Improve your reputation NOW.",
            "critical_fix_few_reviews": "💬 PROBLEM: You only have {} reviews. Businesses with +50 reviews get 270% more clicks.",
            "critical_fix_old_photos": "📸 ABANDONED: Your last photo is {} days old. Businesses with recent photos get 42% more clicks.",
            "critical_fix_general": "📊 General Optimization: Continuous improvement on all fronts to beat the competition.",
            
            # Economic impact
            "economic_impact_losing": "💸 YOU ARE LOSING ${:,}/month (${:,}/year)",
            "economic_impact_breakdown": "Breakdown:",
            "economic_impact_no_website": "${:,}/month for lack of website",
            "economic_impact_unclaimed": "${:,}/month for not claiming your business",
            "economic_impact_low_rating": "${:,}/month for low rating",
            "economic_impact_few_reviews": "${:,}/month for lack of reviews",
            "economic_impact_old_photos": "${:,}/month for outdated photos",
            "economic_impact_clients_lost": "That's {} customers lost every month going to your competition.",
            "economic_impact_good": "✅ Good work. Minimal estimated losses. Keep the momentum.",
            
            # SWOT
            "foda_strengths": "Strengths",
            "foda_opportunities": "Opportunities",
            "foda_weaknesses": "Weaknesses",
            "foda_threats": "Threats",
            
            # Critical issues
            "issue_unclaimed": "🚨 CRITICAL: Business NOT CLAIMED - Anyone can edit your information. This is costing you 40% of your visibility.",
            "issue_low_rating": "⭐ CRITICAL: Rating of {:.1f} scares away 78% of customers. Priority #1: improve reputation.",
            "issue_few_reviews": "💬 URGENT: Only {} reviews. Businesses with +50 reviews get 270% more clicks.",
            "issue_incomplete_nap": "📍 IMPORTANT: Incomplete contact information (NAP). You lose credibility and conversions.",
            "issue_no_category": "🏷️ IMPORTANT: You don't have a main category defined. Google doesn't know when to show you in searches.",
            "issue_old_photos": "📸 Outdated photos ({} days). Businesses with recent photos get 42% more engagement.",
            "issue_no_hours": "🕐 Hours not configured. Customers don't know when to visit you.",
            
            # Recommendations
            "rec_claim_business": "1️⃣ IMMEDIATE ACTION: Claim your business on Google My Business. This only takes 5 minutes and increases your visibility by 40%.",
            "rec_get_reviews": "2️⃣ URGENT: Implement a system to ask for reviews. Goal: get 3-5 new reviews per week.",
            "rec_complete_profile": "3️⃣ PRIORITY: Complete your profile with correct phone, address and hours.",
            "rec_upload_photos": "4️⃣ This week: Upload 10 professional photos (products, location, team). Update photos monthly.",
            "rec_optimize_categories": "5️⃣ Optimize categories: Define your main category and add 2-3 relevant secondary ones.",
            "rec_potential": "🚀 POTENTIAL: You can climb {} positions in the ranking by implementing these improvements in 30-60 days.",
            
            # Score labels
            "score_excellent": "🌟 Excellent",
            "score_good": "✅ Good",
            "score_regular": "⚠️ Regular",
            "score_critical": "🔴 Critical",
            "score_emergency": "🚨 Emergency",
            
            # Dimensions
            "dimension_nap": "NAP (Name, Address, Phone)",
            "dimension_reviews": "Reviews",
            "dimension_photos": "Photos",
            "dimension_categories": "Categories",
            "dimension_verification": "Verification",
        }
    }
    
    def __init__(self, language: Language = Language.ENGLISH):
        self.language = language
    
    def t(self, key: str, *args, **kwargs) -> str:
        """
        Traduce una key al idioma actual
        
        Usage:
            i18n = I18nService(Language.PORTUGUESE)
            text = i18n.t("critical_fix_unclaimed")
            text = i18n.t("critical_fix_few_reviews", 5)  # Con formato
        """
        translations = self.TRANSLATIONS.get(self.language, self.TRANSLATIONS[Language.ENGLISH])
        text = translations.get(key, key)
        
        # Aplicar formato si hay args
        if args:
            try:
                return text.format(*args)
            except:
                return text
        
        return text
    
    def set_language(self, language: Language):
        """Cambia el idioma actual"""
        self.language = language
    
    def get_language(self) -> Language:
        """Retorna el idioma actual"""
        return self.language


# Helper para crear instancia
def create_i18n_service(language: Language = Language.ENGLISH) -> I18nService:
    """Crea una instancia del servicio de i18n"""
    return I18nService(language)
