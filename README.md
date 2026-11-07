# AegisGate Enterprise
### AI Agent Security Gateway & Validation Lab

**A local AI security engineering project that puts enforceable authorization between AI agents and the tools they use.** Built with Python, FastAPI, Claude, Model Context Protocol (MCP), SQLite, Streamlit, Docker, and automated security tests.

> **Project status:** Implemented and locally demonstrated, including Claude, MCP, and Docker integrations. This is a **training/portfolio prototype**, not a production security service. All identities, documents, events, and tickets are synthetic.

## The problem

AI assistants can request actions through tools, but model instructions alone cannot reliably enforce who may access a document, query security events, or create a ticket. An application needs an independent authorization boundary, auditability, and repeatable tests.

**AegisGate's approach:** the agent may *request* a tool call; the gateway checks the requesting identity, tool, and resource **before executing** the action. Denied requests are recorded for security review.

## Architecture

```text
                 User / local test client
                           |
                           v
                FastAPI /agent/chat
                     |         |
             Demo agent   Claude agent
                     \         /
                      v       v
                  Tool requests
                        |
                        v
               AegisGate gateway  <---- MCP STDIO bridge
                        |
               Identity + RBAC policy
                        |
                 Allow / deny
                        |
            +-----------+------------+
            |           |            |
       Search events  Read docs   Create tickets
            |           |            |
            +-----------+------------+
                        |
               SQLite audit trail
                        |
             Detection / findings
                        |
              Streamlit dashboard
```

**Trust boundary:** Both the Claude tool-use path and the MCP bridge call the same protected gateway. The MCP bridge currently uses a **single server-held demo identity**, not delegated identity from an end user.

## Features

| Capability | Implementation |
| --- | --- |
| Tool authorization | Deny-by-default checks for `search_events`, `read_document`, and `create_ticket` |
| Resource-level permissions | Restricted documents and role-based access rules |
| AI integration | Claude tool-use agent with gateway enforcement; deterministic offline demo agent |
| MCP integration | Local MCP v1 STDIO server exposing three protected tools |
| Audit and detection | Persistent SQLite audit events and repeated-denial findings |
| Security dashboard | Streamlit interface for exploring the lab |
| Validation | **24 automated tests** in the uploaded repository; **27 deterministic authorization scenarios** |
| Delivery | Docker Compose and GitHub Actions CI workflow |

### Example access policy

| Resource / action | Employee (Bob) | Analyst (Alice) | Admin (Carol) |
| --- | :---: | :---: | :---: |
| Read `it_policy` | Allow | Allow | Allow |
| Search `security_events` | Deny | Allow | Allow |
| Read `executive_report` | Deny | Deny | Allow |
| Read `threat_intelligence_report` | Deny | Allow | Allow |
| Create incident ticket | Deny | Allow | Allow |

**Custom engineering addition:** `threat_intelligence_report` was added to the synthetic document dataset and protected by a role-specific authorization policy, with tests for permitted and denied access.

## Demonstration evidence

The repository includes screenshots in [`docs/screenshots/`](docs/screenshots/). A selection:

**FastAPI endpoint documentation**

![FastAPI API documentation](docs/screenshots/Screenshot%202026-11-07%20120549.png)

**Security dashboard**

![AegisGate Streamlit dashboard](docs/screenshots/Screenshot%202026-11-07%20143615.png)

**Deterministic security evaluation**

![Security evaluation output](docs/screenshots/Screenshot%202026-11-07%20115603.png)

Additional terminal screenshots document local development, tests, agent/tool workflows, and integration exercises. Screenshots should be reviewed for exposed tokens, API keys, or other secrets before publishing.

## Quick start — VS Code + WSL Ubuntu

**Requirements:** Python 3.12, [`uv`](https://docs.astral.sh/uv/getting-started/installation/), Git, VS Code with WSL support. Docker Desktop is optional for container deployment.

```bash
# From the repository root
uv python install 3.12
uv sync
uv run pytest -v
uv run python -m scripts.evaluate
```

Start the API:

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000/docs** for interactive API documentation. The `/agent/chat` route accepts **POST**, so opening it directly in a browser tab returns `405 Method Not Allowed`.

### Try an authorization denial

In a second WSL terminal:

```bash
BOB=$(curl -s -X POST http://127.0.0.1:8000/demo/login/bob \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])')

curl -i -X POST http://127.0.0.1:8000/tools/execute \
  -H "Authorization: Bearer $BOB" \
  -H 'Content-Type: application/json' \
  -d '{"tool":"read_document","resource":"executive_report"}'
```

**Expected:** `HTTP 403 Forbidden`. For an allowed document request, use a fresh Carol token from `/demo/login/carol`.

> `/demo/login/{user}` is **intentionally insecure** and issues tokens without credentials. Never expose this API publicly or use it with real information.

## Claude AI integration

```bash
uv sync --extra ai
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY and an available CLAUDE_MODEL
set -a
source .env
set +a
```

Restart the API **after loading the environment**, then obtain a fresh demo token and send a `POST /agent/chat` request with `"mode":"claude"`.

Claude can propose tool calls, but `app/gateway.py` independently checks each action. API usage may incur Anthropic charges. The offline `"mode":"demo"` remains available without an API key.

## MCP integration

```bash
uv sync --extra mcp
# With the FastAPI server running, obtain a fresh Alice token:
ALICE=$(curl -s -X POST http://127.0.0.1:8000/demo/login/alice \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])')
export AEGIS_MCP_DEMO_TOKEN="$ALICE"
uv run python -m app.mcp_server
```

The server uses **STDIO**, so it must be launched by or connected to an MCP-compatible client. It exposes:

- `search_events()` — no arguments
- `read_document(resource: str)`
- `create_ticket(title: str)`

All three call the protected gateway. The MCP server does **not** implement end-user identity delegation; its server-held demo token is for local testing only. Restarting the API can invalidate tokens, so generate a new token after a restart.

## Dashboard and Docker

Run the dashboard in another terminal while the API is running:

```bash
uv sync --extra dashboard
uv run streamlit run app/dashboard.py
```

Or deploy the API with Docker Desktop and WSL integration enabled:

```bash
# Stop a separately running API on port 8000 first
docker compose up --build -d
docker compose ps
curl http://127.0.0.1:8000/health
```

The Compose configuration binds the API to the host's loopback interface (`127.0.0.1:8000`). The dashboard is a separate local process.

## Validation and CI

```bash
uv run pytest -v
uv run python -m scripts.evaluate
uv run ruff check app tests scripts
```

- **24 Pytest tests** were present and reported passing in the uploaded project review. Re-run after any change.
- **27 deterministic scenarios** evaluate authorization outcomes. They are **not** a measured Claude prompt-injection attack-success rate.
- `.github/workflows/ci.yml` runs tests, the evaluation, and Ruff on pushes and pull requests. Confirm the latest workflow run is green before claiming CI success.

## Security model and limitations

- **Training only:** the login route lets anyone obtain any demo user's token.
- **Synthetic data only:** do not connect real enterprise documents, credentials, or production systems.
- **Local only:** do not expose the application or MCP bridge to the public internet.
- **No production identity:** replace demo tokens with verified enterprise identity (for example, OIDC), authorization policies, and per-user MCP delegation before considering real use.
- **Limited AI evaluation:** deterministic authorization tests do not prove broad resistance to prompt injection or malicious tool outputs.
- **Further hardening required:** secrets management, deployment security, monitoring, rate limits, and threat-driven testing.

See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) and [`docs/LEARNING_LABS.md`](docs/LEARNING_LABS.md) for the lab threat model and exercises.

## What this project demonstrates

This project connects **AI engineering** (Claude and MCP tool use), **security engineering** (authorization and resource protection), **security operations** (audit logging and detections), and **DevSecOps** (tests, CI, Docker). It is designed as a reproducible technical case study rather than a claim of production readiness.

## References

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [uv documentation](https://docs.astral.sh/uv/)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)