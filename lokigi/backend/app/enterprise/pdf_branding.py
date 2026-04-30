"""
backend/app/enterprise/pdf_branding.py
=========================================
WeasyPrint PDF renderer with full agency white-label support.

How it works
------------
1.  `BrandedPDFRenderer` receives a `BrandTheme` (from ThemeService) at init.
2.  It fills a Jinja2 HTML template with the theme variables (logo, colors,
    agency name, contact email, footer text).
3.  WeasyPrint converts the rendered HTML to PDF bytes in-memory — no temp files.
4.  The logo is embedded as a base64 Data URI so the PDF is fully self-contained
    and requires no filesystem access when served.

Usage
-----
    from app.enterprise.pdf_branding import BrandedPDFRenderer
    from app.enterprise.white_label import theme_service

    theme = theme_service.get_theme(domain=host, db=db)
    renderer = BrandedPDFRenderer(theme=theme)

    pdf_bytes = renderer.render_monthly_report(
        location_name="Restaurante La Pepita",
        period_label="Abril 2026",
        stats={"avg_rating": 4.7, "total_reviews": 142, "response_rate": 0.96},
        reviews=reviews_list,
    )

    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="informe.pdf"'})

WeasyPrint installation
-----------------------
    pip install weasyprint
    # On Linux: apt-get install libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0

Logo embedding
--------------
If `theme.logo_url` is a URL (http/https), the renderer fetches it and embeds
it as base64.  If it starts with `data:`, it is used as-is.
If no logo is set, the agency name is rendered as styled text.
"""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ─── PDF Config dataclass ─────────────────────────────────────────────────────

@dataclass
class PDFBrandingConfig:
    """
    Overrides for PDF-specific branding.  These layer on top of the base
    BrandTheme when rendering reports.
    """
    header_logo_width: int   = 160      # px
    header_logo_position: str = "left"  # "left" | "center" | "right"
    show_page_numbers: bool  = True
    show_powered_by: bool    = False    # False = hide Lokigi branding
    footer_left: str         = "{agency_name} · {agency_email}"
    footer_right: str        = "Informe generado el {date}"
    report_language: str     = "es"


# ─── Jinja2 HTML template for PDF ────────────────────────────────────────────

_PDF_TEMPLATE = """<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
<meta charset="utf-8" />
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: {{ font_family }};
    font-size: 11px;
    color: #1c1917;
    background: #fff;
  }
  @page {
    size: A4;
    margin: 14mm 12mm 18mm 12mm;
    @top-left { content: ""; }
    @bottom-left {
      content: "{{ footer_left }}";
      font-size: 9px; color: #9ca3af;
    }
    @bottom-right {
      content: "{{ footer_right }}{% if show_page_numbers %}  ·  Página " counter(page) " de " counter(pages){% endif %}";
      font-size: 9px; color: #9ca3af;
    }
  }

  /* Header */
  .pdf-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding-bottom: 12px;
    margin-bottom: 18px;
    border-bottom: 3px solid {{ primary_color }};
  }
  .pdf-header .logo img  { max-width: {{ logo_width }}px; max-height: 40px; }
  .pdf-header .logo-text {
    font-size: 16px; font-weight: 900; color: {{ primary_color }};
    letter-spacing: -0.5px;
  }
  .pdf-header .report-meta { text-align: right; }
  .pdf-header .report-meta .title {
    font-size: 13px; font-weight: 700; color: #1f2937;
    text-transform: uppercase; letter-spacing: .05em;
  }
  .pdf-header .report-meta .subtitle { font-size: 10px; color: #6b7280; margin-top: 2px; }

  /* Section titles */
  h2 {
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; color: {{ primary_color }};
    margin: 18px 0 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid #e5e7eb;
  }

  /* KPI grid */
  .kpi-grid { display: flex; gap: 8px; margin-bottom: 16px; }
  .kpi-box {
    flex: 1; text-align: center; padding: 10px 8px;
    background: #eff6ff; border-radius: 8px;
  }
  .kpi-box .value { font-size: 20px; font-weight: 900; color: {{ primary_color }}; }
  .kpi-box .label { font-size: 9px; color: #6b7280; margin-top: 2px; }

  /* Rating bar */
  .rating-row { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
  .rating-label { width: 22px; font-size: 10px; color: #6b7280; }
  .bar-track { flex: 1; height: 7px; background: #e5e7eb; border-radius: 4px; }
  .bar-fill  { height: 100%; border-radius: 4px; background: {{ primary_color }}; }
  .bar-pct   { width: 30px; text-align: right; font-size: 10px; color: #6b7280; }

  /* Reviews table */
  table { width: 100%; border-collapse: collapse; margin-top: 6px; }
  thead th {
    background: {{ primary_color }}; color: #fff;
    font-size: 9px; font-weight: 700; text-transform: uppercase;
    padding: 6px 8px; text-align: left;
  }
  tbody tr:nth-child(even) { background: #f9fafb; }
  tbody td { padding: 6px 8px; font-size: 10px; color: #374151; vertical-align: top; }

  /* Insight box */
  .insight {
    padding: 10px 12px; border-radius: 8px; margin: 10px 0;
    border-left: 4px solid {{ primary_color }};
    background: #eff6ff;
    font-size: 10px; color: #1e3a8a;
  }

  /* Page break */
  .page-break { page-break-after: always; }

  /* Footer note (only when powered_by is True) */
  .powered-by {
    text-align: center; font-size: 8px; color: #d1d5db;
    margin-top: 24px; padding-top: 8px;
    border-top: 1px solid #f3f4f6;
  }
</style>
</head>
<body>

<!-- ── HEADER ── -->
<div class="pdf-header">
  <div class="logo">
    {% if logo_b64 %}
    <img src="{{ logo_b64 }}" alt="{{ agency_name }}" />
    {% else %}
    <div class="logo-text">{{ agency_name }}</div>
    {% endif %}
  </div>
  <div class="report-meta">
    <div class="title">Informe de Reputación</div>
    <div class="subtitle">{{ period_label }}</div>
    <div class="subtitle">{{ location_name }}</div>
  </div>
</div>

<!-- ── KPIs ── -->
<h2>Resumen del período</h2>
<div class="kpi-grid">
  <div class="kpi-box">
    <div class="value">{{ stats.avg_rating }}★</div>
    <div class="label">Nota media</div>
  </div>
  <div class="kpi-box">
    <div class="value">{{ stats.total_reviews }}</div>
    <div class="label">Total reseñas</div>
  </div>
  <div class="kpi-box">
    <div class="value">{{ (stats.response_rate * 100) | round(0) | int }}%</div>
    <div class="label">Respondidas</div>
  </div>
  <div class="kpi-box">
    <div class="value">{{ stats.new_reviews }}</div>
    <div class="label">Nuevas este mes</div>
  </div>
</div>

<!-- ── RATING DISTRIBUTION ── -->
<h2>Distribución de valoraciones</h2>
{% for star, count, pct in rating_distribution %}
<div class="rating-row">
  <div class="rating-label">{{ star }}★</div>
  <div class="bar-track"><div class="bar-fill" style="width:{{ pct }}%"></div></div>
  <div class="bar-pct">{{ pct }}%</div>
</div>
{% endfor %}

<!-- ── INSIGHT ── -->
{% if insight_text %}
<div class="insight">💡 {{ insight_text }}</div>
{% endif %}

<!-- ── RECENT REVIEWS ── -->
<h2>Últimas reseñas del período</h2>
<table>
  <thead>
    <tr>
      <th style="width:80px">Fecha</th>
      <th style="width:40px">★</th>
      <th>Comentario</th>
      <th style="width:80px">Respuesta</th>
    </tr>
  </thead>
  <tbody>
    {% for r in reviews %}
    <tr>
      <td>{{ r.date }}</td>
      <td>{{ r.rating }}★</td>
      <td>{{ r.comment | truncate(120) }}</td>
      <td>{{ "✓ Respondida" if r.replied else "Pendiente" }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

{% if show_powered_by %}
<div class="powered-by">Informe generado con tecnología Lokigi Enterprise</div>
{% endif %}

</body>
</html>"""


# ─── Renderer class ───────────────────────────────────────────────────────────

class BrandedPDFRenderer:
    """
    Renders white-labeled PDF reports using WeasyPrint + Jinja2.

    Parameters
    ----------
    theme : BrandTheme
        The resolved agency theme (from ThemeService).
    pdf_config : PDFBrandingConfig | None
        PDF-specific branding overrides.  Defaults to PDFBrandingConfig().
    """

    def __init__(self, theme, pdf_config: PDFBrandingConfig | None = None) -> None:
        self._theme  = theme
        self._config = pdf_config or PDFBrandingConfig()
        self._jinja_env = self._make_jinja_env()

    # ── Public API ────────────────────────────────────────────────────────────

    def render_monthly_report(
        self,
        *,
        location_name: str,
        period_label: str,
        stats: dict[str, Any],
        reviews: list[dict[str, Any]],
        insight_text: str = "",
    ) -> bytes:
        """
        Render a monthly reputation report for a single location.

        Parameters
        ----------
        location_name : str
            Human-readable name of the Google Business location.
        period_label : str
            e.g. "Abril 2026"
        stats : dict
            Keys: avg_rating (float), total_reviews (int),
                  response_rate (float 0-1), new_reviews (int)
        reviews : list[dict]
            Each dict: {date, rating, comment, replied}
        insight_text : str
            Optional IA-generated insight sentence shown in a callout box.
        """
        rating_distribution = self._compute_rating_distribution(reviews)
        html = self._render_template(
            location_name=location_name,
            period_label=period_label,
            stats=stats,
            reviews=reviews[:20],   # cap at 20 rows to keep PDF manageable
            insight_text=insight_text,
            rating_distribution=rating_distribution,
        )
        return self._html_to_pdf(html)

    def render_executive_summary(
        self,
        *,
        org_name: str,
        period_label: str,
        totals: dict[str, Any],
        top_locations: list[dict[str, Any]],
    ) -> bytes:
        """
        Two-page executive summary for the whole network.
        Uses the same template base with a simplified stats dict.
        """
        stats = {
            "avg_rating":     totals.get("network_avg_rating", 0),
            "total_reviews":  totals.get("total_reviews", 0),
            "response_rate":  totals.get("response_rate", 0),
            "new_reviews":    totals.get("new_reviews", 0),
        }
        html = self._render_template(
            location_name=org_name,
            period_label=period_label,
            stats=stats,
            reviews=top_locations,
            insight_text=(
                f"Tu red de {totals.get('total_locations', 0)} locales alcanzó "
                f"un Brand Authority Index de {totals.get('network_brand_authority', 0):.0f}/100 "
                f"en {period_label}."
            ),
            rating_distribution=[],
        )
        return self._html_to_pdf(html)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _render_template(self, **kwargs: Any) -> str:
        logo_b64 = self._get_logo_b64()
        now = datetime.now(timezone.utc)

        footer_left = self._config.footer_left.format(
            agency_name=self._theme.agency_name,
            agency_email=self._theme.agency_email or "",
        )
        footer_right = self._config.footer_right.format(
            date=now.strftime("%d/%m/%Y"),
        )

        tpl = self._jinja_env.from_string(_PDF_TEMPLATE)
        return tpl.render(
            # Branding
            primary_color=self._theme.primary_color,
            secondary_color=self._theme.secondary_color,
            font_family=self._theme.font_family,
            agency_name=self._theme.agency_name,
            logo_b64=logo_b64,
            logo_width=self._config.header_logo_width,
            # Footer
            footer_left=footer_left,
            footer_right=footer_right,
            show_page_numbers=self._config.show_page_numbers,
            show_powered_by=self._config.show_powered_by,
            # Content
            lang=self._config.report_language,
            **kwargs,
        )

    def _html_to_pdf(self, html: str) -> bytes:
        """Convert HTML to PDF bytes using WeasyPrint."""
        try:
            from weasyprint import HTML as WeasyHTML
            return WeasyHTML(string=html).write_pdf()
        except ImportError:
            logger.error(
                "WeasyPrint is not installed. "
                "Run: pip install weasyprint"
            )
            raise

    def _get_logo_b64(self) -> str | None:
        """
        Return the logo as a base64 Data URI for embedding in the PDF.
        Returns None if no logo is configured.
        """
        logo_url = self._theme.logo_url
        if not logo_url:
            return None
        if logo_url.startswith("data:"):
            return logo_url

        # Fetch remote URL and encode as base64
        try:
            import urllib.request
            with urllib.request.urlopen(logo_url, timeout=5) as resp:  # nosec — URL from trusted DB
                raw = resp.read()
            content_type = resp.headers.get("Content-Type", "image/svg+xml")
            encoded = base64.b64encode(raw).decode()
            return f"data:{content_type};base64,{encoded}"
        except Exception as exc:
            logger.warning("Could not fetch logo %s: %s", logo_url, exc)
            return None

    @staticmethod
    def _compute_rating_distribution(
        reviews: list[dict[str, Any]]
    ) -> list[tuple[int, int, float]]:
        """
        Returns list of (star, count, pct) tuples sorted 5→1.
        """
        from collections import Counter
        counts: Counter[int] = Counter()
        for r in reviews:
            rating = int(r.get("rating", 0))
            if 1 <= rating <= 5:
                counts[rating] += 1
        total = sum(counts.values()) or 1
        return [
            (star, counts[star], round(counts[star] / total * 100, 1))
            for star in range(5, 0, -1)
        ]

    @staticmethod
    def _make_jinja_env():
        try:
            from jinja2 import Environment
            env = Environment(autoescape=True)
            return env
        except ImportError:
            logger.error("Jinja2 is not installed. Run: pip install jinja2")
            raise


# ─── FastAPI endpoint helper ──────────────────────────────────────────────────

def make_pdf_router(pdf_config: PDFBrandingConfig | None = None):
    """
    Returns a FastAPI APIRouter exposing PDF download endpoints.
    Mount at /enterprise/pdf.

    Requires:
        - ThemeMiddleware registered (sets request.state.theme)
        - get_current_org dependency (from multi_tenancy)
    """
    from fastapi import APIRouter, Depends
    from fastapi.responses import Response as FastAPIResponse
    from sqlalchemy.orm import Session
    from app.enterprise.multi_tenancy import Organization, get_current_org
    from app.database import get_db

    router = APIRouter(prefix="/enterprise/pdf", tags=["enterprise-pdf"])

    @router.get("/monthly/{location_id}")
    def download_monthly_report(
        location_id: str,
        period: str = "current",
        request=None,
        org: Organization = Depends(get_current_org),
        db: Session = Depends(get_db),
    ):
        """
        Generate and stream a branded monthly PDF for a location.
        The PDF reflects the agency's logo and colors — not Lokigi's.
        """
        theme = getattr(request.state, "theme", None)
        if theme is None:
            from app.enterprise.white_label import DEFAULT_THEME
            theme = DEFAULT_THEME

        renderer = BrandedPDFRenderer(theme=theme, pdf_config=pdf_config)

        # TODO: replace with real DB queries
        pdf_bytes = renderer.render_monthly_report(
            location_name=location_id,
            period_label=period,
            stats={
                "avg_rating": 4.7,
                "total_reviews": 142,
                "response_rate": 0.96,
                "new_reviews": 12,
            },
            reviews=[],
        )

        return FastAPIResponse(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="informe_{location_id}_{period}.pdf"'
                )
            },
        )

    return router
