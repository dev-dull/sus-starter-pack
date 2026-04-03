import base64
import os
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

LABEL_SELECTOR = "managed-by=sus-credential-manager"
MANAGED_BY_LABEL = "sus-credential-manager"


def get_namespace() -> str:
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
            return f.read().strip()
    except FileNotFoundError:
        return os.environ.get("CREDENTIAL_NAMESPACE", "default")


def get_k8s_client():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
    return client.CoreV1Api()


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:63]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.namespace = get_namespace()
    app.state.k8s = get_k8s_client()
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


def list_credentials(k8s: client.CoreV1Api, namespace: str) -> list[dict]:
    secrets = k8s.list_namespaced_secret(
        namespace, label_selector=LABEL_SELECTOR
    )
    creds = []
    for s in secrets.items:
        keys = list(s.data.keys()) if s.data else []
        creds.append(
            {
                "name": s.metadata.name,
                "display_name": s.metadata.annotations.get(
                    "sus.dev/display-name", s.metadata.name
                ),
                "description": s.metadata.annotations.get("sus.dev/description", ""),
                "keys": keys,
                "key_count": len(keys),
            }
        )
    creds.sort(key=lambda c: c["display_name"])
    return creds


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    creds = list_credentials(request.app.state.k8s, request.app.state.namespace)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "creds": creds, "namespace": request.app.state.namespace},
    )


@app.get("/creds/{secret_name}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, secret_name: str):
    k8s = request.app.state.k8s
    ns = request.app.state.namespace
    try:
        secret = k8s.read_namespaced_secret(secret_name, ns)
    except ApiException as e:
        if e.status == 404:
            return HTMLResponse("<p>Credential not found.</p>", status_code=404)
        raise

    data = {}
    if secret.data:
        for k, v in secret.data.items():
            data[k] = base64.b64decode(v).decode()

    display_name = secret.metadata.annotations.get(
        "sus.dev/display-name", secret_name
    )
    description = secret.metadata.annotations.get("sus.dev/description", "")

    return templates.TemplateResponse(
        "partials/edit_form.html",
        {
            "request": request,
            "secret_name": secret_name,
            "display_name": display_name,
            "description": description,
            "data": data,
        },
    )


@app.post("/creds", response_class=HTMLResponse)
async def create_credential(
    request: Request,
    display_name: str = Form(...),
    description: str = Form(""),
    keys: list[str] = Form(...),
    values: list[str] = Form(...),
):
    k8s = request.app.state.k8s
    ns = request.app.state.namespace
    secret_name = slugify(display_name)

    encoded = {
        k: base64.b64encode(v.encode()).decode()
        for k, v in zip(keys, values)
        if k.strip()
    }

    body = client.V1Secret(
        metadata=client.V1ObjectMeta(
            name=secret_name,
            namespace=ns,
            labels={"managed-by": MANAGED_BY_LABEL},
            annotations={
                "sus.dev/display-name": display_name,
                "sus.dev/description": description,
            },
        ),
        data=encoded,
    )

    try:
        k8s.create_namespaced_secret(ns, body)
    except ApiException as e:
        if e.status == 409:
            error = f"A credential named &ldquo;{secret_name}&rdquo; already exists."
            creds = list_credentials(k8s, ns)
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "creds": creds, "namespace": ns, "error": error},
                status_code=409,
            )
        raise

    creds = list_credentials(k8s, ns)
    response = templates.TemplateResponse(
        "partials/cred_list.html",
        {"request": request, "creds": creds},
    )
    response.headers["HX-Trigger"] = "credSaved"
    return response


@app.put("/creds/{secret_name}", response_class=HTMLResponse)
async def update_credential(
    request: Request,
    secret_name: str,
    display_name: str = Form(...),
    description: str = Form(""),
    keys: list[str] = Form(...),
    values: list[str] = Form(...),
):
    k8s = request.app.state.k8s
    ns = request.app.state.namespace

    encoded = {
        k: base64.b64encode(v.encode()).decode()
        for k, v in zip(keys, values)
        if k.strip()
    }

    try:
        secret = k8s.read_namespaced_secret(secret_name, ns)
        secret.data = encoded
        secret.metadata.annotations["sus.dev/display-name"] = display_name
        secret.metadata.annotations["sus.dev/description"] = description
        k8s.replace_namespaced_secret(secret_name, ns, secret)
    except ApiException as e:
        if e.status == 404:
            return HTMLResponse("<p>Credential not found.</p>", status_code=404)
        raise

    creds = list_credentials(k8s, ns)
    response = templates.TemplateResponse(
        "partials/cred_list.html",
        {"request": request, "creds": creds},
    )
    response.headers["HX-Trigger"] = "credSaved"
    return response


@app.delete("/creds/{secret_name}", response_class=HTMLResponse)
async def delete_credential(request: Request, secret_name: str):
    k8s = request.app.state.k8s
    ns = request.app.state.namespace
    try:
        k8s.delete_namespaced_secret(secret_name, ns)
    except ApiException as e:
        if e.status == 404:
            pass  # already gone, still refresh list
        else:
            raise

    creds = list_credentials(k8s, ns)
    return templates.TemplateResponse(
        "partials/cred_list.html",
        {"request": request, "creds": creds},
    )
