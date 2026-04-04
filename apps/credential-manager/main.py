import base64
import os
import re
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

SUS_API = os.environ.get("SUS_API_URL", "http://sus-landing.sus.svc.cluster.local")
INDEX_SECRET = "cred-mgr-index"
META_DN_PREFIX = "_dn_"
META_DS_PREFIX = "_ds_"


def get_namespace() -> str:
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
            return f.read().strip()
    except FileNotFoundError:
        return os.environ.get("CREDENTIAL_NAMESPACE", "default")


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:63]


def b64key(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def b64decode(s: str) -> str:
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s).decode()


def dn_key(display_name: str) -> str:
    return META_DN_PREFIX + b64key(display_name)


def ds_key(description: str) -> str:
    return META_DS_PREFIX + b64key(description)


def parse_keys(keys: list[str]) -> tuple[str, str, list[str]]:
    display_name = description = ""
    data_keys = []
    for k in keys:
        if k.startswith(META_DN_PREFIX):
            try:
                display_name = b64decode(k[len(META_DN_PREFIX):])
            except Exception:
                pass
        elif k.startswith(META_DS_PREFIX):
            try:
                description = b64decode(k[len(META_DS_PREFIX):])
            except Exception:
                pass
        else:
            data_keys.append(k)
    return display_name, description, data_keys


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.namespace = get_namespace()
    app.state.http = httpx.AsyncClient(base_url=SUS_API, timeout=10.0)
    yield
    await app.state.http.aclose()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


async def list_credentials(http: httpx.AsyncClient) -> list[dict]:
    resp = await http.get(f"/api/secrets/{INDEX_SECRET}")
    if resp.status_code != 200:
        return []

    cred_names = [k for k in resp.json().get("keys", []) if k != "__v1__"]

    creds = []
    for name in cred_names:
        r = await http.get(f"/api/secrets/{name}")
        if r.status_code != 200:
            continue
        display_name, description, data_keys = parse_keys(r.json().get("keys", []))
        creds.append({
            "name": name,
            "display_name": display_name or name,
            "description": description,
            "keys": data_keys,
            "key_count": len(data_keys),
        })

    creds.sort(key=lambda c: c["display_name"])
    return creds


async def index_add(http: httpx.AsyncClient, secret_name: str) -> None:
    resp = await http.get(f"/api/secrets/{INDEX_SECRET}")
    if resp.status_code == 404:
        await http.post("/api/secrets", json={
            "name": INDEX_SECRET,
            "data": {"__v1__": "1", secret_name: "1"},
        })
    else:
        existing = {k: "1" for k in resp.json().get("keys", [])}
        existing[secret_name] = "1"
        existing.setdefault("__v1__", "1")
        await http.put(f"/api/secrets/{INDEX_SECRET}", json={"data": existing})


async def index_remove(http: httpx.AsyncClient, secret_name: str) -> None:
    resp = await http.get(f"/api/secrets/{INDEX_SECRET}")
    if resp.status_code != 200:
        return
    updated = {k: "1" for k in resp.json().get("keys", []) if k != secret_name}
    updated.setdefault("__v1__", "1")
    await http.put(f"/api/secrets/{INDEX_SECRET}", json={"data": updated})


async def render_index(request: Request, error: str = "") -> HTMLResponse:
    creds = await list_credentials(request.app.state.http)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "creds": creds,
            "namespace": request.app.state.namespace,
            "error": error,
        },
    )


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    action: str = Query(None),
    secret_name: str = Query(""),
    display_name: str = Query(""),
    description: str = Query(""),
    keys: list[str] = Query(default=[]),
    values: list[str] = Query(default=[]),
):
    http = request.app.state.http

    if action == "delete":
        await http.delete(f"/api/secrets/{secret_name}")
        await index_remove(http, secret_name)
        return await render_index(request)

    if action == "create":
        name = slugify(display_name)
        data = {k: v for k, v in zip(keys, values) if k.strip()}
        data[dn_key(display_name)] = "1"
        if description:
            data[ds_key(description)] = "1"

        resp = await http.post("/api/secrets", json={"name": name, "data": data})
        if resp.status_code != 200 or resp.json().get("status") != "created":
            error = f'Could not create credential \u201c{name}\u201d \u2014 it may already exist.'
            return await render_index(request, error=error)

        await index_add(http, name)
        return await render_index(request)

    if action == "update":
        check = await http.get(f"/api/secrets/{secret_name}")
        if check.status_code == 404:
            return await render_index(request, error="Credential not found.")

        data = {k: v for k, v in zip(keys, values) if k.strip() and v.strip()}
        data[dn_key(display_name)] = "1"
        if description:
            data[ds_key(description)] = "1"

        resp = await http.put(f"/api/secrets/{secret_name}", json={"data": data})
        if resp.status_code != 200:
            return await render_index(request, error="Failed to update credential.")
        return await render_index(request)

    return await render_index(request)
