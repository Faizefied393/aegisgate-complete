"""Single trusted execution path for ALL protected tools."""
from uuid import uuid4
from app.data import DOCUMENTS, EVENTS
from app.security import Denied, Principal, authorize
from app.storage import audit, connect, utc_now

def execute(principal: Principal, tool: str, resource: str, args: dict | None = None):
    trace_id = str(uuid4())
    args = args or {}
    if not authorize(principal, tool, resource):
        audit(principal.user, tool, resource, "DENY", "NOT_EXECUTED", trace_id)
        raise Denied("tool or resource not permitted")
    try:
        if tool == "search_events":
            result = list(EVENTS)
        elif tool == "read_document":
            result = dict(DOCUMENTS[resource])
        elif tool == "create_ticket":
            title = args.get("title")
            if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160:
                raise ValueError("ticket title must be 1-160 characters")
            with connect() as db:
                cursor = db.execute("INSERT INTO tickets (title,created_by,ts) VALUES (?,?,?)", (title.strip(),principal.user,utc_now()))
                db.commit()
                result = {"ticket_id": cursor.lastrowid, "title": title.strip(), "status": "open"}
        else:
            raise Denied("unknown tool")
    except Exception:
        audit(principal.user, tool, resource, "ALLOW", "ERROR", trace_id)
        raise
    audit(principal.user, tool, resource, "ALLOW", "EXECUTED", trace_id)
    return {"trace_id": trace_id, "result": result}
