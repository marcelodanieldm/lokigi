#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env.production"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}" >&2
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

if [[ -z "${APP_DOMAIN:-}" ]]; then
  echo "APP_DOMAIN is required in ${ENV_FILE}" >&2
  exit 1
fi

health_status="$(curl -sS -o /tmp/lokigi-health.out -w "%{http_code}" "https://${APP_DOMAIN}/health")"
if [[ "${health_status}" != "200" ]]; then
  echo "Healthcheck failed with status ${health_status}" >&2
  cat /tmp/lokigi-health.out >&2 || true
  exit 1
fi

echo "Health endpoint OK"

webhook_status="$(curl -sS -o /tmp/lokigi-webhook.out -w "%{http_code}" -X POST "https://${APP_DOMAIN}/webhooks/google/reviews" -H "Content-Type: application/json" -d '{}')"
case "${webhook_status}" in
  400|401|422)
    echo "Webhook endpoint reachable with expected status ${webhook_status}"
    ;;
  *)
    echo "Unexpected webhook status ${webhook_status}" >&2
    cat /tmp/lokigi-webhook.out >&2 || true
    exit 1
    ;;
esac

cert_output="$(openssl s_client -connect "${APP_DOMAIN}:443" -servername "${APP_DOMAIN}" < /dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates)"
if [[ -z "${cert_output}" ]]; then
  echo "Could not read TLS certificate for ${APP_DOMAIN}" >&2
  exit 1
fi

echo "TLS certificate detected"
echo "${cert_output}"
