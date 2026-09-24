import logging
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from crm_assistant import redis_store, services
from crm_assistant.agent import agent
from crm_assistant.client import (
    create_record,
    delete_record,
    get_accounts_by_company,
    get_contact_by_email,
    search_leads,
    update_record,
)
from crm_assistant.schemas import (
    AccountCreate,
    AccountUpdate,
    ContactCreate,
    ContactUpdate,
    LeadCreate,
    LeadUpdate,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI CRM Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = Path(__file__).parent / "index.html"


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(FRONTEND_PATH)


def _call_zoho(func, *args, **kwargs):
    """Run a Zoho client call and translate its errors into a proper HTTP response
    instead of letting a Zoho error surface as a raw 500."""
    try:
        return func(*args, **kwargs)
    except requests.HTTPError as e:
        detail = e.response.text if e.response is not None else str(e)
        logger.error("Zoho API error: %s", detail)
        raise HTTPException(status_code=502, detail=f"Zoho API error: {detail}")
    except requests.RequestException as e:
        logger.error("Could not reach Zoho: %s", e)
        raise HTTPException(status_code=502, detail=f"Could not reach Zoho: {e}")


# ---- Chat (Project 3 - the agent, over HTTP) ----


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ToolCallInfo(BaseModel):
    name: str
    result: str


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCallInfo] = []


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    history = redis_store.load_history(request.session_id)
    history.append({"role": "user", "content": request.message})
    start_index = len(history)
    result = agent.invoke({"messages": history})
    new_messages = result["messages"][start_index:]
    tool_calls = [
        ToolCallInfo(name=getattr(m, "name", "tool") or "tool", result=str(m.content))
        for m in new_messages
        if type(m).__name__ == "ToolMessage"
    ]
    history = result["messages"]
    redis_store.save_history(request.session_id, history)
    reply = history[-1].content
    logger.info("Chat[%s] user=%r reply=%r", request.session_id, request.message, reply)
    return ChatResponse(reply=reply, tool_calls=tool_calls)


# ---- Tickets (Project 1 - your own service) ----

@app.post("/tickets", response_model=services.Ticket)
def create_ticket(ticket: services.TicketCreate) -> services.Ticket:
    return services.create_ticket(ticket)


@app.get("/tickets", response_model=list[services.Ticket])
def list_tickets(
    company: str | None = None,
    status: services.Status | None = None,
    priority: services.Priority | None = None,
) -> list[services.Ticket]:
    return services.list_tickets(company=company, status=status, priority=priority)


@app.get("/tickets/{ticket_id}", response_model=services.Ticket)
def get_ticket(ticket_id: int) -> services.Ticket:
    ticket = services.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


# ---- Accounts (Zoho) ----

@app.get("/zoho/accounts")
def zoho_accounts(company: str | None = None, industry: str | None = None):
    return _call_zoho(get_accounts_by_company, company, industry)


@app.post("/zoho/accounts")
def create_account(account: AccountCreate):
    return _call_zoho(create_record, "Accounts", account.model_dump(exclude_none=True))


@app.put("/zoho/accounts/{account_id}")
def update_account(account_id: str, account: AccountUpdate):
    return _call_zoho(
        update_record, "Accounts", account_id, account.model_dump(exclude_none=True)
    )


@app.delete("/zoho/accounts/{account_id}")
def delete_account(account_id: str):
    return _call_zoho(delete_record, "Accounts", account_id)


# ---- Contacts (Zoho) ----

@app.get("/zoho/contacts")
def zoho_contacts(email: str | None = None):
    return _call_zoho(get_contact_by_email, email)


@app.post("/zoho/contacts")
def create_contact(contact: ContactCreate):
    return _call_zoho(create_record, "Contacts", contact.model_dump(exclude_none=True))


@app.put("/zoho/contacts/{contact_id}")
def update_contact(contact_id: str, contact: ContactUpdate):
    return _call_zoho(
        update_record, "Contacts", contact_id, contact.model_dump(exclude_none=True)
    )


@app.delete("/zoho/contacts/{contact_id}")
def delete_contact(contact_id: str):
    return _call_zoho(delete_record, "Contacts", contact_id)


# ---- Leads (Zoho) ----

@app.get("/zoho/leads")
def zoho_leads(
    company: str | None = None,
    email: str | None = None,
    status: str | None = None,
    industry: str | None = None,
    source: str | None = None,
):
    return _call_zoho(search_leads, company=company, email=email, status=status, industry=industry, source=source)


@app.post("/zoho/leads")
def create_lead(lead: LeadCreate):
    return _call_zoho(create_record, "Leads", lead.model_dump(exclude_none=True))


@app.put("/zoho/leads/{lead_id}")
def update_lead(lead_id: str, lead: LeadUpdate):
    return _call_zoho(update_record, "Leads", lead_id, lead.model_dump(exclude_none=True))


@app.delete("/zoho/leads/{lead_id}")
def delete_lead(lead_id: str):
    return _call_zoho(delete_record, "Leads", lead_id)