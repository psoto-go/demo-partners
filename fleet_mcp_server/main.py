import os
import requests

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from fastmcp import FastMCP

try:
    from mcp.server.transport_security import TransportSecuritySettings
    security_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)
except ImportError:
    security_settings = None

import google.auth.transport.requests
import google.oauth2.id_token

# Initialize the FastMCP server
if security_settings is not None:
    mcp = FastMCP("Fleet Operations Command Center Manager", transport_security=security_settings)
else:
    mcp = FastMCP("Fleet Operations Command Center Manager")

# Target backend URL and audience (Cloud Run endpoint of the fleet-command-center)
DASHBOARD_URL = os.environ.get(
    "DASHBOARD_URL", 
    "https://fleet-command-center-316438977194.us-central1.run.app"
).rstrip("/")

def get_auth_headers() -> dict:
    """
    Retrieves the ID token to authenticate service-to-service calls on Google Cloud Run.
    Falls back to unauthenticated headers if local development or token retrieval is not available.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    try:
        # Create an auth request
        auth_req = google.auth.transport.requests.Request()
        # Fetch the ID token using the base URL of the target Cloud Run service as the audience
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, DASHBOARD_URL)
        headers["Authorization"] = f"Bearer {id_token}"
        print("Successfully retrieved GCP ID Token for service-to-service authentication.")
    except Exception as e:
        print(f"Skipping Service-to-Service auth (using unauthenticated headers): {e}")
    return headers

@mcp.tool()
def list_shipments() -> str:
    """
    Retrieves all fleet shipments (trucks) currently in the logistics command center.
    
    Returns:
        str: A JSON string containing the list of shipments, their routes, cargo, status, and holds.
    """
    endpoint = f"{DASHBOARD_URL}/api/shipments"
    try:
        headers = get_auth_headers()
        response = requests.get(endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        if hasattr(e, 'response') and e.response is not None:
            return f"Error listing shipments: HTTP {e.response.status_code} - {e.response.text}"
        return f"Error listing shipments: {str(e)}"

@mcp.tool()
def add_shipment(id: str, route: str, cargo: str, status: str = "IN TRANSIT", reason: str = "") -> str:
    """
    Registers and adds a new truck shipment to the fleet operations command center dashboard.
    
    Args:
        id: Unique identifier for the truck, e.g., 'TRK-004'
        route: Start and destination cities, e.g., 'London -> Brussels'
        cargo: Description of the cargo carried, e.g., 'Vaccines & Syringes'
        status: Either 'IN TRANSIT' or 'CUSTOMS HOLD'
        reason: If status is 'CUSTOMS HOLD', details describing the hold blockage.
    """
    endpoint = f"{DASHBOARD_URL}/api/shipments"
    
    # Standardize input ID
    truck_id = id.strip().upper()
    is_resolved = (status != "CUSTOMS HOLD")
    
    payload = {
        "id": truck_id,
        "route": route.strip(),
        "cargo": cargo.strip(),
        "isResolved": is_resolved,
        "status": status.strip().upper(),
        "reason": reason.strip() if not is_resolved else ""
    }
    
    try:
        headers = get_auth_headers()
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return f"Success: Added new shipment {truck_id} to the command center."
    except Exception as e:
        if hasattr(e, 'response') and e.response is not None:
            return f"Error adding shipment: HTTP {e.response.status_code} - {e.response.text}"
        return f"Error adding shipment: {str(e)}"

@mcp.tool()
def resolve_hold(id: str) -> str:
    """
    Resolves an active customs hold for a specific truck, clearing it for transit.
    
    Args:
        id: Unique identifier for the truck to resolve, e.g., 'TRK-001'
    """
    truck_id = id.strip().upper()
    endpoint = f"{DASHBOARD_URL}/api/shipments/{truck_id}/resolve"
    
    try:
        headers = get_auth_headers()
        response = requests.put(endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        return f"Success: Customs hold resolved for truck {truck_id}. Status set to 'CLEARED'."
    except Exception as e:
        if hasattr(e, 'response') and e.response is not None:
            return f"Error resolving hold: HTTP {e.response.status_code} - {e.response.text}"
        return f"Error resolving hold: {str(e)}"

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from contextlib import asynccontextmanager

# Define the Dual ASGI App that routes GET to SSE and POST to Streamable HTTP
class DualMCPSseApp:
    def __init__(self, sse, streamable):
        self.sse = sse
        self.streamable = streamable

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    break
            return

        if scope.get("type") == "http":
            method = scope.get("method", "GET")
            path = scope.get("path", "")
            
            # Normalize double slashes (e.g. "//sse" -> "/sse", "//" -> "/")
            if path.startswith("//"):
                print(f"ASGI Wrapper: Normalizing double slash in path '{path}'")
                path = "/" + path.lstrip("/")
                scope["path"] = path
                raw_path = scope.get("raw_path", b"")
                if raw_path.startswith(b"//"):
                    scope["raw_path"] = b"/" + raw_path.lstrip(b"/")

            # Route POST to streamable_app (Streamable HTTP)
            if method == "POST":
                scope_copy = scope.copy()
                scope_copy["path"] = "/"
                scope_copy["raw_path"] = b"/"
                await self.streamable(scope_copy, receive, send)
            # Route GET to sse_app (SSE Transport)
            else:
                scope_copy = scope.copy()
                scope_copy["path"] = "/sse"
                scope_copy["raw_path"] = b"/sse"
                await self.sse(scope_copy, receive, send)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    # Configure and retrieve the FastMCP apps
    mcp.settings.streamable_http_path = "/"
    streamable_app = mcp.streamable_http_app()
    sse_app = mcp.sse_app()
    
    # Create the dual ASGI application
    dual_app = DualMCPSseApp(sse_app, streamable_app)
    
    # Setup our lifespan context manager to initialize task groups for both apps
    @asynccontextmanager
    async def lifespan(app):
        print("Starting Starlette application, initializing FastMCP lifespans...")
        async with sse_app.router.lifespan_context(sse_app):
            async with streamable_app.router.lifespan_context(streamable_app):
                yield
        print("Shutting down Starlette application...")
        
    # Configure the same routing scheme that succeeded on the workshop manager!
    routes = [
        Route("/", endpoint=dual_app, methods=["GET", "POST"]),
        Route("/mcp/sse", endpoint=dual_app, methods=["GET", "POST"]),
        Route("/mcp/sse/", endpoint=dual_app, methods=["GET", "POST"]),
        Mount("/mcp", sse_app)
    ]
    
    app = Starlette(routes=routes, lifespan=lifespan)
    
    print(f"Starting unified Fleet MCP server on port {port} using uvicorn...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)




