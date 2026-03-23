#!/usr/bin/env python3
"""Public doctor profile harvesting built on VitaClaw's controlled web access."""

from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path

from doctor_matching import load_json_file
from web_access_runtime import PageSnapshot, WebAccessHealthPolicy, WebAccessRuntime


DEFAULT_LINK_PATTERNS = (
    "doctor",
    "physician",
    "expert",
    "faculty",
    "team",
    "staff",
    "医生",
    "医师",
    "专家",
    "主任",
    "教授",
)

DEPARTMENT_HINTS = (
    "心内科",
    "高血压门诊",
    "内分泌科",
    "消化内科",
    "肝病门诊",
    "肾内科",
    "全科医学科",
    "综合内科",
    "精神心理科",
    "心身医学门诊",
    "Cardiology",
    "Endocrinology",
    "General Internal Medicine",
    "Gastroenterology",
    "Nephrology",
)

SPECIALTY_LEADERS = (
    "擅长",
    "专业方向",
    "研究方向",
    "specialties",
    "focus",
    "special interest",
)

FOLLOWUP_HINTS = (
    "长期随访",
    "慢病管理",
    "连续管理",
    "follow-up",
    "continuity clinic",
    "chronic disease",
)

SCHEDULE_HINTS = (
    "门诊时间",
    "出诊",
    "clinic",
    "schedule",
    "周一",
    "周二",
    "周三",
    "周四",
    "周五",
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
)


def _uniq(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _clean_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _split_terms(text: str) -> list[str]:
    return [item.strip(" -•·:：") for item in re.split(r"[;,，、/|]", text or "") if item.strip(" -•·:：")]


def _extract_english_name(text: str) -> str | None:
    matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b", text or "")
    for item in matches:
        clean = item.strip()
        if len(clean) >= 5:
            return clean
    return None


def _extract_chinese_name(text: str) -> str | None:
    patterns = [
        r"([一-龥]{2,4})\s*(?:医生|医师|主任|教授)",
        r"(?:医生|医师|主任|教授)\s*([一-龥]{2,4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text or "")
        if match:
            return match.group(1)
    generic = re.findall(r"[一-龥]{2,4}", text or "")
    for item in generic:
        if item not in {"医院", "门诊", "专家", "医生", "医师", "主任", "教授"}:
            return item
    return None


def _extract_name(page: PageSnapshot, source: dict) -> tuple[str | None, str | None]:
    if source.get("name_hint"):
        return str(source["name_hint"]).strip(), source.get("english_name_hint")

    candidates = [page.title, *page.headings[:8], page.meta_description, page.text[:400]]
    chinese_name = None
    english_name = None
    for item in candidates:
        chinese_name = chinese_name or _extract_chinese_name(item)
        english_name = english_name or _extract_english_name(item)
    if chinese_name or english_name:
        return chinese_name or english_name, english_name
    return None, None


def _extract_department(page: PageSnapshot, source: dict) -> str | None:
    if source.get("department_hint"):
        return str(source["department_hint"]).strip()
    blob = " ".join([page.title, *page.headings, page.meta_description, page.text[:1200]])
    for hint in DEPARTMENT_HINTS:
        if hint.lower() in blob.lower():
            return hint
    return None


def _extract_specialties(page: PageSnapshot) -> list[str]:
    lines = [page.meta_description, *page.headings, *re.split(r"(?<=[。.!?])\s+", page.text[:1600])]
    results: list[str] = []
    for line in lines:
        clean = _clean_space(line)
        if not clean:
            continue
        lowered = clean.lower()
        if any(token in lowered for token in SPECIALTY_LEADERS):
            results.extend(_split_terms(clean))
    return _uniq(results[:8])


def _extract_schedule(page: PageSnapshot) -> str:
    lines = [page.meta_description, *page.headings, *re.split(r"(?<=[。.!?])\s+", page.text[:1800])]
    for line in lines:
        clean = _clean_space(line)
        if not clean:
            continue
        lowered = clean.lower()
        if any(token.lower() in lowered for token in SCHEDULE_HINTS):
            return clean[:240]
    return ""


def _accepts_followup(page: PageSnapshot) -> bool:
    lowered = (page.text or "").lower()
    return any(token.lower() in lowered for token in FOLLOWUP_HINTS)


def _same_or_child_domain(base_url: str, href: str) -> bool:
    base = urllib.parse.urlparse(base_url)
    target = urllib.parse.urlparse(href)
    if not target.hostname:
        return True
    base_host = (base.hostname or "").lower()
    target_host = (target.hostname or "").lower()
    return target_host == base_host or target_host.endswith(f".{base_host}")


def merge_doctor_candidates(*groups: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen_keys: set[str] = set()
    for group in groups:
        for item in group or []:
            key = str(item.get("official_profile_url") or "").strip().lower()
            if not key:
                key = "|".join(
                    [
                        str(item.get("name") or "").strip().lower(),
                        str(item.get("hospital") or "").strip().lower(),
                        str(item.get("department") or "").strip().lower(),
                    ]
                )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            merged.append(item)
    return merged


class DoctorProfileHarvester:
    """Harvest doctor candidates from public hospital pages."""

    def __init__(self, web_runtime: WebAccessRuntime | None = None):
        self.web_runtime = web_runtime or WebAccessRuntime()

    def _source_policy(self, source: dict) -> WebAccessHealthPolicy:
        return WebAccessHealthPolicy(
            allowed_domains=list(source.get("allowed_domains") or []),
        )

    def _extract_profile_links(self, source: dict, page: PageSnapshot) -> list[str]:
        explicit = [str(item).strip() for item in source.get("profile_urls") or [] if str(item).strip()]
        if explicit:
            return _uniq(explicit)

        patterns = [item.lower().strip() for item in source.get("link_substrings") or [] if item and item.strip()]
        if not patterns:
            patterns = list(DEFAULT_LINK_PATTERNS)
        candidates = page.selected_anchors or page.anchors
        profile_urls: list[str] = []
        for item in candidates:
            href = str(item.get("href") or "").strip()
            text = str(item.get("text") or "").strip()
            if not href or not _same_or_child_domain(page.url, href):
                continue
            haystack = f"{href} {text}".lower()
            if any(pattern in haystack for pattern in patterns):
                profile_urls.append(href)
        if profile_urls:
            return _uniq(profile_urls)

        title_like = f"{page.title} {' '.join(page.headings[:4])}".lower()
        if any(pattern in title_like for pattern in ("医生", "专家", "doctor", "physician")):
            return [page.url]
        return []

    def _page_to_candidate(self, page: PageSnapshot, source: dict) -> dict | None:
        name, english_name = _extract_name(page, source)
        if not name and len(page.text or "") < 120:
            return None
        department = _extract_department(page, source)
        specialties = _extract_specialties(page)
        notes = list(page.notes)
        if not department:
            notes.append("未能从公开页面稳定识别科室，建议人工复核。")

        candidate = {
            "name": name or page.title[:40] or "Unknown",
            "english_name": english_name,
            "hospital": source.get("hospital"),
            "department": department,
            "city": source.get("city"),
            "district": source.get("district"),
            "specialties": specialties,
            "official_profile_url": page.url,
            "schedule": _extract_schedule(page),
            "accepts_long_term_followup": _accepts_followup(page),
            "profile_text": (page.meta_description or page.text or "")[:3000],
            "source_refs": [page.url],
            "harvest_mode": page.mode_used,
            "harvest_notes": notes,
        }
        if source.get("pubmed_query_hint"):
            candidate["pubmed_query"] = source["pubmed_query_hint"]
        return candidate

    def harvest_sources(
        self,
        sources: list[dict],
        mode: str = "auto",
        per_source_limit: int | None = None,
    ) -> dict:
        harvested: list[dict] = []
        log: list[dict] = []
        source_refs: list[str] = []

        for source in sources:
            source_url = str(source.get("source_url") or "").strip()
            if not source_url:
                log.append({"source_url": "", "status": "skipped", "reason": "missing source_url"})
                continue

            source_mode = str(source.get("mode") or mode or "auto")
            limit = int(source.get("limit") or per_source_limit or 6)
            policy = self._source_policy(source)

            try:
                directory_page = self.web_runtime.fetch_page(
                    source_url,
                    mode=source_mode,
                    entry_selector=source.get("entry_selector"),
                    policy=policy,
                )
            except Exception as exc:
                log.append(
                    {
                        "source_url": source_url,
                        "status": "failed",
                        "reason": f"{exc.__class__.__name__}: {exc}",
                    }
                )
                continue

            source_refs.append(directory_page.url)
            profile_urls = self._extract_profile_links(source, directory_page)[:limit]
            if not profile_urls:
                maybe_candidate = self._page_to_candidate(directory_page, source)
                if maybe_candidate:
                    harvested.append(maybe_candidate)
                    log.append(
                        {
                            "source_url": source_url,
                            "status": "single-profile",
                            "count": 1,
                            "mode_used": directory_page.mode_used,
                        }
                    )
                else:
                    log.append(
                        {
                            "source_url": source_url,
                            "status": "no-profile-links",
                            "count": 0,
                            "mode_used": directory_page.mode_used,
                        }
                    )
                continue

            added = 0
            for profile_url in profile_urls:
                try:
                    page = self.web_runtime.fetch_page(
                        profile_url,
                        mode=source_mode,
                        policy=policy,
                    )
                except Exception as exc:
                    log.append(
                        {
                            "source_url": source_url,
                            "profile_url": profile_url,
                            "status": "profile-fetch-failed",
                            "reason": f"{exc.__class__.__name__}: {exc}",
                        }
                    )
                    continue
                source_refs.append(page.url)
                candidate = self._page_to_candidate(page, source)
                if not candidate:
                    log.append(
                        {
                            "source_url": source_url,
                            "profile_url": profile_url,
                            "status": "profile-skipped",
                            "reason": "insufficient public profile text",
                        }
                    )
                    continue
                harvested.append(candidate)
                added += 1
            log.append(
                {
                    "source_url": source_url,
                    "status": "ok",
                    "count": added,
                    "mode_used": directory_page.mode_used,
                    "profile_urls": profile_urls,
                }
            )

        merged = merge_doctor_candidates(harvested)
        return {
            "candidates": merged,
            "source_refs": _uniq(source_refs),
            "harvest_log": log,
        }


def load_sources_file(path: str | Path) -> list[dict]:
    payload = load_json_file(path)
    if isinstance(payload, list):
        return payload
    raise ValueError("doctor source file must be a JSON array")


def render_harvest_markdown(result: dict) -> str:
    lines = ["# Doctor Profile Harvester", ""]
    lines.append("## Harvest Summary")
    lines.append("")
    lines.append(f"- Candidates: {len(result.get('candidates') or [])}")
    lines.append(f"- Source refs: {len(result.get('source_refs') or [])}")
    lines.append("")
    lines.append("## Candidates")
    lines.append("")
    if not result.get("candidates"):
        lines.append("- 暂无候选医生。")
    for item in result.get("candidates") or []:
        lines.append(
            f"- {item.get('name', 'Unknown')} | {item.get('hospital', 'Unknown hospital')} | "
            f"{item.get('department', 'Unknown department')} | {item.get('official_profile_url', '')}"
        )
        if item.get("specialties"):
            lines.append(f"  擅长线索：{', '.join(item['specialties'][:4])}")
        if item.get("schedule"):
            lines.append(f"  出诊线索：{item['schedule']}")
    lines.append("")
    lines.append("## Harvest Log")
    lines.append("")
    for item in result.get("harvest_log") or []:
        status = item.get("status", "pending")
        source_url = item.get("source_url", "")
        reason = item.get("reason")
        extra = f" count={item.get('count')}" if item.get("count") is not None else ""
        note = f" ({reason})" if reason else ""
        lines.append(f"- {status}: {source_url}{extra}{note}")
    return "\n".join(lines).rstrip() + "\n"
