import logging
import time

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
    retries: int = 2,
    retry_delay: float = 1.5,
) -> list[dict]:
    """Search a module. Use exactly one of criteria (exact field match), word (loose search), or email.
    Retries a couple of times on an empty result, since Zoho's search index can lag a
    few seconds behind a record that was only just created."""
    params = {}
    if criteria:
        params["criteria"] = criteria
    if word:
        params["word"] = word
    if email:
        params["email"] = email

    for attempt in range(retries + 1):
        data = _request("GET", f"{module}/search", params=params)
        results = data.get("data", [])
        if results or attempt == retries:
            logger.info(
                "Search on %s (%s) returned %d record(s) after %d attempt(s)",
                module, params, len(results), attempt + 1,
            )
            return results
        logger.info(
            "Search on %s (%s) returned nothing, retrying in %.1fs (possible indexing lag)",
            module, params, retry_delay,
        )
        time.sleep(retry_delay)
    return []


# ---- Convenience wrappers used by the ticket assistant ----

def list_records(module: str, fields: str, per_page: int = 20) -> list[dict]:
    """List recent records in a module with no search filter. Zoho's plain
    Get Records endpoint returns a stripped-down default field set unless you
    explicitly ask for the fields you want - so `fields` is required here."""
    data = _request("GET", module, params={"fields": fields, "per_page": per_page})
    return data.get("data", [])


def _combine_criteria(*conditions: str) -> str:
    """Join 1-10 Zoho criteria clauses like (Field:equals:Value) with AND."""
    conditions = [c for c in conditions if c]
    if len(conditions) == 1:
        return conditions[0]
    return "(" + "and".join(conditions) + ")"


def get_accounts_by_company(company: str | None = None, industry: str | None = None) -> list[dict]:
    conditions = []
    if company:
        conditions.append(f"(Account_Name:equals:{company})")
    if industry:
        conditions.append(f"(Industry:equals:{industry})")
    if conditions:
        return search_records("Accounts", criteria=_combine_criteria(*conditions))
    return list_records("Accounts", fields="Account_Name,Website,Phone,Industry,Annual_Revenue,Description")


def get_account_by_id(account_id: str) -> dict | None:
    return get_record("Accounts", account_id)


def get_contact_by_email(email: str | None = None) -> list[dict]:
    if email:
        return search_records("Contacts", email=email)
    return list_records("Contacts", fields="First_Name,Last_Name,Email,Phone,Mobile,Title,Account_Name")


def search_leads(
    company: str | None = None,
    email: str | None = None,
    status: str | None = None,
    industry: str | None = None,
    source: str | None = None,
) -> list[dict]:
    """Look up Leads by any combination of company, email, status, industry, or
    source. With none of these, lists recent Leads."""
    if email:
        return search_records("Leads", email=email)

    conditions = []
    if company:
        conditions.append(f"(Company:equals:{company})")
    if status:
        conditions.append(f"(Lead_Status:equals:{status})")
    if industry:
        conditions.append(f"(Industry:equals:{industry})")
    if source:
        conditions.append(f"(Lead_Source:equals:{source})")

    if conditions:
        return search_records("Leads", criteria=_combine_criteria(*conditions))

    return list_records(
        "Leads",
        fields="Company,Last_Name,First_Name,Email,Phone,Lead_Status,Industry,Lead_Source,Website,Description",
    )