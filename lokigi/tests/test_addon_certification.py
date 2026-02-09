import pytest
from playwright.sync_api import sync_playwright
import time

ADDON_URLS = [
    # Lista de URLs de 50 add-ons para pruebas
    f"https://widget.example.com/addon{i}" for i in range(1, 51)
]

DASHBOARD_URL = "https://lokigi.app/dashboard"

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

# Performance Test
@pytest.mark.parametrize("addon_url", ADDON_URLS)
def test_addon_performance(browser, addon_url):
    page = browser.new_page()
    page.goto(DASHBOARD_URL)
    start = time.time()
    page.evaluate(f"""
        var iframe = document.createElement('iframe');
        iframe.src = '{addon_url}';
        iframe.sandbox = 'allow-scripts allow-same-origin';
        document.body.appendChild(iframe);
    """)
    page.wait_for_timeout(2000)  # Espera carga
    load_time = time.time() - start
    assert load_time < 2.2  # 2s base + 0.2s tolerancia
    page.close()

# Security Audit
@pytest.mark.parametrize("addon_url", ADDON_URLS)
def test_addon_security(browser, addon_url):
    page = browser.new_page()
    page.goto(DASHBOARD_URL)
    # Simula XSS
    page.evaluate(f"""
        var iframe = document.createElement('iframe');
        iframe.srcdoc = '<script>window.top.postMessage("XSS", "*")</script>';
        iframe.sandbox = 'allow-scripts allow-same-origin';
        document.body.appendChild(iframe);
    """)
    msg = page.wait_for_event('console', timeout=1000)
    assert 'XSS' not in msg.text
    # Simula SQL Injection
    page.evaluate(f"""
        var iframe = document.createElement('iframe');
        iframe.srcdoc = '<form><input value="\' OR 1=1 --"></form>';
        iframe.sandbox = 'allow-scripts allow-same-origin';
        document.body.appendChild(iframe);
    """)
    # No debe afectar dashboard
    assert page.url == DASHBOARD_URL
    page.close()

# Installation Loop
@pytest.mark.parametrize("addon_url", ADDON_URLS)
def test_installation_loop(browser, addon_url):
    page = browser.new_page()
    page.goto(DASHBOARD_URL)
    # Instala add-on
    page.evaluate(f"""
        var iframe = document.createElement('iframe');
        iframe.src = '{addon_url}';
        iframe.sandbox = 'allow-scripts allow-same-origin';
        document.body.appendChild(iframe);
    """)
    page.wait_for_timeout(1000)
    # Desinstala add-on
    page.evaluate("""
        var iframes = document.querySelectorAll('iframe');
        iframes.forEach(f => f.remove());
    """)
    page.wait_for_timeout(500)
    # Verifica que no queden restos
    assert len(page.query_selector_all('iframe')) == 0
    # Verifica memoria
    mem = page.evaluate("window.performance.memory.usedJSHeapSize")
    assert mem < 100 * 1024 * 1024  # <100MB
    page.close()
