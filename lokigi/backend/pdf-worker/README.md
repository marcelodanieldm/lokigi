# Lokigi PDF Worker

BullMQ + Puppeteer worker for monthly report PDFs.

## What it does

1. Receives enqueue requests from backend (`POST /enqueue`).
2. Pulls report payload from `monthly_reports`.
3. Generates executive summary (LLM, with fallback).
4. Renders PDF with Lokigi logo + customer brand + sentiment bars + summary.
5. Uploads PDF to S3 and stores signed URL/status back in DB.

## Quick start

```bash
cd backend/pdf-worker
npm install
npm run dev
```

## Required environment variables

- `DATABASE_URL`
- `REDIS_URL`
- `AWS_REGION`
- `AWS_S3_BUCKET`
- `PDF_WORKER_ENQUEUE_TOKEN` (optional but recommended)

## Optional environment variables

- `PDF_WORKER_PORT` (default `4310`)
- `PDF_QUEUE_NAME` (default `monthly-report-pdf`)
- `S3_REPORT_PREFIX` (default `monthly-reports`)
- `PDF_SIGNED_URL_TTL_SECONDS` (default `604800`)
- `LOKIGI_LOGO_URL`
- `APP_DOMAIN`
- `EXEC_SUMMARY_LLM_ENABLED` (`true`/`false`)
- `EXEC_SUMMARY_LLM_API_BASE`
- `EXEC_SUMMARY_LLM_API_KEY`
- `EXEC_SUMMARY_LLM_MODEL`

## Enqueue payload

```json
{
  "report_id": "uuid",
  "signed_url_ttl_seconds": 604800,
  "requested_at": "2026-04-18T18:00:00Z"
}
```
