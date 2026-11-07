# Hands-on learning labs (complete in order)

## Lab 1 — Authorization (30 min)
Run `uv run pytest -v`. Read `app/security.py`. Explain why `authorize` defaults to false. Change one resource permission; write a test that fails before and passes after the change.

## Lab 2 — Enforcement and side effects (30 min)
Read `app/gateway.py`. Prove denied ticket creation leaves `tickets` empty. Add a test for an invalid ticket title. Explain why validation occurs before insertion.

## Lab 3 — API identity (25 min)
Request a Bob demo token and attempt an admin document read. Verify 403. Inspect `/demo/login` and explain why this is not production authentication. Try a forged token and verify 401.

## Lab 4 — Audit and detection (30 min)
Send three denied reads as Bob. Use Carol token to read `/audit`; use Alice token to read `/findings`. Explain the detection threshold and possible false positives.

## Lab 5 — Agent prompt injection (45 min)
Read `injection_sample` as Alice; its text attempts to redirect the agent. Then try to read `executive_report` as Alice. Verify denial. Explain the difference between prompt instructions and enforced permissions.

## Lab 6 — Deterministic evaluation (20 min)
Run `uv run python -m scripts.evaluate` (27 scenarios). Change policy in a temporary branch to allow employee access to executive_report; verify tests/evaluation fail, then revert.

## Lab 7 — Claude (45-90 min; optional paid API)
`uv sync --extra ai`; set `ANTHROPIC_API_KEY` and `CLAUDE_MODEL` in `.env`, then load with `set -a; source .env; set +a`. Request `mode=claude` using `/agent/chat`. Verify the model's tool calls still pass through `execute()`.

## Lab 8 — MCP (45-90 min; optional)
`uv sync --extra mcp`; set `AEGIS_MCP_DEMO_TOKEN` to Alice's token from `/demo/login/alice`; run `uv run python -m app.mcp_server` as a STDIO server using an MCP client. The bridge is local and identity-fixed: do not deploy publicly.

## Lab 9 — Dashboard and Docker (60 min)
`uv sync --extra dashboard`; run `uv run streamlit run app/dashboard.py` with the API running. Run `docker compose up --build -d` and inspect `/health`.

## Lab 10 — Portfolio (45 min)
Document screenshots, test results, 27-scenario evaluation, architecture, limitations, and a 3-minute demo. Explain the design without reading code.
