# AI CRM Assistant

An AI orchestration layer that lets a support team interact with **Zoho CRM** (Leads, Accounts, Contacts) using plain natural language, through a chat interface — built with LangChain, FastAPI, Redis, and Pydantic.

## What it can do

Ask the Assistant things like:

- "Show me open leads from Meridian Textiles"
- "Give me leads which are in Lost status"
- "Create a lead for a company called Falkirk Instruments — contact is Daniel Osei, email daniel.osei@falkirkinstruments.com, description: interested in a bulk order"
- "Update the Falkirk Instruments lead, set status to Contacted"
- "Delete the lead for Falkirk Instruments" (it will ask you to confirm first)
- "Search for the account Blue Harbor Logistics"

It supports **search, create, update, and delete** across three Zoho CRM modules:

| Module | Search by | Notes |
|---|---|---|
| Leads | company, email, status, industry, source (any combination) | Create requires Company, Last Name, First Name, Email, Description |
| Accounts | company name, industry | Create requires Account Name |
| Contacts | email | Create requires Last Name; can be linked to an Account by ID |

The assistant asks for missing required information instead of guessing it, and asks for confirmation before deleting anything.

There's also a full web UI (`index.html`) — browse/search/create/edit/delete for all three modules, plus a chat panel that shows which tool the assistant actually called for each answer.

## Architecture

```
Browser (index.html)
    │  fetch()
    ▼
FastAPI app (main.py)
    ├── /tickets/*     → services.py (in-memory ticketing logic — see note below)
    ├── /zoho/*        → client.py (Zoho CRM REST API, via auth.py's OAuth token handling)
    └── /chat          → agent.py (LangChain agent, tools wrap client.py functions)
                              │
                              ▼
                        redis_store.py → Redis (per-session conversation history)
```



## Project layout

```
crm-assistant/
├── main.py              FastAPI app: all HTTP endpoints, CORS, serves index.html at "/"
├── index.html           Frontend — browse/search/CRUD UI + Assistant chat
└── src/crm_assistant/
    ├── auth.py           Zoho OAuth token fetching + auto-refresh
    ├── client.py         Zoho CRM REST client (generic create/update/delete/search)
    ├── schemas.py        Pydantic models enforcing required fields per module
    ├── services.py       Ticketing logic (not currently wired into the agent)
    ├── agent.py          LangChain tools + the agent itself
    └── redis_store.py    Per-session chat history, serialized via langchain_core.load
```

## Setup

### 1. Install dependencies
```bash
uv sync
```

### 2. Get a Redis instance running
```bash
docker run -d -p 6379:6379 --name crm-redis redis:latest
```
(Windows without Docker: [Memurai](https://www.memurai.com/) is a Redis-compatible native alternative.)

### 3. Configure `.env`

Create a `.env` file in the project root — **never commit this file** (it's already in `.gitignore`):

```
OPENAI_API_KEY=sk-...

ZOHO_CLIENT_ID=...
ZOHO_CLIENT_SECRET=...
ZOHO_REFRESH_TOKEN=...

REDIS_URL=redis://localhost:6379/0
```

To get the three Zoho values: register a **Self Client** at the [Zoho API Console](https://api-console.zoho.com/) with scopes `ZohoCRM.modules.ALL,ZohoSearch.securesearch.READ`, generate a grant token, then exchange it once for a refresh token via `POST https://accounts.zoho.in/oauth/v2/token` (use `accounts.zoho.com` if your account is on the US data center — check which domain your Zoho login uses).

### 4. Run it
```bash
uv run fastapi dev main.py
```

Open **http://127.0.0.1:8000/** for the UI, or **http://127.0.0.1:8000/docs** for the raw API (Swagger, auto-generated from the Pydantic schemas).

## Logging

Every ticket action, Zoho API call, and chat turn is logged to the console with a timestamp (configured in `main.py` via `logging.basicConfig`). Tokens and secrets are never logged — only that a refresh happened, not the token itself.

## Known limitations

- The ticketing service (`services.py`) uses in-memory storage and resets on restart — it was never migrated to a real database, since it's no longer part of the agent's active scope.
- Zoho's Search API can lag a few seconds behind a just-created record (`client.py`'s `search_records` retries automatically to absorb this).
- Chat sessions expire from Redis after 24 hours of inactivity.