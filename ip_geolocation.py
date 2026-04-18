"""
Servicio de Geolocalización por IP - Presupuesto CERO
Detecta el país del usuario mediante IP sin APIs de pago
"""

import ipaddress
from typing import Optional
from enum import Enum


class Country(str, Enum):
    """Países soportados"""
    BRASIL = "BR"
    ARGENTINA = "AR"
    COLOMBIA = "CO"
    MEXICO = "MX"
    CHILE = "CL"
    PERU = "PE"
    URUGUAY = "UY"
    VENEZUELA = "VE"
    ECUADOR = "EC"
    USA = "US"
    SPAIN = "ES"
    UNKNOWN = "UNKNOWN"


class Language(str, Enum):
    """Idiomas soportados"""
    PORTUGUESE = "pt"
    SPANISH = "es"
    ENGLISH = "en"


# Rangos de IPs por país (principales ISPs)
# Esto es una aproximación básica - en producción usar geoip2 o similar
IP_RANGES_BY_COUNTRY = {
    # Brasil - Principales ISPs
    Country.BRASIL: [
        "200.128.0.0/9",      # Brasil Telecom
        "201.0.0.0/12",       # Varias operadoras BR
        "177.0.0.0/10",       # NET/Claro BR
        "179.0.0.0/10",       # Vivo BR
        "189.0.0.0/11",       # Tim BR
    ],
    # Argentina
    Country.ARGENTINA: [
        "190.0.0.0/12",       # Telecom Argentina
        "200.45.0.0/16",      # Fibertel
        "181.0.0.0/12",       # Varios ISPs AR
    ],
    # México
    Country.MEXICO: [
        "187.128.0.0/10",     # Telmex
        "201.128.0.0/11",     # Varios ISPs MX
    ],
    # Colombia
    Country.COLOMBIA: [
        "186.0.0.0/11",       # Varios ISPs CO
        "190.144.0.0/12",     # ETB/Claro CO
    ],
    # Chile
    Country.CHILE: [
        "152.172.0.0/14",     # VTR Chile
        "200.73.0.0/16",      # Entel Chile
    ],
    # Estados Unidos (muestra)
    Country.USA: [
        "8.0.0.0/8",          # Level3
        "12.0.0.0/8",         # AT&T
        "4.0.0.0/8",          # Level3
    ],
}


# Mapeo de países a idiomas
COUNTRY_TO_LANGUAGE = {
    Country.BRASIL: Language.PORTUGUESE,
    Country.ARGENTINA: Language.SPANISH,
    Country.COLOMBIA: Language.SPANISH,
    Country.MEXICO: Language.SPANISH,
    Country.CHILE: Language.SPANISH,
    Country.PERU: Language.SPANISH,
    Country.URUGUAY: Language.SPANISH,
    Country.VENEZUELA: Language.SPANISH,
    Country.ECUADOR: Language.SPANISH,
    Country.SPAIN: Language.SPANISH,
    Country.USA: Language.ENGLISH,
    Country.UNKNOWN: Language.ENGLISH,
}


class IPGeolocationService:
    """Servicio de geolocalización GRATIS basado en rangos de IP"""
    
    def __init__(self):
        # Cachear los rangos parseados para mejor performance
        self._parsed_ranges = {}
        for country, ranges in IP_RANGES_BY_COUNTRY.items():
            self._parsed_ranges[country] = [
                ipaddress.ip_network(range_str) for range_str in ranges
            ]
    
    def detect_country_from_ip(self, ip_address: str) -> Country:
        """
        Detecta el país basado en la IP del usuario
        
        Args:
            ip_address: IP del cliente (ej: "201.5.10.20")
            
        Returns:
            Country enum
        """
        if not ip_address or ip_address == "127.0.0.1":
            return Country.UNKNOWN
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Verificar si es IP privada
            if ip.is_private:
                return Country.UNKNOWN
            
            # Buscar en los rangos conocidos
            for country, networks in self._parsed_ranges.items():
                for network in networks:
                    if ip in network:
                        return country
            
            return Country.UNKNOWN
            
        except ValueError:
            # IP inválida
            return Country.UNKNOWN
    
    def detect_language_from_ip(self, ip_address: str) -> Language:
        """
        Detecta el idioma basado en la IP del usuario
        
        Args:
            ip_address: IP del cliente
            
        Returns:
            Language enum (pt, es, en)
        """
        country = self.detect_country_from_ip(ip_address)
        return COUNTRY_TO_LANGUAGE.get(country, Language.ENGLISH)
    
    def get_client_ip_from_headers(self, headers: dict) -> Optional[str]:
        """
        Extrae la IP del cliente de los headers HTTP
        
        Prioridad:
        1. X-Forwarded-For (cuando está detrás de proxy/load balancer)
        2. X-Real-IP
        3. Remote-Addr (directo)
        
        Args:
            headers: Dict con los headers HTTP
            
        Returns:
            IP del cliente o None
        """
        # X-Forwarded-For puede tener múltiples IPs: "client, proxy1, proxy2"
        forwarded = headers.get("x-forwarded-for")
        if forwarded:
            # Tomar la primera IP (la del cliente original)
            return forwarded.split(",")[0].strip()
        
        # X-Real-IP (usado por algunos proxies)
        real_ip = headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Remote-Addr (conexión directa)
        remote = headers.get("remote-addr")
        if remote:
            return remote.strip()
        
        return None


# Singleton global
_geolocation_service = None


def get_geolocation_service() -> IPGeolocationService:
    """Retorna la instancia singleton del servicio"""
    global _geolocation_service
    if _geolocation_service is None:
        _geolocation_service = IPGeolocationService()
    return _geolocation_service


# Helper functions
def detect_language_from_request_headers(headers: dict) -> Language:
    """
    Helper: Detecta el idioma del usuario desde los headers de la request
    
    Usage en FastAPI:
        @app.get("/")
        async def endpoint(request: Request):
            language = detect_language_from_request_headers(dict(request.headers))
    """
    service = get_geolocation_service()
    client_ip = service.get_client_ip_from_headers(headers)
    
    if client_ip:
        return service.detect_language_from_ip(client_ip)
    
    return Language.ENGLISH


def detect_country_from_request_headers(headers: dict) -> Country:
    """Helper: Detecta el país del usuario desde los headers"""
    service = get_geolocation_service()
    client_ip = service.get_client_ip_from_headers(headers)
    
    if client_ip:
        return service.detect_country_from_ip(client_ip)
    
    return Country.UNKNOWN
