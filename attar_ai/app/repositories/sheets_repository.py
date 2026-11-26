"""
repositories/sheets_repository.py
----------------------------------
Google Sheets repository for live inventory access.
"""

import json
import logging
import os
import time
from typing import Any

import httplib2
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp

from attar_ai.app.core.config import settings
from attar_ai.app.core.exceptions import InventoryError
from attar_ai.app.core.logging import get_logger

logger = get_logger(__name__)


class GoogleSheetsRepository:
    """Repository for accessing Google Sheets inventory data."""

    def __init__(self):
        self._service = None
        self._sheet_id = settings.google_sheet_id
        self._sheet_name = settings.google_sheet_name
        self._timeout = settings.google_http_timeout
        self._max_retries = settings.google_sheets_max_retries
        self._backoff_base = settings.google_sheets_backoff_base

    def _build_service(self):
        """Build and return a Google Sheets API service object."""
        if self._service is not None:
            return self._service

        raw_json = settings.google_service_account_json.strip()
        if not raw_json:
            raise InventoryError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not set. "
                "Add the service-account JSON to your .env file."
            )

        try:
            if raw_json.startswith("{"):
                creds_dict = json.loads(raw_json)
            else:
                with open(raw_json, "r", encoding="utf-8") as f:
                    creds_dict = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            raise InventoryError(f"Could not parse GOOGLE_SERVICE_ACCOUNT_JSON: {exc}") from exc

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

        try:
            authed_http = AuthorizedHttp(
                creds, http=httplib2.Http(timeout=self._timeout)
            )
            self._service = build("sheets", "v4", http=authed_http, cache_discovery=False)
        except Exception:
            logger.warning(
                "Sheets timeout wiring unavailable; using default client "
                "(GOOGLE_HTTP_TIMEOUT not applied)"
            )
            self._service = build("sheets", "v4", credentials=creds, cache_discovery=False)

        return self._service

    def _fetch_sheet_rows(self) -> list[dict]:
        """
        Fetch all data rows from the configured Google Sheet.

        Returns:
            List of dicts keyed by normalized column names.

        Raises:
            InventoryError: On any failure.
        """
        if not self._sheet_id:
            raise InventoryError(
                "GOOGLE_SHEET_ID is not set in .env. "
                "Copy the ID from your Google Sheet URL."
            )

        service = self._build_service()

        range_name = f"'{self._sheet_name}'"  # quotes handle sheet names with spaces

        last_exception = None
        for attempt in range(self._max_retries):
            try:
                result = (
                    service.spreadsheets()
                    .values()
                    .get(spreadsheetId=self._sheet_id, range=range_name)
                    .execute()
                )

                all_rows = result.get("values", [])
                if not all_rows:
                    logger.warning(
                        "Google Sheet returned no rows (sheet_id=%s, sheet_name=%s)",
                        self._sheet_id,
                        self._sheet_name,
                    )
                    return []

                # First row is the header
                raw_headers = all_rows[0]
                headers = [h.strip().lower().replace(" ", "_") for h in raw_headers]

                records = []
                for row in all_rows[1:]:
                    # Pad short rows with empty strings
                    padded = row + [""] * (len(headers) - len(row))
                    record = {headers[i]: padded[i] for i in range(len(headers))}
                    records.append(record)

                logger.info("Fetched %d product rows from Google Sheet", len(records))
                return records

            except Exception as exc:
                last_exception = exc
                if attempt < self._max_retries - 1:
                    wait_time = self._backoff_base ** attempt
                    logger.warning(
                        "Google Sheets request failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        self._max_retries,
                        wait_time,
                        exc,
                    )
                    time.sleep(wait_time)
                else:
                    logger.error("Google Sheets request failed after %d attempts: %s", self._max_retries, exc)

        raise InventoryError(f"Could not read inventory after {self._max_retries} attempts: {last_exception}")

    def lookup_product(self, product_name: str, size: str | None = None) -> str:
        """
        Search the live Google Sheet inventory for a product.

        Args:
            product_name: The product name or alias to search for.
            size: Optional size filter (e.g., "6", "6ml", "12ml").

        Returns:
            JSON string — list of matching product dicts, or [] if nothing found.
            On error, returns {"error": "..."}.
        """
        try:
            rows = self._fetch_sheet_rows()
        except InventoryError as exc:
            logger.error("sheets_lookup error: %s", exc)
            return json.dumps({"error": str(exc)})
        except Exception as exc:
            logger.exception("Unexpected error fetching Google Sheet")
            return json.dumps({"error": f"Could not read inventory: {exc}"})

        if not rows:
            return json.dumps([])

        name_lower = product_name.strip().lower()

        matched = []
        for row in rows:
            name_val = str(row.get("product_name", "")).lower()
            aliases_val = str(row.get("aliases", "")).lower()

            # Substring match on name or any alias token
            if name_lower not in name_val and name_lower not in aliases_val:
                alias_tokens = [a.strip() for a in aliases_val.split(",")]
                if not any(name_lower in token or token in name_lower for token in alias_tokens if token):
                    continue

            # Optional size filter
            if size:
                size_lower = size.strip().lower().replace("ml", "").strip()
                size_val = str(
                    row.get("size_ml") if row.get("size_ml") is not None else row.get("size", "")
                ).lower().replace("ml", "").strip()
                if size_lower not in size_val:
                    continue

            matched.append(row)

        return json.dumps(matched, ensure_ascii=False, default=str)

    def fetch_all_products(self) -> list[dict]:
        """Fetch all products from the sheet (for bulk operations)."""
        return self._fetch_sheet_rows()


# Global repository instance
sheets_repository = GoogleSheetsRepository()