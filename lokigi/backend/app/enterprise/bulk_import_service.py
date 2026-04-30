"""
backend/app/enterprise/bulk_import_service.py
===============================================
Pandas-based CSV / Excel bulk location importer for Enterprise onboarding.

Supported input formats
-----------------------
  CSV  (.csv)  — comma or semicolon separated
  Excel (.xlsx / .xls) — first sheet read automatically

Expected columns (case-insensitive, at least ONE is required)
-------------------------------------------------------------
  place_id       Google Maps place_id  (e.g. ChIJN1t_tDeuEmsRUsoyG83frY4)
  address        Street address (fallback if no place_id)
  name           Business / location name
  phone          Optional contact phone
  city           Optional city
  country        Optional ISO-3166-1 alpha-2 country code  (e.g. PE, AR, MX)

Validation rules
----------------
  - place_id must start with "ChIJ" and be ≥ 12 chars  OR
    address must be at least 10 chars
  - Duplicate place_ids within the file are dropped (keep first)
  - Rows already present in `org_locations` for this org are counted as "skipped"

Output
------
  ImportPreview   — returned by preview() for dry-run (no DB writes)
  dict            — returned by commit() after DB insert + Celery dispatch
"""
from __future__ import annotations

import io
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

_PLACE_ID_RE = re.compile(r"^ChIJ[A-Za-z0-9_\-]{8,}$")
_MAX_ROWS    = 5_000      # safety cap per import

# Column aliases (normalised → canonical)
_COL_ALIASES: dict[str, str] = {
    "place_id":  "place_id",
    "placeid":   "place_id",
    "id_place":  "place_id",
    "google_id": "place_id",
    "address":   "address",
    "direccion": "address",
    "dirección": "address",
    "name":      "name",
    "nombre":    "name",
    "local":     "name",
    "location":  "name",
    "phone":     "phone",
    "telefono":  "phone",
    "teléfono":  "phone",
    "city":      "city",
    "ciudad":    "city",
    "country":   "country",
    "pais":      "country",
    "país":      "country",
}


# ─── Pydantic models for the API response ─────────────────────────────────────

class LocationRow(BaseModel):
    row_number: int
    place_id: str | None
    address: str | None
    name: str | None
    phone: str | None
    city: str | None
    country: str | None
    valid: bool
    error: str | None


class ImportPreview(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    preview_sample: list[LocationRow]     # first 20 valid rows
    errors_sample: list[LocationRow]      # first 10 invalid rows
    columns_detected: list[str]


# ─── Service ──────────────────────────────────────────────────────────────────

class BulkImportService:
    """Stateless service — all methods are class-level."""

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def preview(cls, file_obj: io.BytesIO, filename: str) -> ImportPreview:
        """Dry-run: parse + validate, return statistics without writing to DB."""
        df = cls._parse(file_obj, filename)
        df = cls._normalise(df)
        valid, invalid = cls._validate(df)
        valid_deduped, dupes = cls._dedupe_in_file(valid)

        return ImportPreview(
            total_rows     = len(df),
            valid_rows     = len(valid_deduped),
            invalid_rows   = len(invalid),
            duplicate_rows = len(dupes),
            preview_sample = cls._to_rows(valid_deduped.head(20)),
            errors_sample  = cls._to_rows(invalid.head(10)),
            columns_detected = list(df.columns),
        )

    @classmethod
    def commit(
        cls,
        file_obj: io.BytesIO,
        filename: str,
        *,
        org_id: uuid.UUID,
        db: Session,
    ) -> dict:
        """Parse, validate, deduplicate and insert into `org_locations`.
        Returns stats dict with 'inserted', 'skipped', 'total', 'location_ids'."""
        df = cls._parse(file_obj, filename)
        df = cls._normalise(df)
        valid, _invalid = cls._validate(df)
        valid, _dupes   = cls._dedupe_in_file(valid)

        if len(valid) == 0:
            return {"inserted": 0, "skipped": 0, "total": 0, "location_ids": []}

        # Check which place_ids already exist for this org
        existing_ids: set[str] = set()
        place_ids_in_batch = [r for r in valid["place_id"].dropna().tolist() if r]
        if place_ids_in_batch:
            rows = db.execute(
                text("""
                    SELECT place_id FROM org_locations
                    WHERE org_id = :org_id AND place_id = ANY(:ids)
                """),
                {"org_id": str(org_id), "ids": place_ids_in_batch},
            ).fetchall()
            existing_ids = {r[0] for r in rows}

        inserted_ids: list[str] = []
        skipped = 0
        now = datetime.utcnow()

        for _, row in valid.iterrows():
            pid = row.get("place_id") or None
            if pid and pid in existing_ids:
                skipped += 1
                continue
            loc_id = str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO org_locations
                        (id, org_id, place_id, address, name, phone, city, country, created_at)
                    VALUES
                        (:id, :org_id, :place_id, :address, :name, :phone, :city, :country, :created_at)
                    ON CONFLICT (org_id, place_id) DO NOTHING
                """),
                {
                    "id":         loc_id,
                    "org_id":     str(org_id),
                    "place_id":   pid or None,
                    "address":    row.get("address") or None,
                    "name":       row.get("name") or None,
                    "phone":      row.get("phone") or None,
                    "city":       row.get("city") or None,
                    "country":    row.get("country") or None,
                    "created_at": now,
                },
            )
            if pid:
                inserted_ids.append(pid)

        db.flush()   # caller controls commit

        return {
            "inserted": len(inserted_ids),
            "skipped":  skipped,
            "total":    len(valid),
            "location_ids": inserted_ids,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    @classmethod
    def _parse(cls, file_obj: io.BytesIO, filename: str) -> pd.DataFrame:
        """Read CSV or Excel into a DataFrame."""
        ext = Path(filename).suffix.lower()
        try:
            if ext in {".xlsx", ".xls"}:
                df = pd.read_excel(file_obj, sheet_name=0, dtype=str, nrows=_MAX_ROWS)
            else:
                # Try comma first, fall back to semicolon
                raw = file_obj.read()
                try:
                    df = pd.read_csv(io.BytesIO(raw), dtype=str, nrows=_MAX_ROWS)
                    if df.shape[1] < 2:
                        df = pd.read_csv(io.BytesIO(raw), sep=";", dtype=str, nrows=_MAX_ROWS)
                except Exception:
                    df = pd.read_csv(io.BytesIO(raw), sep=";", dtype=str, nrows=_MAX_ROWS)
        except Exception as exc:
            logger.error("Failed to parse import file: %s", exc)
            raise ValueError(f"Cannot read file '{filename}': {exc}") from exc
        return df

    @classmethod
    def _normalise(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Lowercase column names, apply aliases, strip whitespace."""
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        df = df.rename(columns=lambda c: _COL_ALIASES.get(c, c))
        # Keep only known columns; add missing ones as NaN
        for col in ("place_id", "address", "name", "phone", "city", "country"):
            if col not in df.columns:
                df[col] = None
        # Strip whitespace from string columns
        for col in df.columns:
            df[col] = df[col].apply(lambda v: v.strip() if isinstance(v, str) else v)
        # Replace empty strings with NaN
        df = df.replace({"": None})
        return df

    @classmethod
    def _validate(cls, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return (valid_df, invalid_df) based on place_id / address rules."""
        valid_mask = df.apply(cls._row_is_valid, axis=1)
        return df[valid_mask].copy(), df[~valid_mask].copy()

    @staticmethod
    def _row_is_valid(row: pd.Series) -> bool:
        pid  = row.get("place_id")
        addr = row.get("address")
        if pid and isinstance(pid, str) and _PLACE_ID_RE.match(pid):
            return True
        if addr and isinstance(addr, str) and len(addr) >= 10:
            return True
        return False

    @classmethod
    def _dedupe_in_file(cls, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Remove intra-file duplicates by place_id.  Returns (unique, dropped)."""
        mask_has_place_id = df["place_id"].notna()
        unique  = df[~mask_has_place_id].copy()            # rows without place_id kept as-is
        with_id = df[mask_has_place_id].copy()
        duped   = with_id[with_id.duplicated(subset=["place_id"], keep="first")]
        unique  = pd.concat([unique, with_id.drop_duplicates(subset=["place_id"], keep="first")])
        return unique.reset_index(drop=True), duped.reset_index(drop=True)

    @classmethod
    def _to_rows(cls, df: pd.DataFrame) -> list[LocationRow]:
        result = []
        for i, row in df.iterrows():
            pid  = row.get("place_id")
            addr = row.get("address")
            valid = bool(
                (pid  and isinstance(pid, str)  and _PLACE_ID_RE.match(pid)) or
                (addr and isinstance(addr, str) and len(addr) >= 10)
            )
            error = None if valid else "Missing valid place_id or address (≥10 chars)"
            result.append(LocationRow(
                row_number = int(i) + 2,   # 1-indexed + header row
                place_id   = pid or None,
                address    = addr or None,
                name       = row.get("name") or None,
                phone      = row.get("phone") or None,
                city       = row.get("city") or None,
                country    = row.get("country") or None,
                valid      = valid,
                error      = error,
            ))
        return result
