# QA Automation: Validador de la Cadena de Pago (Lokigi)

## Objetivo
Garantizar que no se pierda ninguna comisión y que el sistema de atribución de afiliados sea infalible.

## Cobertura de la suite
- **End-to-End Tracking:** Simula el flujo completo: Clic en link de afiliado → Navegación → Registro de Lead → Pago en Stripe → Verificación de comisión en el dashboard del socio.
- **Cookie Persistence:** Verifica que si el usuario cierra el navegador y vuelve al día siguiente, la venta siga atribuida al afiliado.
- **Security Test:** Asegura que un afiliado no pueda manipular el ID de referencia en el proceso de checkout para robar comisiones de otros.

## Herramientas
- [Pytest](https://docs.pytest.org/)
- [Playwright](https://playwright.dev/python/)
- [requests](https://docs.python-requests.org/)

## Estructura
- `tests/test_affiliate_payment_chain.py`: Contiene los tests automatizados.
- Selectores y URLs deben ajustarse según el frontend/productivo.

## Ejecución local
1. Instala dependencias:
   ```bash
   pip install pytest playwright requests
   playwright install
   ```
2. Ejecuta los tests:
   ```bash
   pytest tests/test_affiliate_payment_chain.py
   ```

## Integración CI/CD (GitHub Actions)
Agrega el siguiente job a tu workflow `.github/workflows/qa_global_validator.yml`:

```yaml
jobs:
  affiliate-payment-chain:
    runs-on: ubuntu-latest
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
      - name: Run Affiliate Payment Chain QA
        run: pytest tests/test_affiliate_payment_chain.py
```

## Notas
- Usa variables de entorno/configuración para URLs en producción.
- Integra con Stripe test env o mocks para pagos.
- Ajusta los selectores según tu frontend.
- Los tests están marcados con `@pytest.mark.e2e` y `@pytest.mark.security` para filtrado.
