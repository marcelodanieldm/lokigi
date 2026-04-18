"""
El Guardián de Integridad - Data Quality & Evaluation Module
Evalúa la consistencia y exactitud de NAP (Name, Address, Phone) 
en múltiples plataformas y genera score de integridad de datos.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from difflib import SequenceMatcher
import math


class NAPEvaluator:
    """Evaluador de consistencia NAP (Name, Address, Phone)"""
    
    # Umbrales de calidad
    EXCELLENT_SCORE = 95
    GOOD_SCORE = 90
    WARNING_SCORE = 75
    CRITICAL_SCORE = 60
    
    # Ponderaciones para el score final
    WEIGHTS = {
        "name_consistency": 0.20,      # 20%
        "phone_consistency": 0.25,     # 25%
        "address_consistency": 0.20,   # 20%
        "location_accuracy": 0.20,     # 20%
        "completeness": 0.15           # 15%
    }
    
    def __init__(self):
        self.evaluation_results = {}
    
    def evaluate_full_quality(
        self,
        google_maps_data: Dict,
        facebook_data: Optional[Dict] = None,
        instagram_data: Optional[Dict] = None,
        website_data: Optional[Dict] = None,
        coordinates: Optional[Tuple[float, float]] = None,
        address_coordinates: Optional[Tuple[float, float]] = None
    ) -> Dict:
        """
        Evaluación completa de calidad de datos NAP
        
        Args:
            google_maps_data: Datos de Google Maps (source of truth)
            facebook_data: Datos de Facebook Business Page
            instagram_data: Datos de Instagram Business
            website_data: Datos extraídos del sitio web
            coordinates: Coordenadas del pin de Google Maps (lat, lng)
            address_coordinates: Coordenadas geocodificadas de la dirección
            
        Returns:
            Dict con scores detallados y recomendaciones
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_score": 0,
            "dimensions": {},
            "alerts": [],
            "recommendations": [],
            "requires_cleanup_service": False
        }
        
        # 1. Evaluar consistencia de nombre
        name_score = self._evaluate_name_consistency(
            google_maps_data,
            facebook_data,
            instagram_data,
            website_data
        )
        results["dimensions"]["name_consistency"] = name_score
        
        # 2. Evaluar consistencia de teléfono
        phone_score = self._evaluate_phone_consistency(
            google_maps_data,
            facebook_data,
            instagram_data,
            website_data
        )
        results["dimensions"]["phone_consistency"] = phone_score
        
        # 3. Evaluar consistencia de dirección
        address_score = self._evaluate_address_consistency(
            google_maps_data,
            facebook_data,
            website_data
        )
        results["dimensions"]["address_consistency"] = address_score
        
        # 4. Evaluar exactitud de ubicación
        location_score = self._evaluate_location_accuracy(
            coordinates,
            address_coordinates
        )
        results["dimensions"]["location_accuracy"] = location_score
        
        # 5. Evaluar completitud de información
        completeness_score = self._evaluate_completeness(google_maps_data)
        results["dimensions"]["completeness"] = completeness_score
        
        # 6. Calcular score global ponderado
        overall_score = self._calculate_weighted_score(results["dimensions"])
        results["overall_score"] = overall_score
        
        # 7. Generar alertas según dimensiones
        results["alerts"] = self._generate_alerts(results["dimensions"], overall_score)
        
        # 8. Generar recomendaciones accionables
        results["recommendations"] = self._generate_recommendations(
            results["dimensions"],
            overall_score
        )
        
        # 9. Determinar si requiere servicio de limpieza ($99)
        results["requires_cleanup_service"] = overall_score < self.GOOD_SCORE
        
        return results
    
    def _evaluate_name_consistency(
        self,
        google_maps_data: Dict,
        facebook_data: Optional[Dict],
        instagram_data: Optional[Dict],
        website_data: Optional[Dict]
    ) -> Dict:
        """Evalúa consistencia del nombre del negocio en todas las plataformas"""
        google_name = google_maps_data.get("name", "").strip().lower()
        
        comparisons = []
        platforms_checked = 1  # Google siempre presente
        total_similarity = 100  # Google vs Google = 100%
        
        # Comparar con Facebook
        if facebook_data and facebook_data.get("name"):
            fb_name = facebook_data.get("name", "").strip().lower()
            similarity = self._calculate_string_similarity(google_name, fb_name)
            comparisons.append({
                "platform": "Facebook",
                "name": facebook_data.get("name"),
                "similarity": similarity
            })
            total_similarity += similarity
            platforms_checked += 1
        
        # Comparar con Instagram
        if instagram_data and instagram_data.get("name"):
            ig_name = instagram_data.get("name", "").strip().lower()
            similarity = self._calculate_string_similarity(google_name, ig_name)
            comparisons.append({
                "platform": "Instagram",
                "name": instagram_data.get("name"),
                "similarity": similarity
            })
            total_similarity += similarity
            platforms_checked += 1
        
        # Comparar con Website
        if website_data and website_data.get("name"):
            web_name = website_data.get("name", "").strip().lower()
            similarity = self._calculate_string_similarity(google_name, web_name)
            comparisons.append({
                "platform": "Website",
                "name": website_data.get("name"),
                "similarity": similarity
            })
            total_similarity += similarity
            platforms_checked += 1
        
        avg_similarity = total_similarity / platforms_checked
        
        return {
            "score": round(avg_similarity, 2),
            "google_maps_name": google_maps_data.get("name"),
            "comparisons": comparisons,
            "platforms_checked": platforms_checked,
            "status": self._get_status_label(avg_similarity)
        }
    
    def _evaluate_phone_consistency(
        self,
        google_maps_data: Dict,
        facebook_data: Optional[Dict],
        instagram_data: Optional[Dict],
        website_data: Optional[Dict]
    ) -> Dict:
        """Evalúa consistencia del teléfono en todas las plataformas"""
        google_phone = self._normalize_phone(google_maps_data.get("phone", ""))
        
        if not google_phone:
            return {
                "score": 0,
                "google_maps_phone": None,
                "comparisons": [],
                "platforms_checked": 0,
                "status": "missing",
                "alert": "No hay teléfono en Google Maps"
            }
        
        comparisons = []
        platforms_checked = 1
        matches = 1  # Google vs Google = match
        
        # Comparar con Facebook
        if facebook_data and facebook_data.get("phone"):
            fb_phone = self._normalize_phone(facebook_data.get("phone", ""))
            is_match = google_phone == fb_phone
            comparisons.append({
                "platform": "Facebook",
                "phone": facebook_data.get("phone"),
                "normalized": fb_phone,
                "matches": is_match
            })
            if is_match:
                matches += 1
            platforms_checked += 1
        
        # Comparar con Instagram
        if instagram_data and instagram_data.get("phone"):
            ig_phone = self._normalize_phone(instagram_data.get("phone", ""))
            is_match = google_phone == ig_phone
            comparisons.append({
                "platform": "Instagram",
                "phone": instagram_data.get("phone"),
                "normalized": ig_phone,
                "matches": is_match
            })
            if is_match:
                matches += 1
            platforms_checked += 1
        
        # Comparar con Website
        if website_data and website_data.get("phone"):
            web_phone = self._normalize_phone(website_data.get("phone", ""))
            is_match = google_phone == web_phone
            comparisons.append({
                "platform": "Website",
                "phone": website_data.get("phone"),
                "normalized": web_phone,
                "matches": is_match
            })
            if is_match:
                matches += 1
            platforms_checked += 1
        
        score = (matches / platforms_checked) * 100
        
        return {
            "score": round(score, 2),
            "google_maps_phone": google_maps_data.get("phone"),
            "normalized_phone": google_phone,
            "comparisons": comparisons,
            "platforms_checked": platforms_checked,
            "matches": matches,
            "status": self._get_status_label(score)
        }
    
    def _evaluate_address_consistency(
        self,
        google_maps_data: Dict,
        facebook_data: Optional[Dict],
        website_data: Optional[Dict]
    ) -> Dict:
        """Evalúa consistencia de la dirección en plataformas"""
        google_address = google_maps_data.get("address", "").strip().lower()
        
        if not google_address:
            return {
                "score": 0,
                "google_maps_address": None,
                "comparisons": [],
                "platforms_checked": 0,
                "status": "missing"
            }
        
        comparisons = []
        platforms_checked = 1
        total_similarity = 100
        
        # Comparar con Facebook
        if facebook_data and facebook_data.get("address"):
            fb_address = facebook_data.get("address", "").strip().lower()
            similarity = self._calculate_string_similarity(google_address, fb_address)
            comparisons.append({
                "platform": "Facebook",
                "address": facebook_data.get("address"),
                "similarity": similarity
            })
            total_similarity += similarity
            platforms_checked += 1
        
        # Comparar con Website
        if website_data and website_data.get("address"):
            web_address = website_data.get("address", "").strip().lower()
            similarity = self._calculate_string_similarity(google_address, web_address)
            comparisons.append({
                "platform": "Website",
                "address": website_data.get("address"),
                "similarity": similarity
            })
            total_similarity += similarity
            platforms_checked += 1
        
        avg_similarity = total_similarity / platforms_checked
        
        return {
            "score": round(avg_similarity, 2),
            "google_maps_address": google_maps_data.get("address"),
            "comparisons": comparisons,
            "platforms_checked": platforms_checked,
            "status": self._get_status_label(avg_similarity)
        }
    
    def _evaluate_location_accuracy(
        self,
        pin_coordinates: Optional[Tuple[float, float]],
        address_coordinates: Optional[Tuple[float, float]]
    ) -> Dict:
        """
        Evalúa si las coordenadas del pin coinciden con la dirección
        Alerta si el desfase es > 50 metros
        """
        if not pin_coordinates or not address_coordinates:
            return {
                "score": 50,  # Score neutral si no hay datos
                "distance_meters": None,
                "status": "unknown",
                "message": "No hay coordenadas para comparar"
            }
        
        # Calcular distancia usando fórmula de Haversine
        distance_meters = self._calculate_haversine_distance(
            pin_coordinates,
            address_coordinates
        )
        
        # Score basado en distancia
        if distance_meters <= 10:
            score = 100  # Perfecto
        elif distance_meters <= 25:
            score = 95   # Excelente
        elif distance_meters <= 50:
            score = 85   # Bueno
        elif distance_meters <= 100:
            score = 70   # Aceptable
        elif distance_meters <= 200:
            score = 50   # Preocupante
        else:
            score = 20   # Crítico
        
        alert = None
        if distance_meters > 50:
            alert = f"⚠️ Pérdida de Clientes Físicos: El pin está a {round(distance_meters)}m de la dirección real"
        
        return {
            "score": score,
            "pin_coordinates": pin_coordinates,
            "address_coordinates": address_coordinates,
            "distance_meters": round(distance_meters, 2),
            "status": self._get_status_label(score),
            "alert": alert
        }
    
    def _evaluate_completeness(self, google_maps_data: Dict) -> Dict:
        """
        Evalúa qué campos opcionales pero vitales faltan
        - Horarios (business_hours)
        - Horarios especiales (special_hours)
        - Menú (menu_url)
        - Atributos de accesibilidad (accessibility)
        - Descripción (description)
        - Categorías secundarias (secondary_categories)
        """
        total_fields = 0
        completed_fields = 0
        missing_fields = []
        
        # Lista de campos vitales
        vital_fields = {
            "business_hours": "Horario de atención",
            "description": "Descripción del negocio",
            "website": "Sitio web",
            "menu_url": "Menú o catálogo",
            "accessibility_wheelchair": "Accesibilidad",
            "attributes": "Atributos del negocio",
            "services": "Servicios ofrecidos"
        }
        
        for field, label in vital_fields.items():
            total_fields += 1
            value = google_maps_data.get(field)
            
            if value and value not in [None, "", [], {}]:
                completed_fields += 1
            else:
                missing_fields.append(label)
        
        score = (completed_fields / total_fields) * 100
        
        return {
            "score": round(score, 2),
            "completed_fields": completed_fields,
            "total_fields": total_fields,
            "missing_fields": missing_fields,
            "status": self._get_status_label(score)
        }
    
    def _calculate_weighted_score(self, dimensions: Dict) -> float:
        """Calcula el score global ponderado según los pesos definidos"""
        total_score = 0
        
        for dimension, weight in self.WEIGHTS.items():
            if dimension in dimensions:
                dimension_score = dimensions[dimension].get("score", 0)
                total_score += dimension_score * weight
        
        return round(total_score, 2)
    
    def _generate_alerts(self, dimensions: Dict, overall_score: float) -> List[Dict]:
        """Genera alertas críticas basadas en las dimensiones evaluadas"""
        alerts = []
        
        # Alert por score global bajo
        if overall_score < self.CRITICAL_SCORE:
            alerts.append({
                "type": "critical",
                "title": "🚨 Integridad de Datos Crítica",
                "message": f"Score: {overall_score}%. El negocio está perdiendo clientes por información inconsistente.",
                "priority": 1
            })
        elif overall_score < self.WARNING_SCORE:
            alerts.append({
                "type": "warning",
                "title": "⚠️ Integridad de Datos Baja",
                "message": f"Score: {overall_score}%. Se detectaron inconsistencias que afectan la confianza del cliente.",
                "priority": 2
            })
        
        # Alert por teléfono inconsistente
        phone_score = dimensions.get("phone_consistency", {}).get("score", 100)
        if phone_score < 80:
            alerts.append({
                "type": "critical",
                "title": "📞 Teléfonos Inconsistentes",
                "message": "El teléfono no coincide entre plataformas. Los clientes no pueden contactarte.",
                "priority": 1
            })
        
        # Alert por ubicación inexacta
        location_data = dimensions.get("location_accuracy", {})
        if location_data.get("alert"):
            alerts.append({
                "type": "critical",
                "title": "📍 Ubicación Inexacta",
                "message": location_data["alert"],
                "priority": 1
            })
        
        # Alert por campos faltantes
        completeness_data = dimensions.get("completeness", {})
        if completeness_data.get("score", 100) < 70:
            missing_count = len(completeness_data.get("missing_fields", []))
            alerts.append({
                "type": "warning",
                "title": "📋 Información Incompleta",
                "message": f"Faltan {missing_count} campos vitales que afectan tu visibilidad en Google.",
                "priority": 2
            })
        
        # Ordenar por prioridad
        alerts.sort(key=lambda x: x["priority"])
        
        return alerts
    
    def _generate_recommendations(self, dimensions: Dict, overall_score: float) -> List[str]:
        """Genera recomendaciones accionables según los problemas detectados"""
        recommendations = []
        
        # Recomendación principal según score
        if overall_score < self.GOOD_SCORE:
            recommendations.append(
                f"💎 ACCIÓN URGENTE: Score de integridad {overall_score}% (requiere limpieza profesional). "
                "Contrata el Servicio de Limpieza de Datos ($99) para corregir todas las inconsistencias."
            )
        
        # Recomendaciones por dimensión
        name_score = dimensions.get("name_consistency", {}).get("score", 100)
        if name_score < 90:
            recommendations.append(
                "✏️ Unifica el nombre del negocio en todas las plataformas (Google, Facebook, Instagram, Web)."
            )
        
        phone_score = dimensions.get("phone_consistency", {}).get("score", 100)
        if phone_score < 90:
            recommendations.append(
                "📞 Corrige el teléfono para que sea idéntico en Google Maps, redes sociales y sitio web."
            )
        
        address_score = dimensions.get("address_consistency", {}).get("score", 100)
        if address_score < 90:
            recommendations.append(
                "📍 Estandariza la dirección en todas las plataformas usando el formato exacto de Google Maps."
            )
        
        location_score = dimensions.get("location_accuracy", {}).get("score", 100)
        if location_score < 85:
            recommendations.append(
                "🗺️ Reposiciona el pin de Google Maps para que coincida exactamente con tu dirección física."
            )
        
        completeness_data = dimensions.get("completeness", {})
        missing_fields = completeness_data.get("missing_fields", [])
        if missing_fields:
            recommendations.append(
                f"📋 Completa estos campos en Google Maps: {', '.join(missing_fields[:3])}."
            )
        
        return recommendations
    
    # ===== UTILIDADES =====
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calcula similitud entre dos strings usando SequenceMatcher (0-100)"""
        if not str1 or not str2:
            return 0.0
        
        similarity = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
        return round(similarity * 100, 2)
    
    def _normalize_phone(self, phone: str) -> str:
        """Normaliza un número de teléfono removiendo caracteres no numéricos"""
        if not phone:
            return ""
        
        # Remover todo excepto dígitos
        digits_only = re.sub(r'\D', '', phone)
        return digits_only
    
    def _calculate_haversine_distance(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float]
    ) -> float:
        """
        Calcula distancia entre dos coordenadas usando fórmula de Haversine
        Retorna distancia en metros
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Radio de la Tierra en metros
        R = 6371000
        
        # Convertir a radianes
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Fórmula de Haversine
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * \
            math.sin(delta_lon / 2) ** 2
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        
        return distance
    
    def _get_status_label(self, score: float) -> str:
        """Retorna etiqueta de estado según el score"""
        if score >= self.EXCELLENT_SCORE:
            return "excellent"
        elif score >= self.GOOD_SCORE:
            return "good"
        elif score >= self.WARNING_SCORE:
            return "warning"
        elif score >= self.CRITICAL_SCORE:
            return "poor"
        else:
            return "critical"
