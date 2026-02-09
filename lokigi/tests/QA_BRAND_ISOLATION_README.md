# QA Automation: Validador de Aislamiento de Marca (Multi-tenancy)

## Objetivo
Garantizar que el branding, datos y acceso de cada agencia estén completamente aislados.

## Pruebas incluidas
- **Branding Leak Test:** El reporte de la Agencia A nunca debe mostrar branding de la Agencia B ni de Lokigi.
- **Domain Routing Test:** El middleware debe resolver el tenant correcto según subdominio o dominio custom en menos de 200ms.
- **Stripe Subscription Test:** Si la suscripción de la agencia expira, todos sus clientes pierden acceso (soft-lock).

## Herramientas
- [Pytest](https://docs.pytest.org/)
- [Playwright](https://playwright.dev/python/)
- [requests](https://docs.python-requests.org/)

## Ejecución local
1. Instala dependencias:
   ```bash
   pip install pytest playwright requests
   playwright install
   ```
2. Ejecuta los tests:
   ```bash
   pytest tests/test_brand_isolation.py
   ```

## Integración CI/CD (GitHub Actions)
Agrega el siguiente job a tu workflow `.github/workflows/qa_global_validator.yml`:

```yaml
  brand-isolation:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install pytest playwright requests
          playwright install --with-deps
      - name: Run Brand Isolation QA
        run: pytest tests/test_brand_isolation.py
```

## Notas
- Usa entornos de staging y mocks para pruebas de Stripe y dominios.
- Ajusta los selectores y textos según tu frontend real.
- Extiende los asserts para buscar leaks en CSS, links, favicon, etc.
