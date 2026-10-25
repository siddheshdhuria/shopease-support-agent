from app.tools import TICKETS, create_ticket, escalate_to_human, get_ticket_status, update_ticket


def test_create_ticket():
    out = create_ticket.invoke({"customer_name": "Amit", "issue_summary": "Money deducted",
                                "category": "payment", "priority": "high"})
    assert out["ticket_id"] in TICKETS
    assert out["status"] == "Open"


def test_get_ticket_status_found_and_case_insensitive():
    out = get_ticket_status.invoke({"ticket_id": "tkt-1001"})
    assert out["customer"] == "Rahul"


def test_get_ticket_status_not_found():
    assert "error" in get_ticket_status.invoke({"ticket_id": "TKT-9999"})


def test_update_and_escalate():
    update_ticket.invoke({"ticket_id": "TKT-1001", "note": "Customer called again"})
    out = escalate_to_human.invoke({"ticket_id": "TKT-1001", "reason": "legal threat"})
    assert out["status"] == "Escalated"
    assert TICKETS["TKT-1001"]["priority"] == "urgent"


def test_tool_schema_generated_by_decorator():
    schema = create_ticket.args_schema.model_json_schema()
    assert set(schema["required"]) == {"customer_name", "issue_summary", "category", "priority"}
    assert "urgent" in schema["properties"]["priority"]["enum"]
