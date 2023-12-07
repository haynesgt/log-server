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
async def root():
    return {
        "i": "/i/{id}/{path}",
        "o": "/o",
        "_clear": "/_clear",
    }

@app.get("/_clear")
async def clear():
    log_server_cache_service.clear()
    return {
        "root": "/",
        "message": "cleared",
    }

@app.get("/o")
async def get_ids():
    return {
        "root": "/",
        "ids": [
            "/o/" + id
            for id in
            log_server_cache_service.get_ids()
        ]
    }

@app.get("/o/{id}")
async def get_paths_for_id(id: str):
    return {
        "root": "/",
        "paths": [
            "/o/" + id + "/" + path
            for path in
            log_server_cache_service.get_paths(id)
        ]
    }

@app.get("/o/{id}/{path:path}")
async def get_requests_for_path(id: str, path: str):
    requests = log_server_cache_service.get_requests(id, path)[-10:]
    requests.reverse()
    return {
        "root": "/",
        "o/{id}": "/o/" + id,
        "requests": requests
    }

@app.api_route("/i/{id}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def save_request(id: str, path: str, request: Request):
    now = datetime.utcnow()
    await log_server_cache_service.save_request(id, path, request, now)
    return {
        "root": "/",
        "ts": now.isoformat(),
        "o/{id}": "/o/" + id,
        "o/{id}/{path:path}": "/o/" + id + "/" + path,
    }
