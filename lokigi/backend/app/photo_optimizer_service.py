"""photo_optimizer_service.py — GPS injection, resize, and SEO alt-text generation.

Pipeline (in order)
────────────────────
1. Resize  — shrink to max 1024 px width while preserving aspect ratio (Pillow).
2. GPS     — inject EXIF GPS IFD (latitude + longitude) using piexif.
3. Alt-text — generate keyword-rich alt-text using either:
              a) OpenAI vision API   (if tip_llm_enabled and key present)
              b) Keyword fallback    (business keywords + basic image analysis)
"""

from __future__ import annotations

import base64
import io
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Optional heavy imports — fail gracefully so the app starts even without them
# ──────────────────────────────────────────────────────────────────────────────

try:
    from PIL import Image, ExifTags  # type: ignore
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    logger.warning("Pillow not installed. resize_image will be a no-op.")

try:
    import piexif  # type: ignore
    _PIEXIF_AVAILABLE = True
except ImportError:
    _PIEXIF_AVAILABLE = False
    logger.warning("piexif not installed. inject_gps will be a no-op.")


# ──────────────────────────────────────────────────────────────────────────────
# 1. Resize
# ──────────────────────────────────────────────────────────────────────────────

MAX_WIDTH = 1024


def resize_image(image_bytes: bytes, max_width: int = MAX_WIDTH) -> tuple[bytes, int, int, int, int]:
    """Resize image to at most ``max_width`` pixels wide.

    Returns
    -------
    (resized_bytes, original_width, original_height, output_width, output_height)
    """
    if not _PIL_AVAILABLE:
        return image_bytes, 0, 0, 0, 0

    img = Image.open(io.BytesIO(image_bytes))
    orig_w, orig_h = img.size
    fmt = img.format or "JPEG"

    if orig_w <= max_width:
        return image_bytes, orig_w, orig_h, orig_w, orig_h

    ratio = max_width / orig_w
    new_h = int(orig_h * ratio)
    resized = img.resize((max_width, new_h), Image.LANCZOS)

    buf = io.BytesIO()
    save_fmt = fmt if fmt in ("JPEG", "PNG", "WEBP") else "JPEG"
    resized.save(buf, format=save_fmt, quality=88, optimize=True)
    return buf.getvalue(), orig_w, orig_h, max_width, new_h


# ──────────────────────────────────────────────────────────────────────────────
# 2. GPS EXIF injection
# ──────────────────────────────────────────────────────────────────────────────


def _decimal_to_dms(decimal: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Convert decimal degrees to (degrees, minutes, seconds) as piexif rational tuples."""
    d = int(abs(decimal))
    m_float = (abs(decimal) - d) * 60
    m = int(m_float)
    s_float = (m_float - m) * 60
    s_num = int(s_float * 100)
    return (d, 1), (m, 1), (s_num, 100)


def inject_gps_metadata(image_bytes: bytes, lat: float, lon: float) -> bytes:
    """Inject GPS coordinates into JPEG/TIFF EXIF metadata.

    Parameters
    ----------
    image_bytes : raw image bytes (JPEG expected; other formats returned unchanged)
    lat         : decimal latitude  (positive = N, negative = S)
    lon         : decimal longitude (positive = E, negative = W)

    Returns
    -------
    Image bytes with GPS EXIF IFD inserted.
    """
    if not _PIEXIF_AVAILABLE:
        return image_bytes

    try:
        # Load existing EXIF or create empty structure
        try:
            exif_dict = piexif.load(image_bytes)
        except Exception:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

        lat_dms = _decimal_to_dms(lat)
        lon_dms = _decimal_to_dms(lon)

        exif_dict["GPS"] = {
            piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S",
            piexif.GPSIFD.GPSLatitude: lat_dms,
            piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W",
            piexif.GPSIFD.GPSLongitude: lon_dms,
        }

        exif_bytes = piexif.dump(exif_dict)
        buf = io.BytesIO()
        img = Image.open(io.BytesIO(image_bytes))
        img.save(buf, format="JPEG", exif=exif_bytes, quality=88)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("GPS injection failed: %s", exc)
        return image_bytes


# ──────────────────────────────────────────────────────────────────────────────
# 3. Alt-text generation
# ──────────────────────────────────────────────────────────────────────────────

_ALT_CLEAN_RE = re.compile(r"\s{2,}")


def _keyword_fallback_alt_text(keywords: list[str], image_bytes: bytes) -> str:
    """Generate a keyword-rich alt-text from business keywords + basic image analysis."""
    if not _PIL_AVAILABLE or not image_bytes:
        parts = keywords[:4]
        return _ALT_CLEAN_RE.sub(" ", "Imagen de " + ", ".join(parts)).strip() if parts else "Imagen del negocio"

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        orientation = "horizontal" if w > h else "vertical" if h > w else "cuadrada"

        # Dominant colour (very rough bucket)
        img_small = img.resize((50, 50))
        pixels = list(img_small.getdata())
        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)
        brightness = (avg_r + avg_g + avg_b) / 3
        tone = "brillante" if brightness > 180 else "cálida" if avg_r > avg_b else "fresca"

        kw_str = ", ".join(keywords[:4]) if keywords else "negocio local"
        return (
            f"Fotografía {orientation} {tone} de {kw_str} — "
            f"imagen optimizada para SEO local"
        )
    except Exception:
        return "Imagen del negocio, optimizada para SEO local"


async def _llm_alt_text(image_bytes: bytes, keywords: list[str], settings: Any) -> str:
    """Call the configured vision-capable LLM to generate alt-text."""
    import httpx

    kw_str = ", ".join(keywords[:6]) if keywords else "negocio local"
    prompt = (
        f"Genera un atributo alt-text SEO para esta imagen en español. "
        f"Incluye las siguientes palabras clave relevantes del negocio: {kw_str}. "
        f"Máximo 120 caracteres. Sólo devuelve el alt-text, sin comillas ni explicaciones."
    )

    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "model": settings.tip_llm_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 80,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{settings.tip_llm_api_base}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {settings.tip_llm_api_key}"},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


async def generate_alt_text(
    image_bytes: bytes,
    keywords: list[str],
    *,
    use_llm: bool = False,
    settings: Any = None,
) -> tuple[str, str]:
    """Generate alt-text. Returns (alt_text, source) where source is 'llm' or 'keyword'."""
    if use_llm and settings and settings.tip_llm_enabled and settings.tip_llm_api_key:
        try:
            text = await _llm_alt_text(image_bytes, keywords, settings)
            return text, "llm"
        except Exception as exc:
            logger.warning("LLM alt-text failed, falling back to keyword: %s", exc)

    return _keyword_fallback_alt_text(keywords, image_bytes), "keyword"


# ──────────────────────────────────────────────────────────────────────────────
# Full pipeline
# ──────────────────────────────────────────────────────────────────────────────


async def optimize_photo(
    image_bytes: bytes,
    *,
    lat: float | None = None,
    lon: float | None = None,
    keywords: list[str] | None = None,
    use_llm: bool = False,
    settings: Any = None,
) -> dict[str, Any]:
    """Run the full optimization pipeline and return a result dict.

    Keys
    ----
    output_bytes : bytes — optimized image
    original_width, original_height, output_width, output_height : int
    resized : bool
    gps_injected : bool
    alt_text : str
    alt_text_source : str  ('llm' | 'keyword')
    """
    kw = keywords or []

    # Step 1 — Resize
    resized_bytes, orig_w, orig_h, out_w, out_h = resize_image(image_bytes)
    was_resized = (out_w != orig_w) and orig_w > 0

    # Step 2 — GPS
    gps_injected = False
    if lat is not None and lon is not None and _PIEXIF_AVAILABLE:
        try:
            resized_bytes = inject_gps_metadata(resized_bytes, lat, lon)
            gps_injected = True
        except Exception as exc:
            logger.warning("GPS step failed: %s", exc)

    # Step 3 — Alt-text
    alt_text, alt_source = await generate_alt_text(
        resized_bytes, kw, use_llm=use_llm, settings=settings
    )

    return {
        "output_bytes": resized_bytes,
        "original_width": orig_w,
        "original_height": orig_h,
        "output_width": out_w,
        "output_height": out_h,
        "resized": was_resized,
        "gps_injected": gps_injected,
        "alt_text": alt_text,
        "alt_text_source": alt_source,
    }
