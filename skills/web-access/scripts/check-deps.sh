#!/usr/bin/env bash
# Adapted from eze-is/web-access (MIT). Checks Node + Chrome CDP readiness for VitaClaw.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROXY_SCRIPT="${SCRIPT_DIR}/cdp-proxy.mjs"

if command -v node >/dev/null 2>&1; then
  NODE_VER="$(node --version 2>/dev/null || true)"
  NODE_MAJOR="$(echo "${NODE_VER}" | sed 's/v//' | cut -d. -f1)"
  if [ "${NODE_MAJOR:-0}" -ge 22 ] 2>/dev/null; then
    echo "node: ok (${NODE_VER})"
  else
    echo "node: warn (${NODE_VER}, 建议升级到 22+)"
  fi
else
  echo "node: missing — 请安装 Node.js 22+"
  exit 1
fi

if ! node -e "
const net = require('net');
const s = net.createConnection(9222, '127.0.0.1');
s.on('connect', () => process.exit(0));
s.on('error', () => process.exit(1));
setTimeout(() => process.exit(1), 2000);
" 2>/dev/null; then
  echo "chrome: not connected — 请打开 chrome://inspect/#remote-debugging 并勾选 Allow remote debugging"
  exit 1
fi
echo "chrome: ok (port 9222)"

HEALTH="$(curl -s --connect-timeout 2 http://127.0.0.1:3456/health 2>/dev/null || true)"
if echo "${HEALTH}" | grep -q '"connected":true'; then
  echo "proxy: ready"
  exit 0
fi

if ! echo "${HEALTH}" | grep -q '"status":"ok"'; then
  echo "proxy: starting..."
  node "${PROXY_SCRIPT}" >/tmp/vitaclaw-web-access-proxy.log 2>&1 &
fi

for i in $(seq 1 15); do
  sleep 1
  if curl -s http://127.0.0.1:3456/health 2>/dev/null | grep -q '"connected":true'; then
    echo "proxy: ready"
    exit 0
  fi
  if [ "${i}" -eq 3 ]; then
    echo "⚠️ Chrome 可能有授权弹窗，请点击允许后等待连接..."
  fi
done

echo "❌ 连接超时，请检查 Chrome 调试设置"
exit 1
