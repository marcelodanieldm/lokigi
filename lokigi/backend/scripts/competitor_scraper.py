#!/usr/bin/env python
from __future__ import annotations

import json
import os
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


@dataclass
class CompetitorTarget:
    url: str
    zone_label: str | None = None


@dataclass
class ScrapedResult:
    url: str
    name: str | None
    rating_avg: float | None
    review_count_total: int | None
    price_level_raw: str | None
    category: str | None
    address_short: str | None
    posts_30d: int | None
    services: list[str]
    source_status: str


RATING_RE = re.compile(r"([0-5][\.,][0-9])")
REVIEWS_RE = re.compile(r"\(?([0-9][0-9\.,\s]*)\)?\s*(reviews|reseñas)", re.IGNORECASE)
PRICE_RE = re.compile(r"(\${1,4})")
POSTS_30D_RE = re.compile(
    r"(\d+)\s+(publicaciones?|posts?)\s+(en\s+los\s+ultimos\s+30\s+dias|in\s+the\s+last\s+30\s+days)",
    re.IGNORECASE,
)


def _env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and (value is None or value.strip() == ""):
        raise RuntimeError(f"Missing required env var: {name}")
    return value or ""


def _parse_targets(raw: str) -> list[CompetitorTarget]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("COMPETITOR_URLS must be valid JSON") from exc

    if not isinstance(parsed, list):
        raise RuntimeError("COMPETITOR_URLS must be a JSON array")

    targets: list[CompetitorTarget] = []
    for item in parsed:
        if isinstance(item, str):
            url = item.strip()
            if url:
                targets.append(CompetitorTarget(url=url))
            continue
        if isinstance(item, dict):
            url = str(item.get("url") or "").strip()
            if not url:
                continue
            zone_label = str(item.get("zone_label") or "").strip() or None
            targets.append(CompetitorTarget(url=url, zone_label=zone_label))

    if not targets:
        raise RuntimeError("COMPETITOR_URLS contains no valid URLs")

    return targets[:5]


def _wait_random(min_seconds: float, max_seconds: float) -> None:
    wait_s = random.uniform(min_seconds, max_seconds)
    time.sleep(wait_s)


def _first_int(value: str) -> int | None:
    cleaned = re.sub(r"[^0-9]", "", value or "")
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _extract_services(candidates: list[str]) -> list[str]:
    blacklist = {
        "google maps",
        "overview",
        "reviews",
        "reseñas",
        "photos",
        "sitio web",
        "website",
        "directions",
        "call",
        "compartir",
        "share",
    }
    output: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        cleaned = " ".join(item.split())[:80].strip()
        if len(cleaned) < 3:
            continue
        key = cleaned.lower()
        if key in blacklist or key in seen:
            continue
        seen.add(key)
        output.append(cleaned)
    return output[:20]


def _parse_scrape_payload(url: str, payload: dict[str, Any]) -> ScrapedResult:
    body = str(payload.get("body") or "")
    title = str(payload.get("title") or "")
    chips = payload.get("chips") or []

    rating_avg = None
    rating_hit = RATING_RE.search(title) or RATING_RE.search(body)
    if rating_hit:
        try:
            rating_avg = float(rating_hit.group(1).replace(",", "."))
        except ValueError:
            rating_avg = None

    review_count_total = None
    review_hit = REVIEWS_RE.search(body)
    if review_hit:
        review_count_total = _first_int(review_hit.group(1))

    price_level_raw = None
    price_hit = PRICE_RE.search(body)
    if price_hit:
        price_level_raw = price_hit.group(1)

    posts_30d = None
    posts_hit = POSTS_30D_RE.search(body)
    if posts_hit:
        posts_30d = _first_int(posts_hit.group(1))

    lines = [line.strip() for line in body.splitlines() if line.strip()]
    address_short = next((line[:255] for line in lines if re.search(r"\d", line) and len(line) > 8), None)

    name = title.split(" - ")[0].strip()[:120] if title else None
    category = None
    if len(title.split(" - ")) > 1:
        category = title.split(" - ")[1].strip()[:80]

    services = _extract_services([str(x) for x in chips if isinstance(x, str)])
    status = "ok" if rating_avg is not None or review_count_total is not None else "partial"

    return ScrapedResult(
        url=url,
        name=name,
        rating_avg=rating_avg,
        review_count_total=review_count_total,
        price_level_raw=price_level_raw,
        category=category,
        address_short=address_short,
        posts_30d=posts_30d,
        services=services,
        source_status=status,
    )


def _scrape_one(url: str, *, timeout_ms: int, headless: bool, wait_min: float, wait_max: float, user_agent: str) -> ScrapedResult:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            context = browser.new_context(user_agent=user_agent, locale="es-ES", timezone_id="UTC")
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            _wait_random(wait_min, wait_max)
            payload = page.evaluate(
                """
                () => {
                  const body = document.body ? document.body.innerText : '';
                  const title = document.title || '';
                  const chips = Array.from(document.querySelectorAll('button, span, div'))
                    .map(el => (el.textContent || '').trim())
                    .filter(Boolean)
                    .slice(0, 600);
                  return { body, title, chips };
                }
                """
            )
        finally:
            browser.close()

    return _parse_scrape_payload(url, payload)


def _post_with_retry(client: httpx.Client, url: str, *, headers: dict[str, str], payload: dict[str, Any], retries: int = 3) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            backoff = (2 ** (attempt - 1)) + random.uniform(0.2, 0.8)
            time.sleep(backoff)
    raise RuntimeError(f"POST failed after retries: {last_error}")


def main() -> int:
    api_url = _env("LOKIGI_API_URL", required=True).rstrip("/")
    webhook_secret = _env("LOKIGI_WEBHOOK_SECRET", required=True)
    user_id = _env("LOKIGI_USER_ID", required=True)
    targets = _parse_targets(_env("COMPETITOR_URLS", required=True))

    wait_min = float(_env("SCRAPE_WAIT_MIN", "2.5"))
    wait_max = float(_env("SCRAPE_WAIT_MAX", "7.0"))
    timeout_ms = int(_env("PLAYWRIGHT_TIMEOUT_MS", "45000"))
    headless = _env("PLAYWRIGHT_HEADLESS", "true").lower() != "false"
    user_agent = _env(
        "SCRAPER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Secret": webhook_secret,
    }

    logs: list[dict[str, Any]] = []

    start_url = f"{api_url}/internal/growth/competitor-scrape/run/start"
    ingest_url = f"{api_url}/internal/growth/competitor-scrape/ingest"
    finish_url = f"{api_url}/internal/growth/competitor-scrape/run/finish"

    started_at = datetime.now(timezone.utc)

    with httpx.Client() as client:
        run_payload = {
            "user_id": user_id,
            "total_targets": len(targets),
        }
        run_response = _post_with_retry(client, start_url, headers=headers, payload=run_payload)
        run_id = run_response["run_id"]

        success = 0
        failed = 0

        for index, target in enumerate(targets, start=1):
            _wait_random(wait_min, wait_max)
            status = "ok"
            scrape_result: ScrapedResult | None = None
            error_text = None

            for attempt in range(1, 4):
                try:
                    scrape_result = _scrape_one(
                        target.url,
                        timeout_ms=timeout_ms,
                        headless=headless,
                        wait_min=wait_min,
                        wait_max=wait_max,
                        user_agent=user_agent,
                    )
                    break
                except PlaywrightTimeoutError as exc:
                    status = "blocked"
                    error_text = f"timeout attempt {attempt}: {exc}"
                except Exception as exc:
                    status = "error"
                    error_text = f"scrape attempt {attempt}: {exc}"
                time.sleep((2 ** (attempt - 1)) + random.uniform(0.2, 0.8))

            if scrape_result is None:
                failed += 1
                ingest_payload = {
                    "user_id": user_id,
                    "run_id": run_id,
                    "competitor_url": target.url,
                    "zone_label": target.zone_label,
                    "services": [],
                    "source_status": status,
                }
            else:
                if scrape_result.source_status in {"ok", "partial"}:
                    success += 1
                else:
                    failed += 1
                ingest_payload = {
                    "user_id": user_id,
                    "run_id": run_id,
                    "competitor_url": scrape_result.url,
                    "name": scrape_result.name,
                    "zone_label": target.zone_label,
                    "rating_avg": scrape_result.rating_avg,
                    "review_count_total": scrape_result.review_count_total,
                    "price_level_raw": scrape_result.price_level_raw,
                    "category": scrape_result.category,
                    "address_short": scrape_result.address_short,
                    "posts_30d": scrape_result.posts_30d,
                    "services": scrape_result.services,
                    "source_status": scrape_result.source_status,
                }

            try:
                _post_with_retry(client, ingest_url, headers=headers, payload=ingest_payload)
            except Exception as exc:
                failed += 1
                error_text = f"ingest failed: {exc}"

            logs.append(
                {
                    "index": index,
                    "url": target.url,
                    "status": ingest_payload.get("source_status", "error"),
                    "error": error_text,
                }
            )

            _wait_random(wait_min, wait_max + 1.2)

        final_status = "ok" if failed == 0 else ("partial" if success > 0 else "error")
        finish_payload = {
            "user_id": user_id,
            "run_id": run_id,
            "forced_status": final_status,
        }
        _post_with_retry(client, finish_url, headers=headers, payload=finish_payload)

    ended_at = datetime.now(timezone.utc)
    summary = {
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_seconds": int((ended_at - started_at).total_seconds()),
        "processed": len(targets),
        "success": success,
        "failed": failed,
        "status": "ok" if failed == 0 else "partial",
        "items": logs,
    }

    print(json.dumps(summary, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        raise SystemExit(2)
