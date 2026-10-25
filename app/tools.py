"""Agent tools (@tool decorator). Ticket store abhi in-memory hai — production me DynamoDB / RDS."""
import datetime
import itertools
from functools import lru_cache
from typing import Literal

from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore

from app.config import EMBED_MODEL
from app.knowledge_base import KNOWLEDGE_BASE

TICKETS: dict[str, dict] = {
    "TKT-1001": {"customer": "Rahul", "issue": "Laptop not delivered", "category": "delivery",
                 "priority": "medium", "status": "In Progress", "created": "2026-10-15", "notes": []},
    "TKT-1002": {"customer": "Sneha", "issue": "Refund not received", "category": "refund",
                 "priority": "high", "status": "Resolved", "created": "2026-10-10",
                 "notes": ["Refund processed on 2026-10-14"]},
}
_ticket_counter = itertools.count(1003)


@lru_cache(maxsize=1)
def get_retriever():
    """Vector store pehli query pe banta hai (lazy), taaki app start aur tests bina API call ke chalein."""
    from langchain_openai import OpenAIEmbeddings

    docs = [Document(page_content=f"{title}: {content}", metadata={"id": kb_id, "title": title})
            for kb_id, title, content in KNOWLEDGE_BASE]
    store = InMemoryVectorStore.from_documents(docs, OpenAIEmbeddings(model=EMBED_MODEL))
    return store.as_retriever(search_kwargs={"k": 3})


@tool
def search_knowledge_base(query: str) -> str:
    """Search company policy/FAQ documents. Use this before answering any policy, refund,
    delivery, payment, or account question. Query should be in English."""
    results = get_retriever().invoke(query)
    return "\n\n".join(f"[{d.metadata['id']}] {d.page_content}" for d in results)


@tool
def create_ticket(customer_name: str, issue_summary: str,
                  category: Literal["refund", "delivery", "payment", "account", "product", "other"],
                  priority: Literal["low", "medium", "high", "urgent"]) -> dict:
    """Create a new support ticket when the customer has a problem that needs action or follow-up."""
    tid = f"TKT-{next(_ticket_counter)}"
    TICKETS[tid] = {"customer": customer_name, "issue": issue_summary, "category": category,
                    "priority": priority, "status": "Open",
                    "created": datetime.date.today().isoformat(), "notes": []}
    return {"ticket_id": tid, "status": "Open", "priority": priority}


@tool
def get_ticket_status(ticket_id: str) -> dict:
    """Get the current status and details of an existing ticket by ticket ID (e.g. TKT-1001)."""
    t = TICKETS.get(ticket_id.upper())
    return {"ticket_id": ticket_id.upper(), **t} if t else {"error": f"Ticket {ticket_id} not found"}


@tool
def update_ticket(ticket_id: str, note: str) -> dict:
    """Add a note or new information to an existing ticket."""
    t = TICKETS.get(ticket_id.upper())
    if not t:
        return {"error": f"Ticket {ticket_id} not found"}
    t["notes"].append(note)
    return {"ticket_id": ticket_id.upper(), "updated": True, "notes": t["notes"]}


@tool
def escalate_to_human(ticket_id: str, reason: str) -> dict:
    """Escalate a ticket to a human agent for fraud, legal threats, very angry customers,
    or repeated unresolved issues."""
    t = TICKETS.get(ticket_id.upper())
    if not t:
        return {"error": f"Ticket {ticket_id} not found"}
    t["status"], t["priority"] = "Escalated", "urgent"
    t["notes"].append(f"Escalated: {reason}")
    return {"ticket_id": ticket_id.upper(), "status": "Escalated",
            "message": "A human agent will contact the customer within 4 hours (Mon-Sat, 9AM-9PM IST)."}


TOOLS = [search_knowledge_base, create_ticket, get_ticket_status, update_ticket, escalate_to_human]
