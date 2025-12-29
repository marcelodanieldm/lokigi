"""
QA Automation: El Validador de la Cadena de Pago
------------------------------------------------
Objetivo: Garantizar que no se pierda ninguna comisión y que el sistema de atribución sea infalible.

Cobertura:
- End-to-End Tracking: Simula el flujo completo de afiliado a pago y comisión.
- Cookie Persistence: Verifica persistencia de atribución tras cierre y reapertura de navegador.
- Security Test: Previene manipulación de referencia en checkout.

Requiere: pytest, playwright, requests
"""
import pytest
from playwright.sync_api import sync_playwright
import requests
import time

# Configuración
AFFILIATE_LINK = "http://localhost:3000/api/affiliate?ref=AFILIADO123"
DASHBOARD_URL = "http://localhost:3000/partner/dashboard"
STRIPE_WEBHOOK_URL = "http://localhost:8000/webhook/stripe"
TEST_EMAIL = "qa_affiliate_test@lokigi.com"

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

# 1. End-to-End Tracking
@pytest.mark.e2e
def test_affiliate_payment_chain(page):
    # Simula clic en link de afiliado
    page.goto(AFFILIATE_LINK)
    assert "ref=AFILIADO123" in page.url
    # Simula navegación y registro de lead
    page.click("#register-lead")
    page.fill("#email", TEST_EMAIL)
    page.click("#submit-lead")
    assert page.is_visible("#lead-success")
    # Simula pago en Stripe (mock)
    # Aquí deberías integrar con un entorno de pruebas de Stripe o mockear el webhook
    requests.post(STRIPE_WEBHOOK_URL, json={
        "email": TEST_EMAIL,
        "amount": 1000,
        "affiliate_ref": "AFILIADO123"
    })
    time.sleep(2)  # Espera procesamiento
    # Verifica comisión en dashboard
    page.goto(DASHBOARD_URL)
    page.fill("#login-email", TEST_EMAIL)
    page.click("#login-submit")
    assert page.is_visible("#commission-row-AFILIADO123")

# 2. Cookie Persistence
@pytest.mark.e2e
def test_affiliate_cookie_persistence(browser):
    context = browser.new_context()
    page = context.new_page()
    page.goto(AFFILIATE_LINK)
    # Simula cierre de navegador
    cookies = context.cookies()
    context.close()
    # Reabre navegador al día siguiente
    context2 = browser.new_context()
    context2.add_cookies(cookies)
    page2 = context2.new_page()
    page2.goto("http://localhost:3000/checkout")
    # Simula compra
    page2.click("#pay-now")
    # Verifica que la venta sigue atribuida
    assert page2.is_visible("#attributed-to-AFILIADO123")
    context2.close()

# 3. Security Test: Manipulación de referencia
@pytest.mark.security
def test_affiliate_reference_manipulation(page):
    # Usuario legítimo inicia checkout
    page.goto(AFFILIATE_LINK)
    page.click("#register-lead")
    page.fill("#email", TEST_EMAIL)
    page.click("#submit-lead")
    # Intenta manipular el ID de referencia en el checkout
    page.goto("http://localhost:3000/checkout?ref=OTROAFILIADO")
    page.click("#pay-now")
    # El sistema debe ignorar el ref manipulado y mantener el original
    assert page.is_visible("#attributed-to-AFILIADO123")

# Notas:
# - Ajusta los selectores (#register-lead, #pay-now, etc.) según tu frontend.
# - Integra con Stripe test env o mocks para pagos.
# - Usa variables de entorno/configuración para URLs en producción.
