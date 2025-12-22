"""
LOKIGI SCORE ALGORITHM v1.0
==============================
Algoritmo optimizado para presupuesto CERO con scraping manual
Analiza 5 dimensiones críticas de Google Maps + Cálculo de Lucro Cesante
Soporta Argentina, Brasil y Estados Unidos
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import re


class Country(Enum):
    """Países soportados con sus métricas locales"""
    ARGENTINA = "AR"
    BRASIL = "BR"
    EEUU = "US"


@dataclass
class NAP:
    """Name, Address, Phone - Dimensión 1"""
    name_complete: bool = False
    address_complete: bool = False
    phone_present: bool = False
    phone_format_valid: bool = False
    consistency_score: float = 0.0  # 0-1


@dataclass
class ReviewsMetrics:
    """Reseñas - Dimensión 2"""
    total_reviews: int = 0
    average_rating: float = 0.0
    recent_reviews_30d: int = 0
    review_response_rate: float = 0.0  # % de reseñas respondidas
    sentiment_score: float = 0.0  # 0-1


@dataclass
class PhotosMetrics:
    """Fotos - Dimensión 3"""
    total_photos: int = 0
    owner_photos: int = 0
    days_since_last_photo: int = 999
    photo_freshness_score: float = 0.0  # 0-1


@dataclass
class CategoryMetrics:
    """Categorías - Dimensión 4"""
    primary_category_set: bool = False
    additional_categories: int = 0
    category_relevance_score: float = 0.0  # 0-1


@dataclass
class VerificationMetrics:
    """Verificación - Dimensión 5"""
    is_claimed: bool = False
    is_verified: bool = False
    google_guaranteed: bool = False
    business_hours_set: bool = False


@dataclass
class LokigiScoreResult:
    """Resultado completo del algoritmo Lokigi Score"""
    total_score: int  # 0-100
    dimension_scores: Dict[str, int]  # Score por cada dimensión
    lucro_cesante_mensual: float  # USD/mes en pérdidas estimadas
    lucro_cesante_anual: float  # USD/año
    clientes_perdidos_mes: int
    critical_issues: List[str]
    recommendations: List[str]
    ranking_position_estimated: int
    ranking_improvement_potential: int


@dataclass
class ManualScrapedData:
    """
    Datos scraped manualmente por el Worker desde Google Maps
    El Worker copia y pega estos datos desde el perfil de GMB
    """
    # RAW TEXT copiado directamente
    raw_business_name: str
    raw_address: str
    raw_phone: str = ""
    raw_website: str = ""
    
    # Métricas visibles
    rating_text: str = "0"  # ej: "4.5"
    reviews_text: str = "0"  # ej: "230 reseñas"
    
    # Indicadores de estado
    claimed_text: str = ""  # ej: "Propietario de esta empresa" o vacío
    verified_badge: bool = False
    
    # Categorías
    primary_category: str = ""
    additional_categories_text: str = ""  # separado por comas
    
    # Fotos
    photo_count_text: str = "0"
    latest_photo_date_text: str = ""  # ej: "hace 2 semanas", "2023-12-01"
    
    # Horarios
    business_hours_text: str = ""
    
    # País/Ubicación
    country: Country = Country.ARGENTINA
    city: str = ""
    
    # Metadata
    scraped_date: datetime = None


class LokigiScoreCalculator:
    """Motor principal del algoritmo Lokigi Score"""
    
    # Volúmenes de búsqueda promedio por categoría y país (búsquedas/mes)
    SEARCH_VOLUMES = {
        Country.ARGENTINA: {
            "restaurante": 18000,
            "pizzeria": 12000,
            "cafe": 8000,
            "bar": 10000,
            "peluqueria": 5000,
            "gym": 6000,
            "hotel": 15000,
            "dentista": 7000,
            "abogado": 5500,
            "mecanico": 4000,
            "default": 5000
        },
        Country.BRASIL: {
            "restaurante": 35000,
            "pizzaria": 22000,
            "cafe": 15000,
            "bar": 18000,
            "salao_beleza": 10000,
            "academia": 12000,
            "hotel": 28000,
            "dentista": 14000,
            "advogado": 11000,
            "mecanico": 8000,
            "default": 10000
        },
        Country.EEUU: {
            "restaurant": 90000,
            "pizza": 75000,
            "coffee": 60000,
            "bar": 55000,
            "hair_salon": 40000,
            "gym": 50000,
            "hotel": 85000,
            "dentist": 65000,
            "lawyer": 55000,
            "mechanic": 45000,
            "default": 35000
        }
    }
    
    # Valor promedio del cliente por país (USD)
    AVERAGE_CUSTOMER_VALUE = {
        Country.ARGENTINA: 25,
        Country.BRASIL: 30,
        Country.EEUU: 75
    }
    
    # CTR (Click-Through Rate) por posición en resultados de Google Maps
    POSITION_CTR = {
        1: 0.35,   # 35% de clicks
        2: 0.22,   # 22%
        3: 0.15,   # 15%
        4: 0.10,   # 10%
        5: 0.08,   # 8%
        6: 0.05,   # 5%
        7: 0.03,   # 3%
        8: 0.02,   # 2%
        # 9+: despreciable
    }
    
    def __init__(self):
        pass
    
    def parse_manual_data(self, scraped: ManualScrapedData) -> Tuple[
        NAP, ReviewsMetrics, PhotosMetrics, CategoryMetrics, VerificationMetrics
    ]:
        """
        Convierte el texto scrapeado manualmente en métricas estructuradas
        """
        
        # DIMENSIÓN 1: NAP
        nap = NAP()
        nap.name_complete = bool(scraped.raw_business_name and len(scraped.raw_business_name) > 3)
        nap.address_complete = bool(scraped.raw_address and len(scraped.raw_address) > 10)
        nap.phone_present = bool(scraped.raw_phone and len(scraped.raw_phone) > 5)
        nap.phone_format_valid = self._validate_phone_format(scraped.raw_phone, scraped.country)
        nap.consistency_score = self._calculate_nap_consistency(nap)
        
        # DIMENSIÓN 2: Reseñas
        reviews = ReviewsMetrics()
        reviews.average_rating = self._parse_rating(scraped.rating_text)
        reviews.total_reviews = self._parse_review_count(scraped.reviews_text)
        reviews.sentiment_score = self._estimate_sentiment(reviews.average_rating)
        
        # DIMENSIÓN 3: Fotos
        photos = PhotosMetrics()
        photos.total_photos = self._parse_photo_count(scraped.photo_count_text)
        photos.days_since_last_photo = self._parse_days_since_photo(scraped.latest_photo_date_text)
        photos.photo_freshness_score = self._calculate_photo_freshness(photos.days_since_last_photo)
        
        # DIMENSIÓN 4: Categorías
        categories = CategoryMetrics()
        categories.primary_category_set = bool(scraped.primary_category)
        categories.additional_categories = self._count_additional_categories(
            scraped.additional_categories_text
        )
        categories.category_relevance_score = self._calculate_category_relevance(categories)
        
        # DIMENSIÓN 5: Verificación
        verification = VerificationMetrics()
        verification.is_claimed = self._check_if_claimed(scraped.claimed_text)
        verification.is_verified = scraped.verified_badge
        verification.business_hours_set = bool(scraped.business_hours_text)
        
        return nap, reviews, photos, categories, verification
    
    def calculate_lokigi_score(
        self,
        scraped: ManualScrapedData
    ) -> LokigiScoreResult:
        """
        Calcula el Lokigi Score completo (0-100) con análisis de lucro cesante
        """
        
        # 1. Parse manual data
        nap, reviews, photos, categories, verification = self.parse_manual_data(scraped)
        
        # 2. Calcular score por dimensión (20 puntos cada una)
        scores = {}
        scores["NAP"] = self._score_nap(nap)
        scores["Reseñas"] = self._score_reviews(reviews)
        scores["Fotos"] = self._score_photos(photos)
        scores["Categorías"] = self._score_categories(categories)
        scores["Verificación"] = self._score_verification(verification)
        
        # 3. Score total (suma de las 5 dimensiones)
        total_score = sum(scores.values())
        
        # 4. Calcular posición estimada en ranking (basado en score)
        estimated_position = self._estimate_ranking_position(total_score, reviews.total_reviews)
        
        # 5. Calcular LUCRO CESANTE
        lucro_data = self._calculate_lucro_cesante(
            scraped=scraped,
            current_position=estimated_position,
            total_score=total_score,
            reviews=reviews
        )
        
        # 6. Identificar problemas críticos
        critical_issues = self._identify_critical_issues(
            nap, reviews, photos, categories, verification
        )
        
        # 7. Generar recomendaciones priorizadas
        recommendations = self._generate_recommendations(
            scores, critical_issues, lucro_data["improvement_potential"]
        )
        
        return LokigiScoreResult(
            total_score=total_score,
            dimension_scores=scores,
            lucro_cesante_mensual=lucro_data["monthly_loss"],
            lucro_cesante_anual=lucro_data["annual_loss"],
            clientes_perdidos_mes=lucro_data["customers_lost"],
            critical_issues=critical_issues,
            recommendations=recommendations,
            ranking_position_estimated=estimated_position,
            ranking_improvement_potential=lucro_data["improvement_potential"]
        )
    
    # ========== SCORING POR DIMENSIÓN (20 puntos cada una) ==========
    
    def _score_nap(self, nap: NAP) -> int:
        """Score dimensión NAP: 0-20 puntos"""
        score = 0
        
        if nap.name_complete:
            score += 4
        if nap.address_complete:
            score += 6
        if nap.phone_present:
            score += 4
        if nap.phone_format_valid:
            score += 2
        score += int(nap.consistency_score * 4)  # 0-4 puntos
        
        return min(20, score)
    
    def _score_reviews(self, reviews: ReviewsMetrics) -> int:
        """Score dimensión Reseñas: 0-20 puntos"""
        score = 0
        
        # Rating (0-8 puntos)
        if reviews.average_rating >= 4.5:
            score += 8
        elif reviews.average_rating >= 4.0:
            score += 6
        elif reviews.average_rating >= 3.5:
            score += 4
        elif reviews.average_rating >= 3.0:
            score += 2
        
        # Cantidad (0-8 puntos)
        if reviews.total_reviews >= 100:
            score += 8
        elif reviews.total_reviews >= 50:
            score += 6
        elif reviews.total_reviews >= 25:
            score += 4
        elif reviews.total_reviews >= 10:
            score += 2
        
        # Sentiment (0-4 puntos)
        score += int(reviews.sentiment_score * 4)
        
        return min(20, score)
    
    def _score_photos(self, photos: PhotosMetrics) -> int:
        """Score dimensión Fotos: 0-20 puntos"""
        score = 0
        
        # Cantidad de fotos (0-8 puntos)
        if photos.total_photos >= 50:
            score += 8
        elif photos.total_photos >= 25:
            score += 6
        elif photos.total_photos >= 10:
            score += 4
        elif photos.total_photos >= 5:
            score += 2
        
        # Frescura (0-12 puntos)
        score += int(photos.photo_freshness_score * 12)
        
        return min(20, score)
    
    def _score_categories(self, categories: CategoryMetrics) -> int:
        """Score dimensión Categorías: 0-20 puntos"""
        score = 0
        
        if categories.primary_category_set:
            score += 10
        
        # Categorías adicionales (0-5 puntos)
        score += min(5, categories.additional_categories * 2)
        
        # Relevancia (0-5 puntos)
        score += int(categories.category_relevance_score * 5)
        
        return min(20, score)
    
    def _score_verification(self, verification: VerificationMetrics) -> int:
        """Score dimensión Verificación: 0-20 puntos"""
        score = 0
        
        if verification.is_claimed:
            score += 10  # MÁS CRÍTICO
        if verification.is_verified:
            score += 5
        if verification.business_hours_set:
            score += 5
        
        return min(20, score)
    
    # ========== CÁLCULO DE LUCRO CESANTE ==========
    
    def _calculate_lucro_cesante(
        self,
        scraped: ManualScrapedData,
        current_position: int,
        total_score: int,
        reviews: ReviewsMetrics
    ) -> Dict:
        """
        Calcula cuánto dinero pierde el negocio por no estar en posición #1
        
        Fórmula:
        1. Obtener volumen de búsqueda de la categoría en el país
        2. Calcular CTR actual vs CTR potencial (posición #1)
        3. Diferencia de clicks = clientes perdidos
        4. Clientes perdidos × Valor promedio del cliente = Lucro cesante
        """
        
        # 1. Volumen de búsqueda mensual
        category_key = self._normalize_category_key(
            scraped.primary_category,
            scraped.country
        )
        search_volume = self.SEARCH_VOLUMES.get(scraped.country, {}).get(
            category_key,
            self.SEARCH_VOLUMES[scraped.country]["default"]
        )
        
        # 2. CTR actual vs potencial
        current_ctr = self.POSITION_CTR.get(current_position, 0.01)
        potential_ctr = self.POSITION_CTR[1]  # Posición #1
        
        # 3. Clicks perdidos mensualmente
        current_clicks = search_volume * current_ctr
        potential_clicks = search_volume * potential_ctr
        clicks_lost = potential_clicks - current_clicks
        
        # 4. Conversión: asumimos 20% de clicks se convierten en clientes
        conversion_rate = 0.20
        customers_lost = int(clicks_lost * conversion_rate)
        
        # 5. Valor económico
        avg_customer_value = self.AVERAGE_CUSTOMER_VALUE[scraped.country]
        monthly_loss = customers_lost * avg_customer_value
        annual_loss = monthly_loss * 12
        
        # 6. Potencial de mejora (cuántas posiciones podría subir)
        improvement_potential = self._calculate_improvement_potential(
            total_score, current_position
        )
        
        return {
            "monthly_loss": round(monthly_loss, 2),
            "annual_loss": round(annual_loss, 2),
            "customers_lost": customers_lost,
            "current_position": current_position,
            "potential_position": 1,
            "improvement_potential": improvement_potential,
            "search_volume": search_volume,
            "current_ctr": round(current_ctr * 100, 1),
            "potential_ctr": round(potential_ctr * 100, 1)
        }
    
    def _estimate_ranking_position(self, score: int, review_count: int) -> int:
        """
        Estima la posición en el ranking de Google Maps basado en score y reseñas
        
        Lógica:
        - Score 90-100 + 100+ reseñas = Posición 1-2
        - Score 75-89 + 50+ reseñas = Posición 3-4
        - Score 60-74 + 25+ reseñas = Posición 5-6
        - Score 45-59 = Posición 7-8
        - Score <45 = Posición 9+
        """
        
        if score >= 90 and review_count >= 100:
            return 1
        elif score >= 90 and review_count >= 50:
            return 2
        elif score >= 75 and review_count >= 50:
            return 3
        elif score >= 75 and review_count >= 25:
            return 4
        elif score >= 60 and review_count >= 25:
            return 5
        elif score >= 60:
            return 6
        elif score >= 45:
            return 7
        elif score >= 30:
            return 8
        else:
            return 10  # Fuera del top 8
    
    def _calculate_improvement_potential(self, current_score: int, current_position: int) -> int:
        """Cuántas posiciones podría mejorar con optimización"""
        
        if current_score < 30:
            return 7  # Puede subir mucho
        elif current_score < 50:
            return 5
        elif current_score < 70:
            return 3
        elif current_score < 85:
            return 2
        else:
            return 1
    
    # ========== PARSING DE DATOS MANUALES ==========
    
    def _parse_rating(self, rating_text: str) -> float:
        """Extrae rating de texto: '4.5' -> 4.5"""
        try:
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0.0
    
    def _parse_review_count(self, reviews_text: str) -> int:
        """Extrae cantidad de reseñas: '230 reseñas' -> 230"""
        try:
            match = re.search(r'(\d+)', reviews_text)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0
    
    def _parse_photo_count(self, photo_text: str) -> int:
        """Extrae cantidad de fotos: '45 fotos' -> 45"""
        try:
            match = re.search(r'(\d+)', photo_text)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0
    
    def _parse_days_since_photo(self, date_text: str) -> int:
        """
        Convierte texto de fecha en días transcurridos
        Ejemplos: 'hace 2 semanas' -> 14, 'hace 3 meses' -> 90
        """
        date_text = date_text.lower()
        
        # Patrones en español
        if 'hoy' in date_text or 'today' in date_text:
            return 0
        elif 'ayer' in date_text or 'yesterday' in date_text:
            return 1
        elif 'día' in date_text or 'day' in date_text:
            match = re.search(r'(\d+)', date_text)
            return int(match.group(1)) if match else 7
        elif 'semana' in date_text or 'week' in date_text:
            match = re.search(r'(\d+)', date_text)
            weeks = int(match.group(1)) if match else 1
            return weeks * 7
        elif 'mes' in date_text or 'month' in date_text or 'mês' in date_text:
            match = re.search(r'(\d+)', date_text)
            months = int(match.group(1)) if match else 1
            return months * 30
        elif 'año' in date_text or 'year' in date_text or 'ano' in date_text:
            match = re.search(r'(\d+)', date_text)
            years = int(match.group(1)) if match else 1
            return years * 365
        
        # Si no se puede parsear, asumir 1 año
        return 365
    
    def _validate_phone_format(self, phone: str, country: Country) -> bool:
        """Valida formato de teléfono según país"""
        if not phone:
            return False
        
        # Limpiar teléfono
        clean = re.sub(r'[^\d+]', '', phone)
        
        if country == Country.ARGENTINA:
            # +54 9 11 xxxx-xxxx (10-15 dígitos)
            return len(clean) >= 10
        elif country == Country.BRASIL:
            # +55 11 9xxxx-xxxx (10-13 dígitos)
            return len(clean) >= 10
        elif country == Country.EEUU:
            # +1 (xxx) xxx-xxxx (10 dígitos)
            return len(clean) >= 10
        
        return len(clean) >= 10
    
    def _calculate_nap_consistency(self, nap: NAP) -> float:
        """Score de consistencia NAP (0-1)"""
        points = 0
        total = 3
        
        if nap.name_complete:
            points += 1
        if nap.address_complete:
            points += 1
        if nap.phone_present and nap.phone_format_valid:
            points += 1
        
        return points / total
    
    def _estimate_sentiment(self, rating: float) -> float:
        """Estima sentiment score basado en rating (0-1)"""
        if rating >= 4.5:
            return 1.0
        elif rating >= 4.0:
            return 0.8
        elif rating >= 3.5:
            return 0.6
        elif rating >= 3.0:
            return 0.4
        else:
            return 0.2
    
    def _calculate_photo_freshness(self, days: int) -> float:
        """Score de frescura de fotos (0-1)"""
        if days <= 7:
            return 1.0
        elif days <= 30:
            return 0.9
        elif days <= 90:
            return 0.7
        elif days <= 180:
            return 0.5
        elif days <= 365:
            return 0.3
        else:
            return 0.1
    
    def _count_additional_categories(self, categories_text: str) -> int:
        """Cuenta categorías adicionales separadas por coma"""
        if not categories_text:
            return 0
        return len([c.strip() for c in categories_text.split(',') if c.strip()])
    
    def _calculate_category_relevance(self, categories: CategoryMetrics) -> float:
        """Score de relevancia de categorías (0-1)"""
        score = 0.0
        
        if categories.primary_category_set:
            score += 0.6
        
        # Bonus por categorías adicionales (hasta 0.4)
        if categories.additional_categories >= 3:
            score += 0.4
        elif categories.additional_categories >= 2:
            score += 0.3
        elif categories.additional_categories >= 1:
            score += 0.2
        
        return min(1.0, score)
    
    def _check_if_claimed(self, claimed_text: str) -> bool:
        """Detecta si el negocio está reclamado por el propietario"""
        claimed_text = claimed_text.lower()
        indicators = [
            'propietario',
            'owner',
            'dono',
            'proprietário',
            'verificado',
            'verified',
            'reclamado',
            'claimed'
        ]
        return any(ind in claimed_text for ind in indicators)
    
    def _normalize_category_key(self, category: str, country: Country) -> str:
        """Normaliza categoría a una key del diccionario de búsquedas"""
        category_lower = category.lower()
        
        # Mapeo de categorías a keys
        mappings = {
            Country.ARGENTINA: {
                'restaurante': 'restaurante',
                'restaurant': 'restaurante',
                'pizzería': 'pizzeria',
                'pizzeria': 'pizzeria',
                'pizza': 'pizzeria',
                'café': 'cafe',
                'cafeteria': 'cafe',
                'bar': 'bar',
                'pub': 'bar',
                'peluquería': 'peluqueria',
                'salón': 'peluqueria',
                'gimnasio': 'gym',
                'gym': 'gym',
                'hotel': 'hotel',
                'alojamiento': 'hotel',
                'dentista': 'dentista',
                'odontólogo': 'dentista',
                'abogado': 'abogado',
                'estudio jurídico': 'abogado',
                'mecánico': 'mecanico',
                'taller': 'mecanico'
            },
            Country.BRASIL: {
                'restaurante': 'restaurante',
                'pizzaria': 'pizzaria',
                'pizza': 'pizzaria',
                'café': 'cafe',
                'cafeteria': 'cafe',
                'bar': 'bar',
                'salão': 'salao_beleza',
                'beleza': 'salao_beleza',
                'academia': 'academia',
                'ginásio': 'academia',
                'hotel': 'hotel',
                'pousada': 'hotel',
                'dentista': 'dentista',
                'advogado': 'advogado',
                'escritório': 'advogado',
                'mecânico': 'mecanico',
                'oficina': 'mecanico'
            },
            Country.EEUU: {
                'restaurant': 'restaurant',
                'pizzeria': 'pizza',
                'pizza': 'pizza',
                'coffee': 'coffee',
                'cafe': 'coffee',
                'bar': 'bar',
                'pub': 'bar',
                'hair': 'hair_salon',
                'salon': 'hair_salon',
                'gym': 'gym',
                'fitness': 'gym',
                'hotel': 'hotel',
                'inn': 'hotel',
                'dentist': 'dentist',
                'lawyer': 'lawyer',
                'attorney': 'lawyer',
                'mechanic': 'mechanic',
                'auto repair': 'mechanic'
            }
        }
        
        country_mappings = mappings.get(country, {})
        for key, value in country_mappings.items():
            if key in category_lower:
                return value
        
        return 'default'
    
    # ========== DIAGNÓSTICO Y RECOMENDACIONES ==========
    
    def _identify_critical_issues(
        self,
        nap: NAP,
        reviews: ReviewsMetrics,
        photos: PhotosMetrics,
        categories: CategoryMetrics,
        verification: VerificationMetrics
    ) -> List[str]:
        """Identifica los problemas más críticos que están dañando el ranking"""
        issues = []
        
        # CRÍTICO: No reclamado
        if not verification.is_claimed:
            issues.append(
                "🚨 CRÍTICO: Negocio NO RECLAMADO - Cualquiera puede editar tu información. "
                "Esto te está costando el 40% de tu visibilidad."
            )
        
        # CRÍTICO: Rating bajo
        if reviews.average_rating < 3.5:
            issues.append(
                f"⭐ CRÍTICO: Rating de {reviews.average_rating:.1f} espanta al 78% de clientes. "
                "Prioridad #1: mejorar reputación."
            )
        
        # MUY IMPORTANTE: Pocas reseñas
        if reviews.total_reviews < 10:
            issues.append(
                f"💬 URGENTE: Solo {reviews.total_reviews} reseñas. Negocios con +50 reseñas "
                "reciben 270% más clics."
            )
        
        # IMPORTANTE: NAP incompleto
        if not nap.phone_present or not nap.address_complete:
            issues.append(
                "📍 IMPORTANTE: Información de contacto incompleta (NAP). "
                "Pierdes credibilidad y conversiones."
            )
        
        # IMPORTANTE: Sin categoría principal
        if not categories.primary_category_set:
            issues.append(
                "🏷️ IMPORTANTE: No tienes categoría principal definida. "
                "Google no sabe cuándo mostrarte en búsquedas."
            )
        
        # Fotos desactualizadas
        if photos.days_since_last_photo > 180:
            issues.append(
                f"📸 Fotos desactualizadas ({photos.days_since_last_photo} días). "
                "Negocios con fotos frescas obtienen 42% más engagement."
            )
        
        # Sin horarios
        if not verification.business_hours_set:
            issues.append(
                "🕐 Horarios no configurados. Clientes no saben cuándo visitarte."
            )
        
        return issues
    
    def _generate_recommendations(
        self,
        scores: Dict[str, int],
        critical_issues: List[str],
        improvement_potential: int
    ) -> List[str]:
        """Genera plan de acción priorizado"""
        recommendations = []
        
        # Identificar las 2 dimensiones más débiles
        sorted_dimensions = sorted(scores.items(), key=lambda x: x[1])
        weakest_dims = [dim for dim, score in sorted_dimensions[:2]]
        
        # Recomendaciones específicas por dimensión
        if "Verificación" in weakest_dims or scores["Verificación"] < 15:
            recommendations.append(
                "1️⃣ ACCIÓN INMEDIATA: Reclama tu negocio en Google My Business. "
                "Esto solo toma 5 minutos y aumenta tu visibilidad un 40%."
            )
        
        if "Reseñas" in weakest_dims or scores["Reseñas"] < 12:
            recommendations.append(
                "2️⃣ URGENTE: Implementa un sistema para pedir reseñas. "
                "Objetivo: conseguir 3-5 reseñas nuevas por semana."
            )
        
        if "NAP" in weakest_dims or scores["NAP"] < 15:
            recommendations.append(
                "3️⃣ PRIORIDAD: Completa tu perfil con teléfono, dirección y horarios correctos."
            )
        
        if "Fotos" in weakest_dims or scores["Fotos"] < 12:
            recommendations.append(
                "4️⃣ Esta semana: Sube 10 fotos profesionales (productos, local, equipo). "
                "Actualiza fotos cada mes."
            )
        
        if "Categorías" in weakest_dims or scores["Categorías"] < 15:
            recommendations.append(
                "5️⃣ Optimiza categorías: Define tu categoría principal y agrega 2-3 secundarias relevantes."
            )
        
        # Recomendación de potencial
        if improvement_potential >= 3:
            recommendations.append(
                f"🚀 POTENCIAL: Puedes subir {improvement_potential} posiciones en el ranking "
                "implementando estas mejoras en 30-60 días."
            )
        
        return recommendations


# ========== FUNCIÓN HELPER PARA WORKERS ==========

def quick_analyze_from_text(
    business_name: str,
    address: str,
    phone: str,
    rating: str,
    reviews: str,
    claimed_text: str,
    category: str,
    photos_count: str,
    last_photo: str,
    country_code: str = "AR",
    city: str = ""
) -> LokigiScoreResult:
    """
    Función rápida para que Workers analicen un negocio pegando texto
    
    Uso:
    result = quick_analyze_from_text(
        business_name="Pizzería Don Juan",
        address="Av. Corrientes 1234, Buenos Aires",
        phone="+54 11 4444-5555",
        rating="4.2",
        reviews="87 reseñas",
        claimed_text="Propietario de esta empresa",
        category="Pizzería",
        photos_count="23",
        last_photo="hace 2 meses",
        country_code="AR",
        city="Buenos Aires"
    )
    """
    
    # Mapear country code a enum
    country_map = {
        "AR": Country.ARGENTINA,
        "BR": Country.BRASIL,
        "US": Country.EEUU
    }
    country = country_map.get(country_code.upper(), Country.ARGENTINA)
    
    # Crear objeto ManualScrapedData
    scraped = ManualScrapedData(
        raw_business_name=business_name,
        raw_address=address,
        raw_phone=phone,
        rating_text=rating,
        reviews_text=reviews,
        claimed_text=claimed_text,
        primary_category=category,
        photo_count_text=photos_count,
        latest_photo_date_text=last_photo,
        country=country,
        city=city,
        scraped_date=datetime.now()
    )
    
    # Calcular score
    calculator = LokigiScoreCalculator()
    return calculator.calculate_lokigi_score(scraped)
