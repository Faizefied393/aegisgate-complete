"""Local demo authentication and independent authorization.

Demo token issuance is NOT production identity. Replace with OIDC/JWT verification
before exposing to a network or using real data.
"""
import os
import secrets
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from app.data import USERS

# Random on process startup; tokens become invalid after restart.
_KEY = (
    bytes.fromhex(os.environ["AEGIS_DEMO_SIGNING_KEY"])
    if os.getenv("AEGIS_DEMO_SIGNING_KEY")
    else secrets.token_bytes(32)
)

@dataclass(frozen=True)
class Principal:
    user: str
    role: str

class Denied(Exception):
    pass

def issue_demo_token(user: str) -> str:
    if user not in USERS:
        raise Denied("unknown user")
    sig = hmac.new(_KEY, user.encode(), hashlib.sha256).hexdigest()
    return f"{user}.{sig}"

def principal_from_token(token: str) -> Principal:
    try:
        user, signature = token.split(".", 1)
    except ValueError as exc:
        raise Denied("invalid token") from exc
    expected = hmac.new(_KEY, user.encode(), hashlib.sha256).hexdigest()
    if user not in USERS or not hmac.compare_digest(signature, expected):
        raise Denied("invalid token")
    return Principal(user=user, role=USERS[user])

TOOLS = {
    "search_events": {"analyst", "admin"},
    "read_document": {"employee", "analyst", "admin"},
    "create_ticket": {"analyst", "admin"},
}
DOC_ACCESS = {
    "it_policy": {"employee", "analyst", "admin"},
    "soc_runbook": {"analyst", "admin"},
    "executive_report": {"admin"},
    "injection_sample": {"analyst", "admin"},
    "threat_intelligence_report": {"analyst", "admin"},
}

def authorize(principal: Principal, tool: str, resource: str) -> bool:
    if principal.role not in TOOLS.get(tool, set()):
        return False
    if tool == "read_document":
        return principal.role in DOC_ACCESS.get(resource, set())
    if tool == "search_events":
        return resource == "security_events"
    if tool == "create_ticket":
        return resource == "incident_tickets"
    return False
