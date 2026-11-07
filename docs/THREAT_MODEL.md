# Threat model
Assets: confidential synthetic documents, event data, ticket creation, audit integrity.
Trust boundaries: user-to-API, model-to-tool request, MCP bridge-to-executor, gateway-to-database.
Threats: role impersonation, prompt injection, unknown tool, unauthorized document access, unauthorized write, audit suppression, runaway tool calls.
Controls implemented: deny-by-default role/resource checks, single execution boundary, tamper-evident demo tokens within process, SQLite audit trail, bounded Claude loop, synthetic fixtures, localhost binding.
Important gaps: demo login allows impersonation by design; no real OIDC, no per-tenant ownership, no human approval for high-impact tools, no distributed tracing, no production-grade audit immutability, no rate limiting, no durable secrets management. Never use with real company data.
