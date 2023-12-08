from datetime import datetime
import json
from typing import Any, Literal, Never, Sequence, TypedDict, overload

import asyncio
from fastapi import Request

CACHE_FILE = ".cache.json"


class LogServerCacheRequestData(TypedDict):
    ts: str | None
    headers: dict[str, str] | None
    method: str | None
    url: str | None
    scheme: str | None
    hostname: str | None
    port: int | None
    path: str | None
    query_params: str | None
    body: str | None
    json: Any | None


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


PathCache = dict[str, "PathCache"]


def get_all_paths(path_cache: PathCache) -> list[str]:
    paths = []
    for path, subpath_cache in path_cache.items():
        paths.append(path)
        paths += [path + "/" + subpath for subpath in get_all_paths(subpath_cache)]
    return paths


class LogServerCacheService:
    request_cache: dict[str, list[LogServerCacheRequestData]]
    path_cache: PathCache
    loaded: bool

    def __init__(self):
        self.request_cache = {}
        self.path_cache = {}
        self.loaded = False

    def load(self):
        if self.loaded:
            return
        self.loaded = True
        self.load_from_file()
        for path, requests in self.request_cache.items():
            self.find_path_cache_part(path)

    def load_from_file(self):
        try:
            with open(CACHE_FILE, "r") as f:
                self.request_cache = json.load(f)
        except FileNotFoundError:
            pass

    @debounce(1)
    def save_to_file(self):
        with open(CACHE_FILE, "w") as f:
            json.dump(self.request_cache, f, indent=2)

    def clear(self):
        self.request_cache = {}
        self.save_to_file()

    async def save_request(
        self, path: str, request: Request
    ) -> LogServerCacheRequestData:
        self.load()
        serialized_request: LogServerCacheRequestData = {
            "ts": datetime.utcnow().isoformat(),
            "headers": {k.decode(): v.decode() for k, v in request.headers.raw},
            "method": request.method,
            "url": str(request.url),
            "scheme": request.url.scheme,
            "hostname": request.url.hostname,
            "port": request.url.port,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "body": None,
            "json": None,
        }
        if (
            "Content-Type" in request.headers
            and request.headers["Content-Type"] == "application/json"
        ):
            serialized_request["json"] = await request.json()
        else:
            serialized_request["body"] = (await request.body()).decode("utf-8")

        self.request_cache.setdefault(path, [])
        self.request_cache[path].append(serialized_request)

        self.find_path_cache_part(path)
        self.save_to_file()
        return serialized_request

    def get_requests(self, path: str) -> list[LogServerCacheRequestData]:
        self.load()
        return self.request_cache.get(path, [])

    def get_subpaths(self, path: str) -> list[str]:
        if path.endswith("*"):
            if "/" in path:
                path, end = path.rsplit("/", 1)
            else:
                end = path
                path = ""
            cache_part = self.find_path_cache_part(path)
            if end == "**":
                all_paths = get_all_paths(cache_part)
                return [(path + "/" if path else "") + subpath for subpath in all_paths]
            if end == "*":
                return [*cache_part.keys()]
        return [
            (path + "/" if path else "") + subpath
            for subpath in self.find_path_cache_part(path).keys()
        ]

    def find_path_cache_part(self, path: str) -> PathCache:
        self.load()
        path_parts = path.split("/")
        cache_part = self.path_cache
        for part in path_parts:
            if part == "":
                continue
            next_cache_part = cache_part.setdefault(part, {})
            cache_part = next_cache_part
        return cache_part
