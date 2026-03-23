#!/usr/bin/env node
// Adapted from eze-is/web-access (MIT).
// Minimal CDP proxy for VitaClaw public-health browsing.

import fs from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';

const PORT = parseInt(process.env.CDP_PROXY_PORT || '3456', 10);

let ws = null;
let wsCtor = null;
let cmdId = 0;
const pending = new Map();
const sessions = new Map();
let chromePort = null;
let chromeWsPath = null;

async function resolveWsCtor() {
  if (wsCtor) return wsCtor;
  if (typeof globalThis.WebSocket !== 'undefined') {
    wsCtor = globalThis.WebSocket;
    return wsCtor;
  }
  try {
    wsCtor = (await import('ws')).default;
    return wsCtor;
  } catch {
    console.error('[CDP Proxy] 错误：Node.js < 22 且未安装 ws 模块');
    process.exit(1);
  }
}

function checkPort(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection(port, '127.0.0.1');
    const timer = setTimeout(() => {
      socket.destroy();
      resolve(false);
    }, 2000);
    socket.once('connect', () => {
      clearTimeout(timer);
      socket.destroy();
      resolve(true);
    });
    socket.once('error', () => {
      clearTimeout(timer);
      resolve(false);
    });
  });
}

async function discoverChromePort() {
  const candidates = [];
  const home = os.homedir();
  const platform = os.platform();

  if (platform === 'darwin') {
    candidates.push(
      path.join(home, 'Library/Application Support/Google/Chrome/DevToolsActivePort'),
      path.join(home, 'Library/Application Support/Google/Chrome Canary/DevToolsActivePort'),
      path.join(home, 'Library/Application Support/Chromium/DevToolsActivePort'),
    );
  } else if (platform === 'linux') {
    candidates.push(
      path.join(home, '.config/google-chrome/DevToolsActivePort'),
      path.join(home, '.config/chromium/DevToolsActivePort'),
    );
  } else if (platform === 'win32') {
    const localAppData = process.env.LOCALAPPDATA || '';
    candidates.push(
      path.join(localAppData, 'Google/Chrome/User Data/DevToolsActivePort'),
      path.join(localAppData, 'Chromium/User Data/DevToolsActivePort'),
    );
  }

  for (const filePath of candidates) {
    try {
      const content = fs.readFileSync(filePath, 'utf-8').trim();
      const lines = content.split('\n');
      const port = parseInt(lines[0], 10);
      if (port > 0 && port < 65536 && await checkPort(port)) {
        return { port, wsPath: lines[1] || null };
      }
    } catch {
      // keep scanning
    }
  }

  for (const port of [9222, 9229, 9333]) {
    if (await checkPort(port)) return { port, wsPath: null };
  }
  return null;
}

function wsUrlFrom(port, wsPath) {
  if (wsPath) return `ws://127.0.0.1:${port}${wsPath}`;
  return `ws://127.0.0.1:${port}/devtools/browser`;
}

async function connect() {
  if (ws && (ws.readyState === wsCtor.OPEN || ws.readyState === 1)) return;

  const Ctor = await resolveWsCtor();
  if (!chromePort) {
    const discovered = await discoverChromePort();
    if (!discovered) {
      throw new Error(
        'Chrome 未开启远程调试。请打开 chrome://inspect/#remote-debugging 并勾选 Allow remote debugging'
      );
    }
    chromePort = discovered.port;
    chromeWsPath = discovered.wsPath;
  }

  return new Promise((resolve, reject) => {
    ws = new Ctor(wsUrlFrom(chromePort, chromeWsPath));

    const cleanup = () => {
      ws.removeEventListener?.('open', onOpen);
      ws.removeEventListener?.('error', onError);
    };
    const onOpen = () => {
      cleanup();
      resolve();
    };
    const onError = (event) => {
      cleanup();
      reject(new Error(event?.message || event?.error?.message || '连接失败'));
    };
    const onClose = () => {
      ws = null;
      chromePort = null;
      chromeWsPath = null;
      sessions.clear();
    };
    const onMessage = (evt) => {
      const raw = typeof evt === 'string' ? evt : (evt.data || evt);
      const msg = JSON.parse(typeof raw === 'string' ? raw : raw.toString());
      if (msg.method === 'Target.attachedToTarget') {
        const { sessionId, targetInfo } = msg.params;
        sessions.set(targetInfo.targetId, sessionId);
      }
      if (msg.id && pending.has(msg.id)) {
        const { resolve, timer } = pending.get(msg.id);
        clearTimeout(timer);
        pending.delete(msg.id);
        resolve(msg);
      }
    };

    if (ws.on) {
      ws.on('open', onOpen);
      ws.on('error', onError);
      ws.on('close', onClose);
      ws.on('message', onMessage);
    } else {
      ws.addEventListener('open', onOpen);
      ws.addEventListener('error', onError);
      ws.addEventListener('close', onClose);
      ws.addEventListener('message', onMessage);
    }
  });
}

function sendCDP(method, params = {}, sessionId = null) {
  return new Promise((resolve, reject) => {
    if (!ws || (ws.readyState !== wsCtor.OPEN && ws.readyState !== 1)) {
      reject(new Error('WebSocket 未连接'));
      return;
    }
    const id = ++cmdId;
    const message = { id, method, params };
    if (sessionId) message.sessionId = sessionId;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`CDP 命令超时: ${method}`));
    }, 30000);
    pending.set(id, { resolve, timer });
    ws.send(JSON.stringify(message));
  });
}

async function ensureSession(targetId) {
  if (sessions.has(targetId)) return sessions.get(targetId);
  const response = await sendCDP('Target.attachToTarget', { targetId, flatten: true });
  if (response.result?.sessionId) {
    sessions.set(targetId, response.result.sessionId);
    return response.result.sessionId;
  }
  throw new Error(`attach 失败: ${JSON.stringify(response.error)}`);
}

async function waitForLoad(sessionId, timeoutMs = 15000) {
  await sendCDP('Page.enable', {}, sessionId);
  return new Promise((resolve) => {
    let done = false;
    const finish = (value) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      clearInterval(interval);
      resolve(value);
    };
    const timer = setTimeout(() => finish('timeout'), timeoutMs);
    const interval = setInterval(async () => {
      try {
        const response = await sendCDP(
          'Runtime.evaluate',
          { expression: 'document.readyState', returnByValue: true },
          sessionId,
        );
        if (response.result?.result?.value === 'complete') {
          finish('complete');
        }
      } catch {
        // ignore
      }
    }, 500);
  });
}

async function readBody(req) {
  let body = '';
  for await (const chunk of req) body += chunk;
  return body;
}

const server = http.createServer(async (req, res) => {
  const parsed = new URL(req.url, `http://127.0.0.1:${PORT}`);
  const pathname = parsed.pathname;
  const q = Object.fromEntries(parsed.searchParams);
  res.setHeader('Content-Type', 'application/json; charset=utf-8');

  try {
    if (pathname === '/health') {
      res.end(JSON.stringify({
        status: 'ok',
        connected: Boolean(ws && (ws.readyState === wsCtor?.OPEN || ws.readyState === 1)),
        sessions: sessions.size,
        chromePort,
      }));
      return;
    }

    await connect();

    if (pathname === '/targets') {
      const response = await sendCDP('Target.getTargets');
      const pages = response.result.targetInfos.filter((item) => item.type === 'page');
      res.end(JSON.stringify(pages, null, 2));
      return;
    }

    if (pathname === '/new') {
      const response = await sendCDP('Target.createTarget', {
        url: q.url || 'about:blank',
        background: true,
      });
      const targetId = response.result.targetId;
      if ((q.url || 'about:blank') !== 'about:blank') {
        try {
          const sessionId = await ensureSession(targetId);
          await waitForLoad(sessionId);
        } catch {
          // non-fatal
        }
      }
      res.end(JSON.stringify({ targetId }));
      return;
    }

    if (pathname === '/close') {
      const response = await sendCDP('Target.closeTarget', { targetId: q.target });
      sessions.delete(q.target);
      res.end(JSON.stringify(response.result || { closed: true }));
      return;
    }

    if (pathname === '/navigate') {
      const sessionId = await ensureSession(q.target);
      const response = await sendCDP('Page.navigate', { url: q.url }, sessionId);
      await waitForLoad(sessionId);
      res.end(JSON.stringify(response.result || {}));
      return;
    }

    if (pathname === '/info') {
      const sessionId = await ensureSession(q.target);
      const response = await sendCDP(
        'Runtime.evaluate',
        {
          expression: 'JSON.stringify({title: document.title, url: location.href, ready: document.readyState})',
          returnByValue: true,
        },
        sessionId,
      );
      res.end(response.result?.result?.value || '{}');
      return;
    }

    if (pathname === '/eval') {
      const sessionId = await ensureSession(q.target);
      const expression = (await readBody(req)) || q.expr || 'document.title';
      const response = await sendCDP(
        'Runtime.evaluate',
        {
          expression,
          returnByValue: true,
          awaitPromise: true,
        },
        sessionId,
      );
      if (response.result?.result?.value !== undefined) {
        res.end(JSON.stringify({ value: response.result.result.value }));
        return;
      }
      if (response.result?.exceptionDetails) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: response.result.exceptionDetails.text }));
        return;
      }
      res.end(JSON.stringify(response.result || {}));
      return;
    }

    if (pathname === '/click') {
      const sessionId = await ensureSession(q.target);
      const selector = await readBody(req);
      if (!selector) {
        res.statusCode = 400;
        res.end(JSON.stringify({ error: 'POST body 需要 CSS 选择器' }));
        return;
      }
      const selectorJson = JSON.stringify(selector);
      const response = await sendCDP(
        'Runtime.evaluate',
        {
          expression: `(() => {
            const el = document.querySelector(${selectorJson});
            if (!el) return { error: '未找到元素: ' + ${selectorJson} };
            el.scrollIntoView({ block: 'center' });
            el.click();
            return { clicked: true, tag: el.tagName, text: (el.textContent || '').slice(0, 100) };
          })()`,
          returnByValue: true,
          awaitPromise: true,
        },
        sessionId,
      );
      const value = response.result?.result?.value;
      if (value?.error) {
        res.statusCode = 400;
      }
      res.end(JSON.stringify(value || response.result || {}));
      return;
    }

    if (pathname === '/scroll') {
      const sessionId = await ensureSession(q.target);
      const y = parseInt(q.y || '3000', 10);
      const direction = q.direction || 'down';
      let expression = `window.scrollBy(0, ${Math.abs(y)}); "scrolled"`;
      if (direction === 'top') expression = 'window.scrollTo(0, 0); "scrolled to top"';
      if (direction === 'bottom') expression = 'window.scrollTo(0, document.body.scrollHeight); "scrolled to bottom"';
      if (direction === 'up') expression = `window.scrollBy(0, -${Math.abs(y)}); "scrolled up"`;
      const response = await sendCDP(
        'Runtime.evaluate',
        { expression, returnByValue: true },
        sessionId,
      );
      await new Promise((resolve) => setTimeout(resolve, 800));
      res.end(JSON.stringify({ value: response.result?.result?.value }));
      return;
    }

    if (pathname === '/screenshot') {
      const sessionId = await ensureSession(q.target);
      const format = q.format || 'png';
      const response = await sendCDP(
        'Page.captureScreenshot',
        {
          format,
          quality: format === 'jpeg' ? 80 : undefined,
        },
        sessionId,
      );
      if (q.file) {
        fs.writeFileSync(q.file, Buffer.from(response.result.data, 'base64'));
        res.end(JSON.stringify({ saved: q.file }));
        return;
      }
      res.setHeader('Content-Type', `image/${format}`);
      res.end(Buffer.from(response.result.data, 'base64'));
      return;
    }

    res.statusCode = 404;
    res.end(JSON.stringify({ error: '未知端点' }));
  } catch (error) {
    res.statusCode = 500;
    res.end(JSON.stringify({ error: error.message }));
  }
});

server.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    console.error(`[CDP Proxy] 端口 ${PORT} 已被占用`);
  } else {
    console.error('[CDP Proxy] 服务错误:', error.message);
  }
});

server.listen(PORT, async () => {
  console.log(`[CDP Proxy] listening on ${PORT}`);
  try {
    await connect();
    console.log('[CDP Proxy] connected');
  } catch (error) {
    console.error('[CDP Proxy] 初始连接失败:', error.message, '（首次请求时会重试）');
  }
});

process.on('uncaughtException', (error) => {
  console.error('[CDP Proxy] 未捕获异常:', error.message);
});

process.on('unhandledRejection', (error) => {
  console.error('[CDP Proxy] 未处理拒绝:', error?.message || error);
});
