"""Optional MCP v1 STDIO bridge using a server-held demo identity.
Run only locally. This bridge has NO end-user identity delegation.
Protected tools call execute(), never bypass it.
"""
import os
from mcp.server.fastmcp import FastMCP
from app.gateway import execute
from app.security import principal_from_token

mcp = FastMCP("AegisGate local MCP bridge")

def identity():
    token = os.getenv("AEGIS_MCP_DEMO_TOKEN", "")
    return principal_from_token(token)

@mcp.tool()
def search_events() -> dict:
    """Search fictional security events under configured demo identity."""
    return execute(identity(), "search_events", "security_events")

@mcp.tool()
def read_document(resource: str) -> dict:
    """Read fictional document under configured demo identity."""
    return execute(identity(), "read_document", resource)

@mcp.tool()
def create_ticket(title: str) -> dict:
    """Create fictional ticket under configured demo identity."""
    return execute(identity(), "create_ticket", "incident_tickets", {"title":title})

if __name__ == "__main__":
    mcp.run(transport="stdio")
