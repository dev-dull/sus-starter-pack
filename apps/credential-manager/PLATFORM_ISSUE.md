# Platform Issue: Proxy Routing Breaks HTMX Sub-routes

## Summary

The credential manager app (and likely all Python+HTMX apps) cannot make
HTMX requests to any route other than the root because the preview proxy
only routes the root path, not sub-paths.

## What we know

- App runs on port 3000 inside the pod.
- Preview is served at: `http://localhost:9090/build/apps/credential-manager/preview/?pod_ip=...`
- The proxy at port 9090 routes `/build/apps/credential-manager/preview/` → port 3000.

**Confirmed working:**
- `GET /build/apps/credential-manager/preview/` → port 3000 `/` → HTTP 200 ✓

**Confirmed broken:**
- `GET /creds/new/edit` → HTTP 404 (absolute path misses proxy prefix)
- `GET /build/apps/credential-manager/_debug` → HTTP 404 (proxy does not route non-`/preview/` sub-paths)

When using relative HTMX URLs like `creds/new/edit`, the browser resolves
them to `/build/apps/credential-manager/preview/creds/new/edit`, but it is
unknown whether the proxy forwards sub-paths under `/preview/` to port 3000.

## Root cause

HTMX apps need the proxy to forward ALL paths under the app's mount point to
the app server, not just the root. For example:

```
/build/apps/credential-manager/preview/           → port 3000 /
/build/apps/credential-manager/preview/creds/*    → port 3000 /creds/*
/build/apps/credential-manager/preview/creds/new/edit → port 3000 /creds/new/edit
```

Currently only the first rule appears to be active.

## What needs to change at the platform level

The proxy should forward all requests under `/build/apps/{team}/{slug}/preview/`
to the app's port (3000), stripping the `/build/apps/{team}/{slug}/preview`
prefix. This is standard "strip prefix" reverse proxy behaviour, e.g. in nginx:

```nginx
location /build/apps/credential-manager/preview/ {
    proxy_pass http://localhost:3000/;  # trailing slash strips the prefix
}
```

Or in Traefik with a StripPrefix middleware:
```yaml
middlewares:
  strip-prefix:
    stripPrefix:
      prefixes:
        - "/build/apps/credential-manager/preview"
```

Alternatively, the app could be started with uvicorn's `--root-path` flag so
FastAPI is aware of the prefix, but this alone does not fix the proxy routing.

## Workaround attempted (does not work)

Tried using `htmx:configRequest` to prepend the prefix client-side — this
caused HTMX to stop firing requests entirely (likely a HTMX 2.x
incompatibility with modifying `evt.detail.path`).

Tried relative URLs (`hx-get="creds/new/edit"` instead of `/creds/new/edit`)
but it is unclear whether the proxy routes those resolved paths to the app.

## App details

- Path: `/repo/apps/credential-manager/`
- Stack: Python + FastAPI + HTMX 2.0.3
- Port: 3000
- `sus.json` team: apps, slug: credential-manager
