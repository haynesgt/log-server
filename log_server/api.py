from datetime import datetime
from fastapi import FastAPI, Request

from .log_server_cache_service import LogServerCacheService

"""
Endpoints:

Save a request:
<METHOD> /i/<id>/<path>

Get requests:
GET /o/<id>
GET /o/<id>/<path>
"""

app = FastAPI()

log_server_cache_service = LogServerCacheService()

@app.get("/")
def root():
    return {
        "/": "/",
        "./*": [
            "/i/{path}",
            "/o",
            "/_clear",
        ],
        "description": "A simple server to logs requests. Send to /i/<id>/<path> and view at /o/<id>/<path>",
        "repo": "https://www.github.com/haynesgt/log-server",
    }

@app.get("/_clear")
def clear():
    log_server_cache_service.clear()
    return {
        "/": "/",
        "message": "cleared",
    }

@app.get("/o/{path:path}")
def get_requests_for_path(path: str):
    requests = log_server_cache_service.get_requests(path)[-10:]
    requests.reverse()
    previous_path = "/".join(path.split("/")[:-1])
    return {
        "/": "/",
        "..": "/o/" + previous_path,
        "requests": requests,
    }

@app.api_route("/i/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def save_request(path: str, request: Request):
    now = datetime.utcnow()
    await log_server_cache_service.save_request(path, request, now)
    return {
        "/": "/",
        ".": "/o/" + path,
        "ts": now.isoformat(),
    }
