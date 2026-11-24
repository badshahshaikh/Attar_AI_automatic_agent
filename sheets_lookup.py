"""
sheets_lookup.py
----------------
Live inventory lookup against a Google Sheet.

The sheet is fetched fresh on every call — no caching — so you can edit
prices or stock in Google Sheets and the very next /chat request picks up
the change automatically.

Required environment variables (set in .env):
    GOOGLE_SHEET_ID           – the long ID from the sheet URL
    GOOGLE_SHEET_NAME         – the tab/worksheet name (e.g. "Products")
    GOOGLE_SERVICE_ACCOUNT_JSON – full JSON content of the service-account key file

Expected sheet columns (header row 1):
    product_id | product_name | aliases | size_ml | price | stock_quantity | description

Column names are normalised to lowercase with underscores, so capitalisation
in the sheet header does not matter.
"""

import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Timeout (seconds) for Google Sheets HTTP calls. Prevents a stalled inventory
# request from hanging a worker thread indefinitely.
try:
    GOOGLE_HTTP_TIMEOUT = float(os.getenv("GOOGLE_HTTP_TIMEOUT", "30"))
except (TypeError, ValueError):
    GOOGLE_HTTP_TIMEOUT = 30.0

# ---------------------------------------------------------------------------
# Google Sheets client (lazy-init so import never crashes on missing creds)
# ---------------------------------------------------------------------------

def _build_sheets_service():
    """
    Build and return a Google Sheets API service object.
    Credentials come from the GOOGLE_SERVICE_ACCOUNT_JSON env var.
    Raises a clear RuntimeError if credentials are missing or malformed.
    """
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw_json:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not set. "
            "Add the service-account JSON to your .env file."
        )

    try:
        # Accept either inline JSON or a file path
        if raw_json.startswith("{"):
            creds_dict = json.loads(raw_json)
        else:
            # Treat it as a file path
            with open(raw_json, "r", encoding="utf-8") as f:
                creds_dict = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"Could not parse GOOGLE_SERVICE_ACCOUNT_JSON: {exc}"
        ) from exc

    # Import here so the module can be imported without google-auth installed
    # (useful for running tests on the rest of the codebase)
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google client libraries are not installed. "
            "Run: pip install google-auth google-api-python-client"
        ) from exc

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    # Prefer a client with a finite HTTP timeout so a stalled call cannot hang.
    # Fall back to the standard client if the timeout wiring is unavailable.
    try:
        import httplib2
        from google_auth_httplib2 import AuthorizedHttp

        authed_http = AuthorizedHttp(
            creds, http=httplib2.Http(timeout=GOOGLE_HTTP_TIMEOUT)
        )
        return build("sheets", "v4", http=authed_http, cache_discovery=False)
    except Exception:
        logger.warning(
            "Sheets timeout wiring unavailable; using default client "
            "(GOOGLE_HTTP_TIMEOUT not applied)"
        )
        return build("sheets", "v4", credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------------------
# Fetch all rows from the sheet
# ---------------------------------------------------------------------------

def _fetch_sheet_rows() -> list[dict]:
    """
    Fetch all data rows from the configured Google Sheet.
    Returns a list of dicts keyed by normalised column names.

    Raises RuntimeError with a helpful message on any failure.
    """
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Products").strip()

    if not sheet_id:
        raise RuntimeError(
            "GOOGLE_SHEET_ID is not set in .env. "
            "Copy the ID from your Google Sheet URL."
        )

    service = _build_sheets_service()

    range_name = f"'{sheet_name}'"  # quotes handle sheet names with spaces
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=range_name)
        .execute()
    )

    all_rows = result.get("values", [])
    if not all_rows:
        logger.warning("Google Sheet returned no rows (sheet_id=%s, sheet_name=%s)", sheet_id, sheet_name)
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


# ---------------------------------------------------------------------------
# Public lookup function — called by the AI agent via function-calling
# ---------------------------------------------------------------------------

def lookup_product(product_name: str, size: str | None = None) -> str:
    """
    Search the live Google Sheet inventory for a product.

    Parameters
    ----------
    product_name : str
        The product name or alias the customer mentioned.
        Fuzzy substring match (case-insensitive) against both
        product_name and aliases columns.
    size : str | None
        Optional size filter (e.g. "6", "6ml", "12ml").
        Matched as a substring of the size_ml column.

    Returns
    -------
    str
        JSON string — list of matching product dicts, or [] if nothing found.
        On error, returns {"error": "..."}.
    """
    try:
        rows = _fetch_sheet_rows()
    except RuntimeError as exc:
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
        name_val    = str(row.get("product_name", "")).lower()
        aliases_val = str(row.get("aliases", "")).lower()

        # Substring match on name or any alias token
        if name_lower not in name_val and name_lower not in aliases_val:
            # Also try matching any individual alias token against the query
            alias_tokens = [a.strip() for a in aliases_val.split(",")]
            if not any(name_lower in token or token in name_lower for token in alias_tokens if token):
                continue

        # Optional size filter — match against size_ml column
        if size:
            size_lower = size.strip().lower().replace("ml", "").strip()
            size_val = str(row.get("size_ml") if row.get("size_ml") is not None else row.get("size", "")).lower().replace("ml", "").strip()
            if size_lower not in size_val:
                continue

        matched.append(row)

    return json.dumps(matched, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# OpenAI function-calling schema — unchanged interface from Excel version
# ---------------------------------------------------------------------------

LOOKUP_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "lookup_product",
        "description": (
            "Search the live MS Fragrances Google Sheets inventory for a product. "
            "Call this whenever you need product details: price, stock, sizes, description. "
            "Results are always real-time from the sheet — never guess or invent information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": (
                        "The product name or alias to search for. "
                        "e.g. 'Oud', 'Rose', 'gulab'. "
                        "Use the customer's exact wording — the lookup handles spelling variations."
                    ),
                },
                "size": {
                    "type": "string",
                    "description": (
                        "Optional size to filter by, e.g. '6', '6ml', '12ml'. "
                        "Omit if the customer did not mention a size."
                    ),
                },
            },
            "required": ["product_name"],
        },
    },
}
