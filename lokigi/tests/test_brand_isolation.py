"""
QA Automation: El Validador de Aislamiento de Marca
--------------------------------------------------
Objetivo: Garantizar que el branding no se filtre entre agencias (multi-tenancy).

Cobertura:
- Branding Leak Test: El reporte de la Agencia A nunca debe mostrar branding de la Agencia B ni de Lokigi.
- Domain Routing Test: El middleware debe resolver el tenant correcto según subdominio o dominio custom en <200ms.
- Stripe Subscription Test: Si la suscripción de la agencia expira, todos sus clientes pierden acceso (soft-lock).

Requiere: pytest, playwright, requests
"""
import pytest
from playwright.sync_api import sync_playwright
import requests
import time

AGENCY_A_DOMAIN = "agenciaa.lokigi.com"
AGENCY_B_DOMAIN = "agenciab.lokigi.com"
LOKIGI_DOMAIN = "lokigi.com"
REPORT_PATH = "/impact-report"
DASHBOARD_PATH = "/dashboard"

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def context(browser):
    context = browser.new_context()
    yield context
    context.close()

@pytest.fixture
def page(context):
    page = context.new_page()
    yield page
    page.close()

# 1. Branding Leak Test
@pytest.mark.e2e
def test_branding_leak(page):
    # Carga reporte de Agencia A
    page.goto(f"https://{AGENCY_A_DOMAIN}{REPORT_PATH}")
    # Verifica que el logo, color y nombre sean de Agencia A
    assert page.is_visible("img[alt='Agency A Logo']")
    assert page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor") == "rgb(34, 211, 238)"  # Ejemplo: color de Agencia A
    assert page.is_visible("text=Agencia A")
    # Verifica que NO aparezca branding de Agencia B ni de Lokigi
    assert not page.is_visible("img[alt='Agency B Logo']")
    assert not page.is_visible("text=Lokigi")

# 2. Domain Routing Test
@pytest.mark.e2e
def test_domain_routing_speed(browser):
    for domain in [AGENCY_A_DOMAIN, AGENCY_B_DOMAIN]:
        context = browser.new_context()
        page = context.new_page()
        start = time.time()
        page.goto(f"https://{domain}{DASHBOARD_PATH}")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 200, f"Routing for {domain} took too long: {elapsed:.2f}ms"
        # Verifica branding correcto
        assert page.is_visible(f"text={domain.split('.')[0].capitalize()}")
        context.close()

# 3. Stripe Subscription Test
@pytest.mark.e2e
def test_stripe_subscription_softlock(page):
    # Simula expiración de suscripción de Agencia A
    requests.post("http://localhost:8000/api/stripe/mock-expire", json={"agency_id": "agenciaa"})
    page.goto(f"https://{AGENCY_A_DOMAIN}{DASHBOARD_PATH}")
    # Debe mostrar mensaje de acceso bloqueado
    assert page.is_visible("text=Acceso suspendido por suscripción expirada")

# Notas:
# - Ajusta los selectores y textos según tu frontend real.
# - Usa entornos de staging y mocks para pruebas de Stripe.
# - Puedes extender los asserts para buscar leaks en CSS, links, favicon, etc.
