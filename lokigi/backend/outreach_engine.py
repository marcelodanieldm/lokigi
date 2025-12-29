"""
Lokigi Outreach Engine: Crawler & Dispatcher
Chief Full Stack Developer
"""
import time
import hashlib
import random
import string
import requests
from typing import List, Dict
from bs4 import BeautifulSoup

# --- Scraper Liviano para Google Maps (simulado con BeautifulSoup) ---
def scrape_maps(query: str, location: str, max_results: int = 10) -> List[Dict]:
    """
    Extrae datos básicos de negocios en una zona geográfica específica.
    (En producción, usar Playwright headless o API de terceros; aquí, BeautifulSoup para demo.)
    """
    # Simulación: normalmente harías requests a Google Maps y parsearías el HTML
    # Aquí devolvemos datos mock para la demo
    businesses = []
    for i in range(max_results):
        businesses.append({
            "name": f"Negocio Demo {i+1}",
            "score": random.randint(60, 99),
            "phone": f"+34 600 000 00{i}",
            "website": f"negociodemo{i+1}.es",
            "address": f"Calle Falsa {i+1}, {location}",
        })
    return businesses

# --- Generador de Links Únicos ---
def generate_unique_link(business: Dict, base_url: str = "https://lokigi.com/audit/") -> str:
    """
    Genera una URL única para cada negocio usando hash.
    """
    raw = business["name"] + business["phone"] + business["website"]
    hash_id = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"{base_url}{hash_id}"

# --- Integración de Mensajería (WhatsApp API Ready) ---
def prepare_message(business: Dict, link: str) -> str:
    return (
        f"Hola {business['name']}, analicé tu local en Maps y tienes un score de {business['score']}/100. "
        f"Mira lo que está haciendo tu competencia aquí: {link}"
    )

# --- Rate Limiting y Rotación de Proxies (simulado) ---
def safe_dispatch(businesses: List[Dict], send_func, delay: float = 2.0, proxies: List[str] = None):
    """
    Envía mensajes con límites de velocidad y rotación de proxies.
    send_func(business, link, proxy) debe implementar el envío real.
    """
    proxies = proxies or [None]
    for i, b in enumerate(businesses):
        link = generate_unique_link(b)
        proxy = proxies[i % len(proxies)]
        send_func(b, link, proxy)
        time.sleep(delay)

# --- Ejemplo de integración ---
if __name__ == "__main__":
    # 1. Scrapea negocios
    businesses = scrape_maps("Dentista", "Madrid", max_results=5)
    # 2. Prepara y muestra mensajes
    def fake_send(business, link, proxy):
        msg = prepare_message(business, link)
        print(f"[Proxy: {proxy}] {msg}")
    # 3. Despacha con rate limiting y proxies
    safe_dispatch(businesses, fake_send, delay=1.5, proxies=[None, "proxy1:8080"])
