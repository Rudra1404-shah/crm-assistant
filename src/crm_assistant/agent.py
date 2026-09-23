import logging

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool

from crm_assistant.client import (
    create_record,
    delete_record,
    get_accounts_by_company,
    get_contact_by_email,
    search_leads as find_leads,
    update_record,
)

load_dotenv()

logger = logging.getLogger(__name__)


# ---- Accounts ----

@tool
def search_accounts(company: str) -> str:
    """Look up a company's Account record in the CRM by exact name."""
    accounts = get_accounts_by_company(company)
    if not accounts:
        return f"No account found for '{company}'."
    acc = accounts[0]
    return (
        f"id={acc.get('id')}, Account_Name={acc.get('Account_Name')}, "
        f"industry={acc.get('Industry')}, phone={acc.get('Phone')}, website={acc.get('Website')}"
    )


@tool
def create_account(
    account_name: str,
    website: str | None = None,
    phone: str | None = None,
    industry: str | None = None,
    description: str | None = None,
) -> str:
    """Create a new Account (company) in the CRM. account_name is required."""
    fields = {"Account_Name": account_name}
    if website:
        fields["Website"] = website
    if phone:
        fields["Phone"] = phone
    if industry:
        fields["Industry"] = industry
    if description:
        fields["Description"] = description
    record = create_record("Accounts", fields)
    return f"Created account, id={record['details']['id']}."


@tool
def update_account(
    account_id: str,
    account_name: str | None = None,
    website: str | None = None,
    phone: str | None = None,
    industry: str | None = None,
    description: str | None = None,
) -> str:
    """Update an existing Account by ID. Only include fields you want changed."""
    fields = {}
    if account_name:
        fields["Account_Name"] = account_name
    if website:
        fields["Website"] = website
    if phone:
        fields["Phone"] = phone
    if industry:
        fields["Industry"] = industry
    if description:
        fields["Description"] = description
    update_record("Accounts", account_id, fields)
    return f"Updated account {account_id}."


@tool
def delete_account(account_id: str) -> str:
    """Delete an Account by ID. This cannot be undone - confirm with the user first."""
    delete_record("Accounts", account_id)
    return f"Deleted account {account_id}."


# ---- Contacts ----

@tool
def search_contacts(email: str) -> str:
    """Look up a Contact in the CRM by email address."""
    contacts = get_contact_by_email(email)
    if not contacts:
        return f"No contact found for '{email}'."
    c = contacts[0]
    account = c.get("Account_Name") or {}
    return (
        f"id={c.get('id')}, {c.get('First_Name')} {c.get('Last_Name')}, "
        f"phone={c.get('Phone')}, company={account.get('name')}"
    )


@tool
def create_contact(
    last_name: str,
    first_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    mobile: str | None = None,
    title: str | None = None,
    account_id: str | None = None,
) -> str:
    """Create a new Contact in the CRM. last_name is required. Pass account_id
    to link this contact to an existing Account (look it up with search_accounts first)."""
    fields = {"Last_Name": last_name}
    if first_name:
        fields["First_Name"] = first_name
    if email:
        fields["Email"] = email
    if phone:
        fields["Phone"] = phone
    if mobile:
        fields["Mobile"] = mobile
    if title:
        fields["Title"] = title
    if account_id:
        fields["Account_Name"] = {"id": account_id}
    record = create_record("Contacts", fields)
    return f"Created contact, id={record['details']['id']}."


@tool
def update_contact(
    contact_id: str,
    last_name: str | None = None,
    first_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    mobile: str | None = None,
    title: str | None = None,
    account_id: str | None = None,
) -> str:
    """Update an existing Contact by ID. Only include fields you want changed."""
    fields = {}
    if last_name:
        fields["Last_Name"] = last_name
    if first_name:
        fields["First_Name"] = first_name
    if email:
        fields["Email"] = email
    if phone:
        fields["Phone"] = phone
    if mobile:
        fields["Mobile"] = mobile
    if title:
        fields["Title"] = title
    if account_id:
        fields["Account_Name"] = {"id": account_id}
    update_record("Contacts", contact_id, fields)
    return f"Updated contact {contact_id}."


@tool
def delete_contact(contact_id: str) -> str:
    """Delete a Contact by ID. This cannot be undone - confirm with the user first."""
    delete_record("Contacts", contact_id)
    return f"Deleted contact {contact_id}."


# ---- Leads ----

@tool
def search_leads(company: str | None = None, email: str | None = None) -> str:
    """Look up a Lead by company name or email address. Provide at least one.
    Use this to find a Lead's id before updating or deleting it, if the user
    only gave you a name/company/email rather than an id."""
    leads = find_leads(company=company, email=email)
    if not leads:
        return "No lead found matching those filters."
    l = leads[0]
    return (
        f"id={l.get('id')}, {l.get('First_Name')} {l.get('Last_Name')} "
        f"at {l.get('Company')}, status={l.get('Lead_Status')}"
    )


@tool
def create_lead(
    company: str,
    last_name: str,
    first_name: str,
    email: str,
    description: str,
) -> str:
    """Create a new Lead. All five fields are required - ask the user for any
    that are missing instead of guessing."""
    fields = {
        "Company": company,
        "Last_Name": last_name,
        "First_Name": first_name,
        "Email": email,
        "Description": description,
    }
    record = create_record("Leads", fields)
    return f"Created lead, id={record['details']['id']}."


@tool
def update_lead(
    lead_id: str,
    company: str | None = None,
    last_name: str | None = None,
    first_name: str | None = None,
    email: str | None = None,
    description: str | None = None,
    phone: str | None = None,
    lead_status: str | None = None,
) -> str:
    """Update an existing Lead by ID. Only include fields you want changed."""
    fields = {}
    if company:
        fields["Company"] = company
    if last_name:
        fields["Last_Name"] = last_name
    if first_name:
        fields["First_Name"] = first_name
    if email:
        fields["Email"] = email
    if description:
        fields["Description"] = description
    if phone:
        fields["Phone"] = phone
    if lead_status:
        fields["Lead_Status"] = lead_status
    update_record("Leads", lead_id, fields)
    return f"Updated lead {lead_id}."


@tool
def delete_lead(lead_id: str) -> str:
    """Delete a Lead by ID. This cannot be undone - confirm with the user first."""
    delete_record("Leads", lead_id)
    return f"Deleted lead {lead_id}."


tools = [
    search_accounts, create_account, update_account, delete_account,
    search_contacts, create_contact, update_contact, delete_contact,
    search_leads, create_lead, update_lead, delete_lead,
]

SYSTEM_PROMPT = """You are a CRM assistant with access to Zoho CRM Accounts, Contacts,
and Leads. Use the tools available to search, create, update, and delete these records
based on the user's request.

If the user wants to update or delete a record but only gave you a name, company, or
email rather than an id, call the matching search tool first to find the id, then use
that id in the update/delete call - do this automatically, without asking the user for
the id yourself. Only ask the user for missing information if the search comes back
with no match, or with more than one possible match and you genuinely can't tell which
one they mean.

Never guess a required value for create (like Company, Last_Name, Email) - ask the user
if it's missing. Before deleting anything, confirm with the user that they actually want
to delete it, since it cannot be undone."""

agent = create_agent("openai:gpt-4o-mini", tools=tools, system_prompt=SYSTEM_PROMPT)


if __name__ == "__main__":
    print("CRM Assistant — type 'quit' to exit\n")
    messages: list = []
    while True:
        user_input = input("> ")
        if user_input.strip().lower() in ("quit", "exit"):
            break
        messages.append({"role": "user", "content": user_input})
        result = agent.invoke({"messages": messages})
        messages = result["messages"]  # carry full history (incl. tool calls) into the next turn
        print(messages[-1].content, "\n")