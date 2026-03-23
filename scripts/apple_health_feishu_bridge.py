#!/usr/bin/env python3
"""
VitaClaw Apple Health → Feishu Bridge Server

接收 iOS 快捷指令 POST 过来的 Apple Health 日度数据，
写入 VitaClaw 数据层，并通过飞书机器人发送健康日报给指定用户。

启动方式:
    python3 scripts/apple_health_feishu_bridge.py --feishu-app-id cli_xxx --feishu-app-secret xxx --feishu-user-id ou_xxx

环境变量 (可替代命令行参数):
    FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_RECEIVE_USER_ID
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from health_data_store import HealthDataStore  # noqa: E402

# ---------------------------------------------------------------------------
# Feishu API helpers
# ---------------------------------------------------------------------------
FEISHU_BASE = "https://open.feishu.cn/open-apis"


def _feishu_get_tenant_token(app_id: str, app_secret: str) -> str:
    """获取飞书 tenant_access_token (有效期 2 小时)."""
    url = f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal"
    body = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    if result.get("code") != 0:
        raise RuntimeError(f"Failed to get tenant token: {result}")
    return result["tenant_access_token"]


def _feishu_send_message(
    token: str,
    receive_id: str,
    receive_id_type: str,
    msg_type: str,
    content: str,
) -> dict:
    """发送飞书消息给指定用户/群."""
    url = f"{FEISHU_BASE}/im/v1/messages?receive_id_type={receive_id_type}"
    body = json.dumps({
        "receive_id": receive_id,
        "msg_type": msg_type,
        "content": content,
    }).encode()
    req = Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    })
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Health data processing
# ---------------------------------------------------------------------------

# iOS 快捷指令 "查找健康样本" 支持的数据类型映射
HEALTH_TYPE_MAP = {
    "steps":             ("apple-health-sync", "steps"),
    "heart_rate":        ("apple-health-sync", "heart_rate"),
    "resting_heart_rate": ("apple-health-sync", "resting_heart_rate"),
    "hrv":               ("apple-health-sync", "hrv"),
    "blood_pressure_systolic":  ("blood-pressure-tracker", "bp_reading"),
    "blood_pressure_diastolic": ("blood-pressure-tracker", "bp_reading"),
    "blood_oxygen":      ("apple-health-sync", "spo2"),
    "body_mass":         ("apple-health-sync", "weight"),
    "sleep_hours":       ("sleep-analyzer", "sleep_record"),
    "active_energy":     ("apple-health-sync", "active_energy"),
    "exercise_minutes":  ("apple-health-sync", "exercise_minutes"),
}


def _process_health_payload(payload: dict, data_dir: str | None = None) -> dict:
    """
    处理 iOS 快捷指令发来的健康数据 JSON，写入 VitaClaw JSONL 数据层。

    期望的 payload 格式:
    {
        "date": "2026-03-16",
        "device": "iPhone 15 Pro",
        "metrics": {
            "steps": 8234,
            "heart_rate": {"avg": 72, "min": 55, "max": 128},
            "resting_heart_rate": 58,
            "hrv": 42,
            "blood_pressure_systolic": 125,
            "blood_pressure_diastolic": 82,
            "blood_oxygen": 98,
            "body_mass": 72.5,
            "sleep_hours": 7.2,
            "active_energy": 420,
            "exercise_minutes": 35
        }
    }
    """
    date_str = payload.get("date") or datetime.now().strftime("%Y-%m-%d")
    metrics = payload.get("metrics", {})
    device = payload.get("device", "iOS Shortcut")

    records_written = []
    errors = []

    # 合并血压为一条记录
    sys_val = metrics.pop("blood_pressure_systolic", None)
    dia_val = metrics.pop("blood_pressure_diastolic", None)
    if sys_val is not None and dia_val is not None:
        try:
            store = HealthDataStore("blood-pressure-tracker", data_dir=data_dir)
            rec = store.append(
                record_type="bp_reading",
                data={
                    "systolic": sys_val,
                    "diastolic": dia_val,
                    "source": "apple_health",
                    "device": device,
                },
                note=f"Auto-sync from Apple Health via iOS Shortcut",
                timestamp=date_str,
            )
            records_written.append({"type": "bp_reading", "id": rec["id"]})
        except Exception as e:
            errors.append(f"bp_reading: {e}")

    # 处理其他指标
    for metric_key, value in metrics.items():
        mapping = HEALTH_TYPE_MAP.get(metric_key)
        if not mapping:
            continue
        skill_name, record_type = mapping
        try:
            store = HealthDataStore(skill_name, data_dir=data_dir)
            if isinstance(value, dict):
                data = {**value, "source": "apple_health", "device": device}
            else:
                data = {"value": value, "source": "apple_health", "device": device}
            rec = store.append(
                record_type=record_type,
                data=data,
                note="Auto-sync from Apple Health via iOS Shortcut",
                timestamp=date_str,
            )
            records_written.append({"type": record_type, "id": rec["id"]})
        except Exception as e:
            errors.append(f"{metric_key}: {e}")

    return {
        "success": len(errors) == 0,
        "date": date_str,
        "records_written": len(records_written),
        "details": records_written,
        "errors": errors,
    }


def _build_daily_report(payload: dict) -> str:
    """根据 iOS 快捷指令发来的原始数据生成飞书卡片文本."""
    date_str = payload.get("date", "unknown")
    metrics = payload.get("metrics", {})

    lines = [f"📊 VitaClaw 每日健康同步 — {date_str}", ""]

    metric_labels = {
        "steps": ("🚶 步数", "", "步"),
        "heart_rate": ("❤️ 心率", "avg", "bpm"),
        "resting_heart_rate": ("💚 静息心率", "", "bpm"),
        "hrv": ("📈 HRV", "", "ms"),
        "blood_pressure_systolic": ("🩸 收缩压", "", "mmHg"),
        "blood_pressure_diastolic": ("🩸 舒张压", "", "mmHg"),
        "blood_oxygen": ("🫁 血氧", "", "%"),
        "body_mass": ("⚖️ 体重", "", "kg"),
        "sleep_hours": ("😴 睡眠", "", "小时"),
        "active_energy": ("🔥 活动消耗", "", "kcal"),
        "exercise_minutes": ("🏃 运动时间", "", "分钟"),
    }

    # 合并血压显示
    sys_val = metrics.get("blood_pressure_systolic")
    dia_val = metrics.get("blood_pressure_diastolic")

    for key, (label, sub_key, unit) in metric_labels.items():
        if key in ("blood_pressure_systolic", "blood_pressure_diastolic"):
            continue  # 单独处理
        val = metrics.get(key)
        if val is None:
            continue
        if isinstance(val, dict):
            display_val = val.get(sub_key, val.get("value", val))
            if isinstance(display_val, dict):
                display_val = json.dumps(display_val, ensure_ascii=False)
        else:
            display_val = val
        lines.append(f"{label}: {display_val} {unit}")

    if sys_val is not None and dia_val is not None:
        lines.append(f"🩸 血压: {sys_val}/{dia_val} mmHg")

    lines.append("")
    lines.append("✅ 数据已自动写入 VitaClaw 健康档案")

    return "\n".join(lines)


def _build_feishu_interactive_card(payload: dict, result: dict) -> str:
    """构建飞书 Interactive Card 消息."""
    date_str = payload.get("date", "unknown")
    metrics = payload.get("metrics", {})

    elements = []

    # 标题行
    elements.append({
        "tag": "markdown",
        "content": f"**日期**: {date_str}  |  **来源**: Apple Health 自动同步"
    })

    elements.append({"tag": "hr"})

    # 指标区域
    fields = []
    field_map = [
        ("steps", "🚶 步数", "步"),
        ("heart_rate", "❤️ 心率", "bpm"),
        ("resting_heart_rate", "💚 静息心率", "bpm"),
        ("hrv", "📈 HRV", "ms"),
        ("blood_oxygen", "🫁 血氧", "%"),
        ("body_mass", "⚖️ 体重", "kg"),
        ("sleep_hours", "😴 睡眠", "小时"),
        ("active_energy", "🔥 消耗", "kcal"),
        ("exercise_minutes", "🏃 运动", "分钟"),
    ]

    for key, label, unit in field_map:
        val = metrics.get(key)
        if val is None:
            continue
        if isinstance(val, dict):
            val = val.get("avg", val.get("value", "—"))
        fields.append({
            "is_short": True,
            "text": {"tag": "lark_md", "content": f"**{label}**\n{val} {unit}"}
        })

    # 血压单独处理
    sys_val = metrics.get("blood_pressure_systolic")
    dia_val = metrics.get("blood_pressure_diastolic")
    if sys_val is not None and dia_val is not None:
        fields.append({
            "is_short": True,
            "text": {"tag": "lark_md", "content": f"**🩸 血压**\n{sys_val}/{dia_val} mmHg"}
        })

    if fields:
        elements.append({"tag": "div", "fields": fields})

    elements.append({"tag": "hr"})

    # 状态行
    status = "✅ 已写入" if result.get("success") else "⚠️ 部分失败"
    elements.append({
        "tag": "markdown",
        "content": f"{status} | 写入 {result.get('records_written', 0)} 条记录到 VitaClaw"
    })

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"📊 每日健康报告 — {date_str}"},
            "template": "blue",
        },
        "elements": elements,
    }
    return json.dumps(card, ensure_ascii=False)


# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------

class HealthBridgeHandler(BaseHTTPRequestHandler):
    """接收 iOS 快捷指令 POST 请求的 HTTP Handler."""

    server: HealthBridgeServer  # type hint

    def do_POST(self):
        if self.path != "/api/health-sync":
            self._respond(404, {"error": "not found"})
            return

        # 验证 token
        auth_token = self.server.auth_token
        if auth_token:
            provided = self.headers.get("X-Auth-Token", "")
            if provided != auth_token:
                self._respond(401, {"error": "unauthorized"})
                return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._respond(400, {"error": "empty body"})
            return
        if content_length > 1024 * 1024:  # 1MB 上限
            self._respond(413, {"error": "payload too large"})
            return

        try:
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._respond(400, {"error": f"invalid JSON: {e}"})
            return

        # 1. 写入 VitaClaw 数据层
        result = _process_health_payload(payload, data_dir=self.server.data_dir)

        # 2. 发送飞书消息
        feishu_result = None
        if self.server.feishu_app_id and self.server.feishu_receive_id:
            try:
                token = _feishu_get_tenant_token(
                    self.server.feishu_app_id,
                    self.server.feishu_app_secret,
                )
                card_content = _build_feishu_interactive_card(payload, result)
                feishu_result = _feishu_send_message(
                    token=token,
                    receive_id=self.server.feishu_receive_id,
                    receive_id_type=self.server.feishu_receive_id_type,
                    msg_type="interactive",
                    content=card_content,
                )
            except Exception as e:
                feishu_result = {"error": str(e)}

        result["feishu"] = feishu_result
        self._respond(200, result)

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok", "service": "vitaclaw-health-bridge"})
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, status: int, body: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8"))

    def log_message(self, format, *args):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {args[0]}", flush=True)


class HealthBridgeServer(HTTPServer):
    """带配置的 HTTP Server."""

    def __init__(self, addr, handler, *, data_dir, auth_token,
                 feishu_app_id, feishu_app_secret,
                 feishu_receive_id, feishu_receive_id_type):
        super().__init__(addr, handler)
        self.data_dir = data_dir
        self.auth_token = auth_token
        self.feishu_app_id = feishu_app_id
        self.feishu_app_secret = feishu_app_secret
        self.feishu_receive_id = feishu_receive_id
        self.feishu_receive_id_type = feishu_receive_id_type


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="VitaClaw Apple Health → Feishu Bridge Server"
    )
    parser.add_argument("--port", type=int, default=8470,
                        help="HTTP server port (default: 8470)")
    parser.add_argument("--host", default="0.0.0.0",
                        help="HTTP server bind address (default: 0.0.0.0)")
    parser.add_argument("--data-dir", default=None,
                        help="VitaClaw data directory")
    parser.add_argument("--auth-token", default=None,
                        help="Simple auth token for iOS Shortcut requests (or env AUTH_TOKEN)")
    parser.add_argument("--feishu-app-id", default=None,
                        help="Feishu app_id (or env FEISHU_APP_ID)")
    parser.add_argument("--feishu-app-secret", default=None,
                        help="Feishu app_secret (or env FEISHU_APP_SECRET)")
    parser.add_argument("--feishu-user-id", default=None,
                        help="Feishu receive user open_id (or env FEISHU_RECEIVE_USER_ID)")
    parser.add_argument("--feishu-receive-id-type", default="open_id",
                        choices=["open_id", "user_id", "union_id", "email", "chat_id"],
                        help="Feishu receive_id_type (default: open_id)")
    args = parser.parse_args()

    # 环境变量 fallback
    auth_token = args.auth_token or os.environ.get("AUTH_TOKEN")
    feishu_app_id = args.feishu_app_id or os.environ.get("FEISHU_APP_ID")
    feishu_app_secret = args.feishu_app_secret or os.environ.get("FEISHU_APP_SECRET")
    feishu_receive_id = args.feishu_user_id or os.environ.get("FEISHU_RECEIVE_USER_ID")

    if not auth_token:
        # 自动生成一个 auth token
        auth_token = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
        print(f"[INFO] Auto-generated auth token: {auth_token}")
        print(f"[INFO] Add this to your iOS Shortcut 'X-Auth-Token' header")

    server = HealthBridgeServer(
        (args.host, args.port),
        HealthBridgeHandler,
        data_dir=args.data_dir,
        auth_token=auth_token,
        feishu_app_id=feishu_app_id,
        feishu_app_secret=feishu_app_secret,
        feishu_receive_id=feishu_receive_id,
        feishu_receive_id_type=args.feishu_receive_id_type,
    )

    print(f"[INFO] VitaClaw Health Bridge started on {args.host}:{args.port}")
    print(f"[INFO] Endpoint: POST /api/health-sync")
    print(f"[INFO] Health check: GET /health")
    if feishu_app_id:
        print(f"[INFO] Feishu notification: enabled → {feishu_receive_id}")
    else:
        print(f"[WARN] Feishu notification: disabled (no --feishu-app-id)")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
