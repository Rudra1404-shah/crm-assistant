import logging
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

logger = logging.getLogger(__name__)

Priority = Literal["Low", "Medium", "High"]
Status = Literal["Open", "Closed"]


class TicketCreate(BaseModel):
    customer_email: str
    company: str
    subject: str
    description: str
    priority: Priority


class Ticket(TicketCreate):
    id: int
    status: Status
    created_at: datetime


tickets_db: dict[int, Ticket] = {}
_next_id = 1


def create_ticket(ticket: TicketCreate) -> Ticket:
    global _next_id
    try:
        new_ticket = Ticket(
            id=_next_id,
            status="Open",
            created_at=datetime.utcnow(),
            **ticket.model_dump(),
        )
        tickets_db[new_ticket.id] = new_ticket
        _next_id += 1
        logger.info(
            "Created ticket %d for %s at %s (priority=%s)",
            new_ticket.id, new_ticket.customer_email, new_ticket.company, new_ticket.priority,
        )
        return new_ticket
    except Exception as e:
        logger.error("Failed to create ticket for %s: %s", ticket.company, e)
        raise


def list_tickets(
    company: str | None = None,
    status: Status | None = None,
    priority: Priority | None = None,
) -> list[Ticket]:
    results = list(tickets_db.values())
    if company is not None:
        results = [t for t in results if t.company.lower() == company.lower()]
    if status is not None:
        results = [t for t in results if t.status == status]
    if priority is not None:
        results = [t for t in results if t.priority == priority]
    logger.info(
        "Retrieved %d ticket(s) (company=%s, status=%s, priority=%s)",
        len(results), company, status, priority,
    )
    return results


def get_ticket(ticket_id: int) -> Ticket | None:
    ticket = tickets_db.get(ticket_id)
    if ticket is None:
        logger.warning("Ticket %d not found", ticket_id)
    return ticket