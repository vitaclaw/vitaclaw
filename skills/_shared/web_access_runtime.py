#!/usr/bin/env python3
"""Controlled Web Access runtime for VitaClaw public-health workflows."""

from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


BLOCKED_HOST_SUFFIXES = (
    "xiaohongshu.com",
    "weibo.com",
    "zhihu.com",
    "douyin.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "bosszhipin.com",
    "zhipin.com",
    "taobao.com",
    "jd.com",
    "tmall.com",
    "bilibili.com",
    "youtube.com",
    "reddit.com",
    "baidu.com",
    "bing.com",
    "google.com",
    "sogou.com",
    "so.com",
)

BLOCKED_SCHEMES = {"javascript", "mailto", "tel", "data"}
DYNAMIC_PAGE_MARKERS = (
    "enable javascript",
    "please enable javascript",
    "javascript required",
    "loading...",
    "加载中",
    "请开启javascript",
    "请使用浏览器访问",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _web_access_skill_dir() -> Path:
    return _repo_root() / "skills" / "web-access"


def _check_deps_script() -> Path:
    return _web_access_skill_dir() / "scripts" / "check-deps.sh"


def _default_headers() -> dict[str, str]:
    return {
        "User-Agent": "VitaClaw/1.0 (+https://github.com/vitaclaw/vitaclaw)",
    }


def _normalized_host(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower().strip(".")


def _host_matches(host: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        clean = pattern.lower().strip()
        if not clean:
            continue
        if host == clean or host.endswith(f".{clean}"):
            return True
    return False


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.headings: list[str] = []
        self.anchors: list[dict[str, str]] = []
        self._tag_stack: list[str] = []
        self._current_anchor_href: str | None = None
        self._current_anchor_text: list[str] = []
        self._in_title = False
        self._in_description = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "a" and attrs_dict.get("href"):
            self._current_anchor_href = attrs_dict["href"]
            self._current_anchor_text = []
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                self.description = attrs_dict.get("content", "").strip()
        elif tag in {"h1", "h2", "h3"}:
            self._tag_stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "a" and self._current_anchor_href is not None:
            text = " ".join(part.strip() for part in self._current_anchor_text if part.strip()).strip()
            self.anchors.append({"href": self._current_anchor_href, "text": text})
            self._current_anchor_href = None
            self._current_anchor_text = []
        elif tag == "title":
            self._in_title = False
        elif tag in {"h1", "h2", "h3"}:
            if self._tag_stack:
                self._tag_stack.pop()

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title = " ".join(part for part in [self.title, text] if part).strip()
        if self._current_anchor_href is not None:
            self._current_anchor_text.append(text)
        if self._tag_stack:
            self.headings.append(text)


class _HTMLToText(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip = False
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data):
        if self._skip:
            return
        text = data.strip()
        if text:
            self.parts.append(text)


def html_to_text(html: str) -> str:
    parser = _HTMLToText()
    parser.feed(html)
    return " ".join(parser.parts).strip()


@dataclass
class PageSnapshot:
    url: str
    title: str
    text: str
    headings: list[str]
    anchors: list[dict[str, str]]
    mode_used: str
    meta_description: str = ""
    notes: list[str] = field(default_factory=list)
    selected_anchors: list[dict[str, str]] = field(default_factory=list)
    raw_html: str | None = None

    def as_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "text": self.text,
            "headings": self.headings,
            "anchors": self.anchors,
            "mode_used": self.mode_used,
            "meta_description": self.meta_description,
            "notes": self.notes,
            "selected_anchors": self.selected_anchors,
        }


class WebAccessHealthPolicy:
    """Restrict web-access to public-health information tasks."""

    def __init__(
        self,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ):
        self.allowed_domains = [item.lower().strip() for item in (allowed_domains or []) if item and item.strip()]
        self.blocked_domains = list(BLOCKED_HOST_SUFFIXES)
        for item in blocked_domains or []:
            clean = item.lower().strip()
            if clean and clean not in self.blocked_domains:
                self.blocked_domains.append(clean)

    def validate_url(self, url: str) -> tuple[bool, str | None]:
        parsed = urllib.parse.urlparse(url)
        if (parsed.scheme or "").lower() not in {"http", "https"}:
            return False, "Only http(s) public pages are allowed."
        if parsed.scheme.lower() in BLOCKED_SCHEMES:
            return False, "Blocked URL scheme."
        host = _normalized_host(url)
        if not host:
            return False, "Missing hostname."
        if _host_matches(host, self.blocked_domains):
            return False, f"Blocked non-health domain: {host}"
        if self.allowed_domains and not _host_matches(host, self.allowed_domains):
            return False, f"Domain not allowed by source policy: {host}"
        return True, None


class WebAccessRuntime:
    """Static + browser fallback fetcher for controlled public-health browsing."""

    def __init__(
        self,
        policy: WebAccessHealthPolicy | None = None,
        static_fetcher=None,
        browser_fetcher=None,
        runtime_checker=None,
    ):
        self.policy = policy or WebAccessHealthPolicy()
        self.static_fetcher = static_fetcher or self._fetch_url_text
        self.browser_fetcher = browser_fetcher
        self.runtime_checker = runtime_checker or self._run_check_deps

    def _fetch_url_text(self, url: str, timeout: int = 20) -> str:
        request = urllib.request.Request(url, headers=_default_headers())
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _run_check_deps(self) -> dict:
        script = _check_deps_script()
        if not script.exists():
            return {
                "ready": False,
                "reason": "web-access skill not installed",
                "script": str(script),
            }
        try:
            result = subprocess.run(
                ["bash", str(script)],
                capture_output=True,
                text=True,
                check=False,
                timeout=45,
            )
        except Exception as exc:
            return {
                "ready": False,
                "reason": exc.__class__.__name__,
                "notes": [str(exc)],
                "script": str(script),
            }
        return {
            "ready": result.returncode == 0,
            "reason": "ok" if result.returncode == 0 else "runtime-check-failed",
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "script": str(script),
        }

    def _parse_static_snapshot(self, url: str, html: str) -> PageSnapshot:
        parser = _AnchorParser()
        parser.feed(html)
        anchors = []
        for item in parser.anchors:
            href = item["href"].strip()
            if not href:
                continue
            absolute = urllib.parse.urljoin(url, href)
            anchors.append({"href": absolute, "text": item.get("text", "").strip()})
        return PageSnapshot(
            url=url,
            title=parser.title.strip(),
            text=html_to_text(html)[:30000],
            headings=parser.headings[:20],
            anchors=anchors[:400],
            mode_used="static",
            meta_description=parser.description.strip(),
            raw_html=html,
        )

    def _page_needs_browser(self, snapshot: PageSnapshot) -> bool:
        lowered = (snapshot.text or "").lower()
        if any(marker in lowered for marker in DYNAMIC_PAGE_MARKERS):
            return True
        if len(snapshot.text or "") < 220 and len(snapshot.anchors or []) < 4:
            return True
        if not snapshot.title and not snapshot.headings and len(snapshot.text or "") < 400:
            return True
        return False

    def _call_proxy_json(self, url: str, method: str = "GET", data: str | None = None, timeout: int = 30):
        payload = data.encode("utf-8") if data is not None else None
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "text/plain; charset=utf-8", **_default_headers()},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="ignore")
        return json.loads(body or "{}")

    def _browser_fetch(self, url: str, entry_selector: str | None = None) -> PageSnapshot:
        runtime = self.runtime_checker()
        if not runtime.get("ready"):
            raise RuntimeError(runtime.get("reason") or "browser runtime not ready")
        target = self._call_proxy_json(
            f"http://127.0.0.1:3456/new?url={urllib.parse.quote(url, safe='')}",
            timeout=45,
        ).get("targetId")
        if not target:
            raise RuntimeError("web-access proxy failed to create target")
        try:
            selector_json = json.dumps(entry_selector) if entry_selector else "null"
            script = f"""
(() => {{
  const pack = (anchor) => {{
    const href = (anchor.href || "").trim();
    const text = (anchor.textContent || "").replace(/\\s+/g, " ").trim();
    return href ? {{ href, text }} : null;
  }};
  const anchors = Array.from(document.querySelectorAll("a[href]"))
    .map(pack)
    .filter(Boolean)
    .slice(0, 400);
  const selectedAnchors = {selector_json}
    ? Array.from(document.querySelectorAll({selector_json}))
        .filter((node) => node && node.href)
        .map(pack)
        .filter(Boolean)
        .slice(0, 120)
    : [];
  const headings = Array.from(document.querySelectorAll("h1, h2, h3"))
    .map((node) => (node.textContent || "").replace(/\\s+/g, " ").trim())
    .filter(Boolean)
    .slice(0, 20);
  const meta =
    document.querySelector('meta[name="description"]')?.content ||
    document.querySelector('meta[property="og:description"]')?.content ||
    "";
  return JSON.stringify({{
    url: location.href,
    title: document.title || "",
    text: (document.body?.innerText || "").replace(/\\s+/g, " ").trim().slice(0, 30000),
    headings,
    anchors,
    selectedAnchors,
    metaDescription: meta,
  }});
}})()
""".strip()
            payload = self._call_proxy_json(
                f"http://127.0.0.1:3456/eval?target={urllib.parse.quote(target, safe='')}",
                method="POST",
                data=script,
                timeout=45,
            )
            if payload.get("error"):
                raise RuntimeError(payload["error"])
            parsed = json.loads(payload.get("value") or "{}")
            return PageSnapshot(
                url=parsed.get("url") or url,
                title=parsed.get("title", ""),
                text=parsed.get("text", ""),
                headings=parsed.get("headings") or [],
                anchors=parsed.get("anchors") or [],
                selected_anchors=parsed.get("selectedAnchors") or [],
                meta_description=parsed.get("metaDescription", ""),
                mode_used="browser",
            )
        finally:
            try:
                self._call_proxy_json(
                    f"http://127.0.0.1:3456/close?target={urllib.parse.quote(target, safe='')}",
                    timeout=10,
                )
            except Exception:
                pass

    def fetch_page(
        self,
        url: str,
        mode: str = "auto",
        entry_selector: str | None = None,
        policy: WebAccessHealthPolicy | None = None,
    ) -> PageSnapshot:
        active_policy = policy or self.policy
        allowed, reason = active_policy.validate_url(url)
        if not allowed:
            raise ValueError(reason or "blocked by health web policy")

        if mode not in {"auto", "static", "browser"}:
            raise ValueError(f"Unsupported mode: {mode}")

        if mode in {"auto", "static"}:
            html = self.static_fetcher(url)
            snapshot = self._parse_static_snapshot(url, html)
            if mode == "static":
                return snapshot
            if not self._page_needs_browser(snapshot):
                return snapshot
            snapshot.notes.append("Static snapshot suggests JS-heavy or low-signal page; trying browser fallback.")

        if mode == "browser" or self.browser_fetcher is not None:
            try:
                if self.browser_fetcher is not None:
                    browser_snapshot = self.browser_fetcher(url, entry_selector=entry_selector)
                    if isinstance(browser_snapshot, PageSnapshot):
                        return browser_snapshot
                    return PageSnapshot(**browser_snapshot)
                return self._browser_fetch(url, entry_selector=entry_selector)
            except Exception as exc:
                if mode == "browser":
                    raise
                snapshot.notes.append(f"Browser fallback unavailable: {exc.__class__.__name__}")
                return snapshot

        return snapshot
