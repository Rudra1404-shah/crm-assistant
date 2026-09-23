import logging

import requests

from .auth import get_access_token

logger = logging.getLogger(__name__)

BASE_URL = "https://www.zohoapis.in/crm/v8"


def _headers(force_refresh: bool = False) -> dict[str, str]:
    return {"Authorization": f"Zoho-oauthtoken {get_access_token(force_refresh=force_refresh)}"}


def _request(method: str, path: str, **kwargs) -> dict:
    try:
        response = requests.request(
            method, f"{BASE_URL}/{path}", headers=_headers(), timeout=10, **kwargs
        )

        if response.status_code == 401:
            logger.warning("%s %s got 401, forcing token refresh and retrying", method, path)
            response = requests.request(
                method, f"{BASE_URL}/{path}", headers=_headers(force_refresh=True),
                timeout=10, **kwargs,
            )

        if response.status_code == 204:
            logger.info("%s %s returned no content", method, path)
            return {"data": []}

        response.raise_for_status()
        logger.info("%s %s succeeded (%s)", method, path, response.status_code)
        return response.json()

    except requests.HTTPError as e:
        detail = e.response.text if e.response is not None else str(e)
        logger.error("%s %s failed: %s", method, path, detail)
        raise
    except requests.RequestException as e:
        logger.error("%s %s could not reach Zoho: %s", method, path, e)
        raise


def create_record(module: str, fields: dict) -> dict:
    """Create one record. `fields` uses Zoho's field API names (e.g. Account_Name, Last_Name)."""
    result = _request("POST", module, json={"data": [fields]})
    record = result["data"][0]
    logger.info("Created %s record id=%s", module, record.get("details", {}).get("id"))
    return record


def update_record(module: str, record_id: str, fields: dict) -> dict:
    """Update one existing record by ID. Only include the fields you want changed."""
    result = _request("PUT", f"{module}/{record_id}", json={"data": [fields]})
    logger.info("Updated %s record id=%s", module, record_id)
    return result["data"][0]


def delete_record(module: str, record_id: str) -> dict:
    """Delete one record by ID."""
    result = _request("DELETE", f"{module}/{record_id}")
    logger.info("Deleted %s record id=%s", module, record_id)
    return result["data"][0]


def get_record(module: str, record_id: str) -> dict | None:
    """Fetch a single record by ID."""
    data = _request("GET", f"{module}/{record_id}")
    records = data.get("data", [])
    return records[0] if records else None


def search_records(
    module: str,
    criteria: str | None = None,
    word: str | None = None,
    email: str | None = None,
) -> list[dict]:
    """Search a module. Use exactly one of criteria (exact field match), word (loose search), or email."""
    params = {}
    if criteria:
        params["criteria"] = criteria
    if word:
        params["word"] = word
    if email:
        params["email"] = email
    data = _request("GET", f"{module}/search", params=params)
    results = data.get("data", [])
    logger.info("Search on %s (%s) returned %d record(s)", module, params, len(results))
    return results


# ---- Convenience wrappers used by the ticket assistant ----

def get_accounts_by_company(company: str) -> list[dict]:
    return search_records("Accounts", criteria=f"(Account_Name:equals:{company})")


def get_account_by_id(account_id: str) -> dict | None:
    return get_record("Accounts", account_id)


def get_contact_by_email(email: str) -> list[dict]:
    return search_records("Contacts", email=email)