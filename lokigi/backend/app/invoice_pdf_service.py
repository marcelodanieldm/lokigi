"""WeasyPrint invoice PDF generator.

Generates a clean, branded PDF invoice from a BillingInvoice row.
Returns raw bytes that can be streamed as application/pdf.
"""
from __future__ import annotations

import io
import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

# HTML template embedded directly (no extra file needed)
_INVOICE_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <style>
    @page {{ size: A4; margin: 28mm 20mm 24mm 20mm; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 11pt;
      color: #111;
      line-height: 1.5;
    }}
    /* ── Header bar ── */
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 3px solid #4f46e5;
      padding-bottom: 14px;
      margin-bottom: 28px;
    }}
    .brand {{ font-size: 22pt; font-weight: 800; color: #4f46e5; letter-spacing: -0.5px; }}
    .brand sub {{ font-size: 9pt; font-weight: 400; color: #6b7280; display: block; margin-top: 2px; }}
    .invoice-meta {{ text-align: right; font-size: 10pt; color: #374151; }}
    .invoice-meta .inv-number {{ font-size: 14pt; font-weight: 700; color: #111; }}
    /* ── Two-column bill/to ── */
    .parties {{ display: flex; justify-content: space-between; margin-bottom: 28px; }}
    .party-block {{ width: 47%; }}
    .party-block h3 {{ font-size: 8pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af; margin-bottom: 6px; }}
    .party-block p {{ font-size: 10.5pt; color: #111; }}
    /* ── Table ── */
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
    thead tr {{ background: #f3f4f6; }}
    th {{
      font-size: 9pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;
      color: #6b7280; padding: 8px 10px; text-align: left; border-bottom: 1px solid #e5e7eb;
    }}
    td {{ padding: 10px 10px; border-bottom: 1px solid #f3f4f6; font-size: 10.5pt; }}
    tr:last-child td {{ border-bottom: none; }}
    .text-right {{ text-align: right; }}
    /* ── Totals ── */
    .totals {{ margin-left: auto; width: 46%; }}
    .totals-row {{ display: flex; justify-content: space-between; padding: 5px 0; font-size: 10.5pt; }}
    .totals-row.total {{
      font-weight: 800; font-size: 13pt; border-top: 2px solid #111; margin-top: 6px; padding-top: 8px;
    }}
    /* ── Status badge ── */
    .badge {{
      display: inline-block; padding: 3px 10px; border-radius: 999px;
      font-size: 9pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
    }}
    .badge-paid {{ background: #dcfce7; color: #15803d; }}
    .badge-pending {{ background: #fef9c3; color: #854d0e; }}
    .badge-void {{ background: #f3f4f6; color: #6b7280; }}
    /* ── Footer ── */
    .footer {{
      margin-top: 36px; padding-top: 12px; border-top: 1px solid #e5e7eb;
      font-size: 9pt; color: #9ca3af; text-align: center;
    }}
  </style>
</head>
<body>

<div class="header">
  <div>
    <div class="brand">lokigi<sub>Plataforma de Reputación Digital</sub></div>
  </div>
  <div class="invoice-meta">
    <div class="inv-number">{invoice_number}</div>
    <div>Emitida: {issued_date}</div>
    <div>Período: {period_start} – {period_end}</div>
    <div style="margin-top:6px">
      <span class="badge badge-{status_key}">{status_label}</span>
    </div>
  </div>
</div>

<div class="parties">
  <div class="party-block">
    <h3>De</h3>
    <p><strong>lokigi SAS</strong></p>
    <p>hola@lokigi.com</p>
    <p>lokigi.com</p>
  </div>
  <div class="party-block">
    <h3>Para</h3>
    <p><strong>{customer_name}</strong></p>
    <p>{customer_email}</p>
  </div>
</div>

<table>
  <thead>
    <tr>
      <th>Descripción</th>
      <th>Plan</th>
      <th>Período</th>
      <th class="text-right">Importe</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>{description}</td>
      <td><strong>{plan_label}</strong></td>
      <td>{period_start} – {period_end}</td>
      <td class="text-right"><strong>{currency} {amount:.2f}</strong></td>
    </tr>
    {proration_row}
  </tbody>
</table>

<div class="totals">
  <div class="totals-row"><span>Subtotal</span><span>{currency} {amount:.2f}</span></div>
  {proration_total_row}
  <div class="totals-row total"><span>Total</span><span>{currency} {total:.2f}</span></div>
</div>

<div class="footer">
  {invoice_number} · lokigi © {year} · Este documento es un comprobante de pago digital.
</div>

</body>
</html>
"""


def render_invoice_pdf(
    *,
    invoice_number: str,
    issued_date: date,
    period_start: date,
    period_end: date,
    plan: str,
    amount_cents: int,
    currency: str = "USD",
    status: str = "paid",
    customer_name: str = "",
    customer_email: str = "",
    description: str | None = None,
    proration_cents: int = 0,
) -> bytes:
    """Render an invoice to PDF bytes using WeasyPrint."""
    try:
        from weasyprint import HTML as WeasyHTML  # type: ignore
    except ImportError:
        logger.error("WeasyPrint is not installed — cannot generate PDF.")
        raise

    plan_labels = {"starter": "Starter ($39/mo)", "growth": "Growth ($89/mo)", "enterprise": "Enterprise ($299/mo)"}
    status_labels = {"paid": "Pagado", "pending": "Pendiente", "void": "Anulado"}
    status_keys = {"paid": "paid", "pending": "pending", "void": "void"}

    amount = amount_cents / 100
    proration = proration_cents / 100
    total = amount + proration

    if proration_cents != 0:
        sign = "+" if proration_cents > 0 else ""
        proration_row = (
            f"<tr><td>Ajuste por prorrateo</td><td>—</td><td>—</td>"
            f"<td class='text-right'>{sign}{currency} {proration:.2f}</td></tr>"
        )
        proration_total_row = (
            f"<div class='totals-row'><span>Prorrateo</span>"
            f"<span>{sign}{currency} {proration:.2f}</span></div>"
        )
    else:
        proration_row = ""
        proration_total_row = ""

    html_content = _INVOICE_HTML.format(
        invoice_number=invoice_number,
        issued_date=issued_date.strftime("%d %b %Y"),
        period_start=period_start.strftime("%d %b %Y"),
        period_end=period_end.strftime("%d %b %Y"),
        plan_label=plan_labels.get(plan, plan.title()),
        amount=amount,
        currency=currency,
        total=total,
        status_label=status_labels.get(status, status.title()),
        status_key=status_keys.get(status, "paid"),
        customer_name=customer_name or "Cliente lokigi",
        customer_email=customer_email or "",
        description=description or f"Suscripción mensual Plan {plan_labels.get(plan, plan.title())}",
        proration_row=proration_row,
        proration_total_row=proration_total_row,
        year=issued_date.year,
    )

    pdf_bytes = io.BytesIO()
    WeasyHTML(string=html_content).write_pdf(pdf_bytes)
    return pdf_bytes.getvalue()
