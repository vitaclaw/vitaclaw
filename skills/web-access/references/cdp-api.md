# Web Access CDP API

VitaClaw vendors a controlled subset of the upstream `web-access` CDP proxy.

## Runtime

- Health check: `http://127.0.0.1:3456/health`
- Start via readiness script: `bash skills/web-access/scripts/check-deps.sh`
- Proxy script: `skills/web-access/scripts/cdp-proxy.mjs`

## Endpoints

### `GET /health`

Returns proxy status, Chrome connection status, and active session count.

### `GET /targets`

Lists current page targets.

### `GET /new?url=...`

Creates a background tab and waits for load completion.

### `GET /close?target=...`

Closes the target tab created for the workflow.

### `GET /navigate?target=...&url=...`

Navigates an existing tab to a new URL.

### `GET /info?target=...`

Returns `title`, `url`, and `readyState`.

### `POST /eval?target=...`

Runs arbitrary JavaScript in the page context. The POST body is the JS expression.

### `POST /click?target=...`

Performs a JS click on the first element matching the CSS selector in the POST body.

### `GET /scroll?target=...&y=...&direction=...`

Scrolls the page to trigger lazy loading. Supports `down`, `up`, `top`, and `bottom`.

### `GET /screenshot?target=...&file=/tmp/shot.png`

Captures a screenshot, optionally writing it to a file.

## VitaClaw Usage

Within VitaClaw, this proxy is primarily consumed through:

- `skills/_shared/web_access_runtime.py`
- `skills/_shared/doctor_profile_harvester.py`

The default policy is public-health read-only browsing. Social posting, payment flows, and personal account automation are out of scope.
