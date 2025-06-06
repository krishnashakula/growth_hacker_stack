import os
import sys
# Ensure the project root is on the import path so test modules can import
# the application packages when running with pytest's default settings.
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Provide a minimal stub for the optional ``praw`` dependency so that tests can
# patch ``praw.Reddit`` even when the library isn't installed.
if 'praw' not in sys.modules:  # pragma: no cover - executed in CI
    import types

    praw_stub = types.ModuleType('praw')

    class Reddit:  # type: ignore
        def __init__(self, *a, **k):
            raise ModuleNotFoundError('praw is required')

    praw_stub.Reddit = Reddit
    sys.modules['praw'] = praw_stub

# Provide a very small stub of ``fastapi.testclient`` when ``httpx`` is not
# installed. This allows the tests to run without pulling in optional
# dependencies.
try:
    from fastapi.testclient import TestClient as _RealTestClient  # type: ignore
except Exception:  # pragma: no cover - executed when httpx is missing
    import types
    from urllib.parse import urlparse, parse_qs

    from fastapi import FastAPI

    class TestClient:  # type: ignore
        def __init__(self, app: FastAPI):
            self.app = app

        def get(self, path: str):
            parsed = urlparse(path)
            query = parse_qs(parsed.query)
            geo = query.get("geo", ["US"])[0]
            limit = int(query.get("limit", ["20"])[0])

            # Find the route matching the path and call its handler directly.
            for route in self.app.routes:
                if getattr(route, "path", None) == parsed.path and "GET" in getattr(route, "methods", []):
                    data = route.endpoint(geo=geo, limit=limit)
                    return types.SimpleNamespace(status_code=200, json=lambda: data)
            raise ValueError(f"No route for {path}")

    # Expose the stub as ``fastapi.testclient``
    module = types.ModuleType("fastapi.testclient")
    module.TestClient = TestClient
    sys.modules.setdefault("fastapi.testclient", module)
