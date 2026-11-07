"""Loopback-only training API. Demo tokens are NOT real authentication."""
from typing import Literal
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from app.agent import run_claude, run_demo
from app.gateway import execute
from app.security import Denied, Principal, issue_demo_token, principal_from_token
from app.storage import rows

app = FastAPI(title="AegisGate Enterprise — Local Security Lab", version="1.0")

class ToolInput(BaseModel):
    tool: str
    resource: str
    arguments: dict = Field(default_factory=dict)

class AgentInput(BaseModel):
    prompt: str = Field(min_length=1, max_length=1500)
    mode: Literal["demo", "claude"] = "demo"

def current_principal(authorization: str | None = Header(default=None)) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        return principal_from_token(authorization[7:])
    except Denied:
        raise HTTPException(status_code=401, detail="Invalid token") from None

@app.get("/health")
def health():
    return {"status":"healthy", "mode":"local-training-only"}

@app.post("/demo/login/{user}")
def demo_login(user: str):
    """Intentionally insecure DEMO ONLY: anyone can request any demo user's token."""
    try:
        return {"access_token":issue_demo_token(user),"token_type":"bearer", "warning":"NOT production authentication"}
    except Denied:
        raise HTTPException(status_code=404, detail="unknown demo user") from None

@app.post("/tools/execute")
def tool_execute(body: ToolInput, principal: Principal = Depends(current_principal)):
    try:
        return execute(principal, body.tool, body.resource, body.arguments)
    except Denied:
        raise HTTPException(status_code=403, detail="Forbidden") from None
    except (ValueError, KeyError):
        raise HTTPException(status_code=422, detail="Invalid tool arguments") from None

@app.post("/agent/chat")
def chat(body: AgentInput, principal: Principal = Depends(current_principal)):
    try:
        return run_demo(principal, body.prompt) if body.mode == "demo" else run_claude(principal, body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

@app.get("/audit")
def audit_log(principal: Principal = Depends(current_principal)):
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return rows("audit")

@app.get("/findings")
def findings(principal: Principal = Depends(current_principal)):
    if principal.role not in {"analyst", "admin"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    return rows("findings")

@app.get("/tickets")
def tickets(principal: Principal = Depends(current_principal)):
    if principal.role not in {"analyst", "admin"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    return rows("tickets")
