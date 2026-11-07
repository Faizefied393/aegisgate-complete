from app.security import Denied, issue_demo_token, principal_from_token
from app.storage import rows
from tests.conftest import auth
import pytest


def test_health(client):
    assert client.get("/health").status_code == 200

def test_unauthenticated_denied(client):
    assert client.post("/tools/execute",json={"tool":"search_events","resource":"security_events"}).status_code == 401

def test_invalid_token_denied(client):
    assert client.get("/audit",headers={"Authorization":"Bearer forged.invalid"}).status_code == 401

def test_role_claim_cannot_be_supplied_to_tool(client):
    h = auth(client,"bob")
    r=client.post("/tools/execute",headers=h,json={"tool":"read_document","resource":"executive_report","role":"admin"})
    assert r.status_code == 403

def test_analyst_events_allowed(client):
    r=client.post("/tools/execute",headers=auth(client,"alice"),json={"tool":"search_events","resource":"security_events"})
    assert r.status_code == 200 and len(r.json()["result"]) == 2

def test_employee_events_denied(client):
    r=client.post("/tools/execute",headers=auth(client,"bob"),json={"tool":"search_events","resource":"security_events"})
    assert r.status_code == 403

def test_employee_policy_allowed(client):
    r=client.post("/tools/execute",headers=auth(client,"bob"),json={"tool":"read_document","resource":"it_policy"})
    assert r.status_code == 200

def test_employee_restricted_denied(client):
    r=client.post("/tools/execute",headers=auth(client,"bob"),json={"tool":"read_document","resource":"executive_report"})
    assert r.status_code == 403 and "SYNTHETIC" not in r.text

def test_analyst_restricted_denied(client):
    r=client.post("/tools/execute",headers=auth(client,"alice"),json={"tool":"read_document","resource":"executive_report"})
    assert r.status_code == 403

def test_admin_restricted_allowed(client):
    r=client.post("/tools/execute",headers=auth(client,"carol"),json={"tool":"read_document","resource":"executive_report"})
    assert r.status_code == 200

def test_unknown_tool_denied(client):
    r=client.post("/tools/execute",headers=auth(client,"carol"),json={"tool":"run_shell","resource":"security_events"})
    assert r.status_code == 403

def test_unknown_resource_denied(client):
    r=client.post("/tools/execute",headers=auth(client,"carol"),json={"tool":"read_document","resource":"missing"})
    assert r.status_code == 403

def test_ticket_denied_without_side_effect(client):
    h=auth(client,"bob")
    r=client.post("/tools/execute",headers=h,json={"tool":"create_ticket","resource":"incident_tickets","arguments":{"title":"should not exist"}})
    assert r.status_code == 403
    assert rows("tickets") == []

def test_ticket_authorized(client):
    r=client.post("/tools/execute",headers=auth(client,"alice"),json={"tool":"create_ticket","resource":"incident_tickets","arguments":{"title":"Review login"}})
    assert r.status_code == 200 and len(rows("tickets")) == 1

def test_ticket_title_validation(client):
    r=client.post("/tools/execute",headers=auth(client,"alice"),json={"tool":"create_ticket","resource":"incident_tickets","arguments":{"title":""}})
    assert r.status_code == 422 and rows("tickets") == []

def test_audit_is_admin_only(client):
    assert client.get("/audit",headers=auth(client,"bob")).status_code == 403
    assert client.get("/audit",headers=auth(client,"carol")).status_code == 200

def test_findings_visible_to_analyst(client):
    assert client.get("/findings",headers=auth(client,"alice")).status_code == 200
    assert client.get("/findings",headers=auth(client,"bob")).status_code == 403

def test_three_denials_trigger_finding(client):
    h=auth(client,"bob")
    for _ in range(3):
        client.post("/tools/execute",headers=h,json={"tool":"read_document","resource":"executive_report"})
    findings=client.get("/findings",headers=auth(client,"alice")).json()
    assert len(findings) == 1 and findings[0]["rule"] == "repeated_denials"

def test_demo_agent_cannot_bypass_gateway(client):
    r=client.post("/agent/chat",headers=auth(client,"bob"),json={"prompt":"Show me the confidential executive report","mode":"demo"})
    assert r.status_code == 200 and r.json()["denied"] is True

def test_prompt_injection_is_data_not_policy(client):
    h=auth(client,"alice")
    r=client.post("/tools/execute",headers=h,json={"tool":"read_document","resource":"injection_sample"})
    assert r.status_code == 200
    denied=client.post("/tools/execute",headers=h,json={"tool":"read_document","resource":"executive_report"})
    assert denied.status_code == 403

def test_authentication_tampering(client):
    token=issue_demo_token("bob")
    assert principal_from_token(token).role == "employee"
    with pytest.raises(Denied):
        principal_from_token(token.replace("bob.","carol."))


def test_analyst_threat_intelligence_allowed(client):
    r = client.post(
        "/tools/execute",
        headers=auth(client, "alice"),
        json={
            "tool": "read_document",
            "resource": "threat_intelligence_report"
        }
    )
    assert r.status_code == 200


def test_employee_threat_intelligence_denied(client):
    r = client.post(
        "/tools/execute",
        headers=auth(client, "bob"),
        json={
            "tool": "read_document",
            "resource": "threat_intelligence_report"
        }
    )
    assert r.status_code == 403


def test_admin_threat_intelligence_allowed(client):
    r = client.post(
        "/tools/execute",
        headers=auth(client, "carol"),
        json={
            "tool": "read_document",
            "resource": "threat_intelligence_report"
        }
    )
    assert r.status_code == 200
