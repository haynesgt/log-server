from datetime import datetime
import json
from typing import TypedDict, overload

import asyncio
from fastapi import Request

CACHE_FILE = ".cache.json"

class LogServerCacheRequestData(TypedDict):
    method: str
    path: str
    headers: dict[str, str]
    query_params: dict[str, str]
    body: bytes

LogServerCachePathData = list[LogServerCacheRequestData]

LogServerCacheIdData = dict[str, LogServerCachePathData]

LogServerCacheData = dict[str, LogServerCacheIdData]

# debounce decorator which calls fn after delay seconds if it was called recently
# or otherwise calls it immediately
def debounce(delay_seconds: float):
    def decorator(fn):
        last_call: datetime | None = None
        last_call_future: asyncio.Future | None = None

        def debounced(*args, **kwargs):
            nonlocal last_call, last_call_future
            if last_call_future is not None:
                return
            now = datetime.utcnow()
            if last_call is None or (now - last_call).total_seconds() > delay_seconds:
                last_call = now
                return fn(*args, **kwargs)
            last_call_future = asyncio.get_running_loop().create_future()
            async def run():
                nonlocal last_call_future
                await asyncio.sleep(delay_seconds)
                last_call_future = None
                return fn(*args, **kwargs)
            asyncio.get_running_loop().create_task(run())
        return debounced
    return decorator

class LogServerCacheService:
    cache: LogServerCacheData

    def __init__(self):
        self.cache = {}
        self.load_from_file()

    def load_from_file(self):
        try:
            with open(CACHE_FILE, "r") as f:
                self.cache = json.load(f)
        except Exception as e:
            print(e)
            pass

    @debounce(1)
    def save_to_file(self):
        with open(CACHE_FILE, "w") as f:
            json.dump(self.cache, f)
    
    def clear(self):
        self.cache = {}
        self.save_to_file()

    async def save_request(self, id: str, path: str, request: Request, now: datetime = datetime.utcnow()):
        self.cache.setdefault(id, {})
        self.cache[id].setdefault(path, [])

        serialized_request = {
            "ts": now.isoformat(),
            "headers": {k.decode(): v.decode() for k, v in request.headers.raw},
            "method": request.method,
            "scheme": request.url.scheme,
            "hostname": request.url.hostname,
            "port": request.url.port,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": str(request.query_params),
            "body": (await request.body()).decode("utf-8"),
        }
        if "Content-Type" in request.headers and request.headers["Content-Type"] == "application/json":
            serialized_request["body"] = request.json()
        self.cache[id][path].append(serialized_request)
        self.save_to_file()
    
    def get_ids(self) -> list[str]:
        return self.cache.keys()

    def get_paths(self, id: str) -> list[str]:
        return [path for path in self.cache.get(id, {}).keys()]

    def get_requests(self, id: str, path) -> LogServerCachePathData:
        return self.cache.get(id, {}).get(path, [])