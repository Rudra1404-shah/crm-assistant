from pydantic import BaseModel, ConfigDict


# ---- Leads ----

class LeadCreate(BaseModel):
    """Required fields we enforce ourselves, before Zoho ever sees the request.
    Any other Zoho Lead field (Phone, Industry, Lead_Status, Website, etc.) is
    still accepted and passed through — it's just not required."""

    model_config = ConfigDict(extra="allow")

    Company: str
    Last_Name: str
    First_Name: str
    Email: str
    Description: str


class LeadUpdate(BaseModel):
    """All fields optional — send only what you actually want to change."""

    model_config = ConfigDict(extra="allow")

    Company: str | None = None
    Last_Name: str | None = None
    First_Name: str | None = None
    Email: str | None = None
    Description: str | None = None
    Phone: str | None = None
    Mobile: str | None = None
    Title: str | None = None
    Lead_Source: str | None = None
    Lead_Status: str | None = None
    Industry: str | None = None
    Website: str | None = None


# ---- Accounts ----

class AccountCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    Account_Name: str
    Website: str | None = None
    Phone: str | None = None
    Industry: str | None = None
    Annual_Revenue: float | None = None
    Description: str | None = None


class AccountUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")

    Account_Name: str | None = None
    Website: str | None = None
    Phone: str | None = None
    Industry: str | None = None
    Annual_Revenue: float | None = None
    Description: str | None = None


# ---- Contacts ----

class AccountLookup(BaseModel):
    """Reference to an existing Account by ID — how Zoho expects a Contact
    to be linked to a company, not a plain string."""

    id: str


class ContactCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    Last_Name: str
    First_Name: str | None = None
    Email: str | None = None
    Phone: str | None = None
    Mobile: str | None = None
    Title: str | None = None
    Account_Name: AccountLookup | None = None


class ContactUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")

    Last_Name: str | None = None
    First_Name: str | None = None
    Email: str | None = None
    Phone: str | None = None
    Mobile: str | None = None
    Title: str | None = None
    Account_Name: AccountLookup | None = None