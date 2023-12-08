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
        "*": [
            "/i/test/path",
            "/o",
            "/o/**",
            "/_clear",
            "/_db",
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


@app.get("/_db")
def db():
    log_server_cache_service.load()
    return {
        "/": "/",
        "request_cache": log_server_cache_service.request_cache,
        "path_cache": log_server_cache_service.path_cache,
    }


@app.get("/o/{path:path}")
def get_requests_for_path(path: str):
    requests = log_server_cache_service.get_requests(path)[-10:]
    requests.reverse()
    previous_path = "/".join(path.split("/")[:-1])

    return {
        "/": "/",
        "..": "/o/" + previous_path,
        "*": [
            "/o/" + subpath for subpath in log_server_cache_service.get_subpaths(path)
        ],
        "**": "/o/" + ((path + "/" if path else "") + "**").replace("**/**", "**"),
        "requests": requests,
    }


@app.api_route(
    "/i/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def save_request(path: str, request: Request):
    request_info = await log_server_cache_service.save_request(path, request)
    return {
        "/": "/",
        "o": "/o/" + path,
        "ts": request_info["ts"],
    }
