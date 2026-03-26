#!/usr/bin/env python3
"""Multi-channel push dispatcher for VitaClaw health notifications.

Delivers push_issues via one or more channels with priority-based routing.

Channels:
    feishu  — Feishu Open API bot message
    macos   — macOS native notification (osascript / terminal-notifier)
    bark    — Bark iOS push (self-hosted or public)
    webhook — Generic HTTP POST webhook

Environment variables:
    VITACLAW_PUSH_CHANNEL  — comma-separated: "feishu,macos" | "none" (default: "none")
    FEISHU_APP_ID          — Feishu self-built app ID
    FEISHU_APP_SECRET      — Feishu app secret
    FEISHU_RECEIVE_USER_ID — Target user open_id (ou_xxx)
    FEISHU_RECEIVE_ID_TYPE — "open_id" (default) | "chat_id" | "user_id"
    BARK_URL               — Bark push URL (e.g. https://api.day.app/YOUR_KEY)
    VITACLAW_WEBHOOK_URL   — Generic webhook POST endpoint

Priority routing (configurable via VITACLAW_PUSH_ROUTING):
    high   → all configured channels
    medium → first configured channel only
    low    → none (task board only)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen


def _feishu_get_tenant_token(app_id: str, app_secret: str) -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    body = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    if result.get("code") != 0:
        raise RuntimeError(f"Failed to get Feishu tenant token: {result}")
    return result["tenant_access_token"]


def _feishu_send_text(token: str, receive_id: str, receive_id_type: str, text: str) -> dict:
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}"
    content = json.dumps({"text": text})
    body = json.dumps(
        {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": content,
        }
    ).encode()
    req = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _format_issues_text(issues: list[dict]) -> str:
    if not issues:
        return ""
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    lines = [f"[VitaClaw 健康提醒] {now}\n"]
    for issue in issues:
        priority = issue.get("priority", "medium")
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
        title = issue.get("title", issue.get("topic", ""))
        lines.append(f"{icon} {title}")
        if issue.get("suggestion"):
            lines.append(f"   → {issue['suggestion']}")
    return "\n".join(lines)


def dispatch(push_issues: list[dict]) -> dict:
    """Deliver push_issues via all configured channels with priority routing.

    Returns {"channels": list[str], "sent": int, "errors": list[str]}
    """
    raw = os.environ.get("VITACLAW_PUSH_CHANNEL", "none").lower().strip()
    if raw == "none" or not push_issues:
        return {"channel": raw, "channels": [raw], "sent": 0, "errors": []}

    channels = [ch.strip() for ch in raw.split(",") if ch.strip()]

    all_errors: list[str] = []
    total_sent = 0

    # Route by priority: high → all channels, medium → first channel, low → skip
    high_issues = [i for i in push_issues if i.get("priority") == "high"]
    medium_issues = [i for i in push_issues if i.get("priority") == "medium"]

    for channel in channels:
        # High-priority issues go to all channels
        issues_for_channel = list(high_issues)
        # Medium-priority issues only go to the first channel
        if channel == channels[0]:
            issues_for_channel.extend(medium_issues)

        if not issues_for_channel:
            continue

        handler = CHANNEL_HANDLERS.get(channel)
        if handler is None:
            all_errors.append(f"Unknown push channel: {channel}")
            continue

        result = handler(issues_for_channel)
        total_sent += result.get("sent", 0)
        all_errors.extend(result.get("errors", []))

    return {
        "channel": ",".join(channels),  # backward compat
        "channels": channels,
        "sent": total_sent,
        "errors": all_errors,
    }


def _dispatch_feishu(issues: list[dict]) -> dict:
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    receive_id = os.environ.get("FEISHU_RECEIVE_USER_ID", "")
    receive_id_type = os.environ.get("FEISHU_RECEIVE_ID_TYPE", "open_id")

    errors: list[str] = []
    if not app_id or not app_secret:
        errors.append("FEISHU_APP_ID and FEISHU_APP_SECRET must be set")
        return {"channel": "feishu", "sent": 0, "errors": errors}
    if not receive_id:
        errors.append("FEISHU_RECEIVE_USER_ID must be set")
        return {"channel": "feishu", "sent": 0, "errors": errors}

    text = _format_issues_text(issues)
    if not text:
        return {"channel": "feishu", "sent": 0, "errors": []}

    try:
        token = _feishu_get_tenant_token(app_id, app_secret)
        result = _feishu_send_text(token, receive_id, receive_id_type, text)
        if result.get("code") != 0:
            errors.append(f"Feishu API error: {result}")
            return {"channel": "feishu", "sent": 0, "errors": errors}
        return {"channel": "feishu", "sent": len(issues), "errors": []}
    except (URLError, RuntimeError, OSError) as exc:
        errors.append(str(exc))
        return {"channel": "feishu", "sent": 0, "errors": errors}


# ── macOS native notification ─────────────────────────────────


def _dispatch_macos(issues: list[dict]) -> dict:
    """Send notifications via macOS osascript (works without extra deps)."""
    if sys.platform != "darwin":
        return {"channel": "macos", "sent": 0, "errors": ["macOS notifications only available on Darwin"]}

    errors: list[str] = []
    sent = 0
    for issue in issues:
        priority = issue.get("priority", "medium")
        title = issue.get("title", "VitaClaw 健康提醒")
        reason = issue.get("reason", "")
        # Truncate for notification display
        body = reason[:200] if reason else ""
        sound = "default" if priority == "high" else ""

        script = (
            f'display notification "{_escape_applescript(body)}" '
            f'with title "VitaClaw" '
            f'subtitle "{_escape_applescript(title)}"'
        )
        if sound:
            script += f' sound name "{sound}"'

        try:
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                timeout=5,
                check=False,
            )
            sent += 1
        except Exception as exc:
            errors.append(f"osascript failed: {exc}")

    return {"channel": "macos", "sent": sent, "errors": errors}


def _escape_applescript(text: str) -> str:
    """Escape text for use in AppleScript string literals."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


# ── Bark iOS push ─────────────────────────────────────────────


def _dispatch_bark(issues: list[dict]) -> dict:
    """Send notifications via Bark (iOS push service)."""
    bark_url = os.environ.get("BARK_URL", "").rstrip("/")
    if not bark_url:
        return {"channel": "bark", "sent": 0, "errors": ["BARK_URL not set"]}

    errors: list[str] = []
    sent = 0
    for issue in issues:
        priority = issue.get("priority", "medium")
        title = issue.get("title", "VitaClaw")
        body = issue.get("reason", "")[:300]
        # Bark supports sound/level via query params
        level = "timeSensitive" if priority == "high" else "active"

        try:
            url = f"{bark_url}/VitaClaw/{_url_encode(title + ': ' + body)}?level={level}"
            req = Request(url, method="GET")
            with urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
            if result.get("code") == 200:
                sent += 1
            else:
                errors.append(f"Bark error: {result}")
        except Exception as exc:
            errors.append(f"Bark push failed: {exc}")

    return {"channel": "bark", "sent": sent, "errors": errors}


def _url_encode(text: str) -> str:
    """Simple URL-safe encoding for Bark push content."""
    from urllib.parse import quote

    return quote(text, safe="")


# ── Generic webhook ───────────────────────────────────────────


def _dispatch_webhook(issues: list[dict]) -> dict:
    """Send notifications via generic HTTP POST webhook."""
    webhook_url = os.environ.get("VITACLAW_WEBHOOK_URL", "")
    if not webhook_url:
        return {"channel": "webhook", "sent": 0, "errors": ["VITACLAW_WEBHOOK_URL not set"]}

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = json.dumps(
        {
            "source": "vitaclaw",
            "timestamp": now,
            "issues": [
                {
                    "priority": i.get("priority", "medium"),
                    "title": i.get("title", ""),
                    "reason": i.get("reason", ""),
                    "next_step": i.get("next_step", ""),
                }
                for i in issues
            ],
        },
        ensure_ascii=False,
    ).encode()

    try:
        req = Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=10) as resp:
            if resp.status < 300:
                return {"channel": "webhook", "sent": len(issues), "errors": []}
            return {"channel": "webhook", "sent": 0, "errors": [f"HTTP {resp.status}"]}
    except Exception as exc:
        return {"channel": "webhook", "sent": 0, "errors": [str(exc)]}


# ── Channel registry ──────────────────────────────────────────

CHANNEL_HANDLERS = {
    "feishu": _dispatch_feishu,
    "macos": _dispatch_macos,
    "bark": _dispatch_bark,
    "webhook": _dispatch_webhook,
}
