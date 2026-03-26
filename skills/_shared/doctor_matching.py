#!/usr/bin/env python3
"""Shared public-doctor matching helpers for VitaClaw."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

TERM_TRANSLATIONS = {
    "高血压": "hypertension",
    "血压": "blood pressure",
    "心血管": "cardiovascular",
    "胸痛": "chest pain",
    "心悸": "palpitations",
    "糖尿病": "diabetes",
    "糖前期": "prediabetes",
    "血糖": "glucose",
    "脂肪肝": "fatty liver",
    "肝功能": "liver function",
    "血脂": "lipid",
    "甘油三酯": "triglyceride",
    "胆固醇": "cholesterol",
    "肾功能": "kidney function",
    "尿酸": "uric acid",
    "失眠": "sleep",
    "焦虑": "anxiety",
    "抑郁": "depression",
    "甲状腺": "thyroid",
    "体检": "checkup",
    "复诊": "follow-up",
    "减重": "weight management",
    "肥胖": "obesity",
    "营养": "nutrition",
}


DEPARTMENT_RULES = [
    {
        "department": "心内科 / 高血压门诊",
        "keywords": [
            "hypertension",
            "blood pressure",
            "高血压",
            "血压",
            "晨起头胀",
            "headache",
            "palpitations",
            "胸闷",
            "cardiovascular",
            "lipid",
            "血脂",
            "甘油三酯",
        ],
        "reason": "更适合处理高血压、心血管危险因素和长期随访。",
        "preparation": "准备近 2 周家庭血压、用药清单、血脂/体重变化和症状时间线。",
        "urgency": "routine",
    },
    {
        "department": "内分泌科",
        "keywords": [
            "diabetes",
            "prediabetes",
            "glucose",
            "hba1c",
            "糖尿病",
            "糖前期",
            "血糖",
            "肥胖",
            "obesity",
            "thyroid",
            "甲状腺",
        ],
        "reason": "更适合处理血糖异常、糖代谢风险、体重和内分泌问题。",
        "preparation": "准备空腹 / 餐后血糖、HbA1c、体重变化、饮食运动记录。",
        "urgency": "routine",
    },
    {
        "department": "消化内科 / 肝病门诊",
        "keywords": [
            "alt",
            "ast",
            "fatty liver",
            "肝功能",
            "脂肪肝",
            "转氨酶",
            "肝",
            "尿酸",
        ],
        "reason": "更适合处理脂肪肝、肝功能异常和代谢相关肝病。",
        "preparation": "准备近两次肝功能、腹部超声、饮酒 / 体重变化和药物补剂情况。",
        "urgency": "routine",
    },
    {
        "department": "肾内科",
        "keywords": [
            "egfr",
            "creatinine",
            "urine protein",
            "kidney",
            "肾功能",
            "肌酐",
            "蛋白尿",
            "尿白蛋白",
        ],
        "reason": "更适合处理肾功能、蛋白尿和慢病相关肾脏风险。",
        "preparation": "准备肌酐、eGFR、尿检、血压和用药史。",
        "urgency": "routine",
    },
    {
        "department": "全科医学科 / 综合内科",
        "keywords": [
            "checkup",
            "annual checkup",
            "体检",
            "多个异常",
            "multiple abnormalities",
            "continuity",
            "长期管理",
            "follow-up coordination",
        ],
        "reason": "适合先整合多个体检异常、梳理路径，再决定是否转专科。",
        "preparation": "准备完整体检报告、既往病史、正在服用的药物和最想解决的问题。",
        "urgency": "routine",
    },
    {
        "department": "精神心理科 / 心身医学门诊",
        "keywords": [
            "depression",
            "anxiety",
            "panic",
            "sleep",
            "insomnia",
            "抑郁",
            "焦虑",
            "失眠",
            "情绪",
        ],
        "reason": "适合处理睡眠-情绪联动、压力、焦虑和抑郁症状。",
        "preparation": "准备最近 2 周睡眠、情绪、功能影响和量表分数。",
        "urgency": "routine",
    },
    {
        "department": "儿科 / 儿内科",
        "keywords": [
            "pediatric",
            "child",
            "infant",
            "baby",
            "toddler",
            "儿童",
            "小孩",
            "宝宝",
            "婴儿",
            "幼儿",
            "孩子",
            "发烧",
            "发热",
            "fever",
            "手足口",
            "小儿",
            "新生儿",
        ],
        "reason": "儿童疾病（发热、感染、发育等）应由儿科专科医生评估和处理。",
        "preparation": (
            "准备体温记录、发热时长、伴随症状（咳嗽/呕吐/皮疹/精神状态）、"
            "年龄月龄、既往病史和疫苗接种情况。"
        ),
        "urgency": "routine",
    },
    {
        "department": "发热门诊",
        "keywords": [
            "发烧",
            "发热",
            "fever",
            "高热",
            "高烧",
            "体温",
            "感染",
            "流感",
        ],
        "reason": "发热需排查感染源，发热门诊可快速做血常规、流感/新冠筛查等。",
        "preparation": "准备体温峰值和变化曲线、发热天数、伴随症状（咳嗽/咽痛/腹泻）、接触史和用药情况。",
        "urgency": "urgent",
    },
]


RED_FLAG_RULES = [
    ("胸痛", "若伴胸痛等急性危险症状，应优先线下急诊/胸痛中心，而不是普通门诊比选。"),
    ("chest pain", "If chest pain is present, acute care should come before doctor matching."),
    ("呼吸困难", "若伴呼吸困难或明显进行性恶化，应先急诊评估。"),
    ("severe shortness of breath", "Severe shortness of breath should be escalated to emergency evaluation."),
    ("晕厥", "晕厥/黑矇属于高危信号，应先急诊评估。"),
    ("severe hypoglycemia", "Severe hypoglycemia should be escalated before routine doctor matching."),
    ("高烧不退", "持续高热应优先到发热门诊或急诊就诊，不宜等普通门诊。"),
    ("惊厥", "出现惊厥/抽搐应立即急诊救治。"),
]


def _slugify(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return re.sub(r"-{2,}", "-", clean).strip("-") or "item"


def _uniq(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _flatten_terms(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = re.split(r"[;\n,，、]", value)
        return [item.strip() for item in items if item.strip()]
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_flatten_terms(item))
        return result
    return [str(value).strip()]


def _expand_terms(values: list[str]) -> list[str]:
    terms = []
    for raw in values:
        clean = raw.strip()
        if not clean:
            continue
        terms.append(clean)
        translated = TERM_TRANSLATIONS.get(clean)
        if translated:
            terms.append(translated)
    return _uniq(terms)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _contains_any(text: str, keywords: list[str]) -> list[str]:
    lowered = _normalize_text(text)
    matches = []
    for keyword in keywords:
        if _normalize_text(keyword) and _normalize_text(keyword) in lowered:
            matches.append(keyword)
    return _uniq(matches)


def _ascii_name_candidates(doctor: dict) -> list[str]:
    raw = []
    for key in ("english_name", "pubmed_name", "name"):
        value = doctor.get(key)
        if value:
            raw.append(str(value))
    for alias in doctor.get("aliases", []) or []:
        raw.append(str(alias))
    result = []
    for item in raw:
        if re.search(r"[A-Za-z]", item):
            result.append(item.strip())
    return _uniq(result)


class _HTMLToText(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip = False
        self._parts: list[str] = []

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
            self._parts.append(text)

    def get_text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._parts)).strip()


def html_to_text(html: str) -> str:
    parser = _HTMLToText()
    parser.feed(html)
    return parser.get_text()


def fetch_url_text(url: str, headers: dict | None = None, timeout: int = 20) -> str:
    request = urllib.request.Request(
        url,
        headers=headers
        or {
            "User-Agent": "VitaClaw/1.0 (+https://github.com/vitaclaw/vitaclaw)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


@dataclass
class DepartmentRecommendation:
    department: str
    score: int
    matched_terms: list[str]
    reason: str
    preparation: str
    urgency: str


class DepartmentFitRouter:
    """Route the user's problem to likely departments using conservative rules."""

    def route(self, patient_profile: dict, top_n: int = 3) -> dict:
        terms = _expand_terms(
            _flatten_terms(patient_profile.get("conditions"))
            + _flatten_terms(patient_profile.get("symptoms"))
            + _flatten_terms(patient_profile.get("abnormal_findings"))
            + _flatten_terms(patient_profile.get("goals"))
            + _flatten_terms(patient_profile.get("summary"))
        )
        text_blob = " | ".join(terms)
        recommendations: list[DepartmentRecommendation] = []

        for rule in DEPARTMENT_RULES:
            matched = _contains_any(text_blob, rule["keywords"])
            if not matched:
                continue
            score = min(95, 35 + len(matched) * 8)
            recommendations.append(
                DepartmentRecommendation(
                    department=rule["department"],
                    score=score,
                    matched_terms=matched,
                    reason=rule["reason"],
                    preparation=rule["preparation"],
                    urgency=rule["urgency"],
                )
            )

        if not recommendations:
            recommendations.append(
                DepartmentRecommendation(
                    department="全科医学科 / 综合内科",
                    score=35,
                    matched_terms=[],
                    reason="当前信息不足以精确路由，先用全科/综合内科整合问题更稳妥。",
                    preparation="准备最困扰你的 1-3 个问题、近期关键指标和既往检查。",
                    urgency="routine",
                )
            )

        recommendations.sort(key=lambda item: (-item.score, item.department))
        urgent = []
        for keyword, message in RED_FLAG_RULES:
            if _normalize_text(keyword) in _normalize_text(text_blob):
                urgent.append(message)

        return {
            "input_terms": terms,
            "recommendations": [
                {
                    "department": item.department,
                    "score": item.score,
                    "matched_terms": item.matched_terms,
                    "reason": item.reason,
                    "preparation": item.preparation,
                    "urgency": item.urgency,
                }
                for item in recommendations[:top_n]
            ],
            "must_seek_care": _uniq(urgent),
        }


class PubMedClient:
    """Thin wrapper around the official NCBI E-utilities API."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, email: str | None = None, fetcher=None, delay_seconds: float = 0.34):
        self.email = email
        self.fetcher = fetcher or fetch_url_text
        self.delay_seconds = delay_seconds

    def _build_url(self, endpoint: str, params: dict[str, str]) -> str:
        payload = dict(params)
        if self.email:
            payload["email"] = self.email
        query = urllib.parse.urlencode(payload, doseq=True)
        return f"{self.BASE_URL}/{endpoint}?{query}"

    def _fetch(self, endpoint: str, params: dict[str, str]) -> str:
        url = self._build_url(endpoint, params)
        text = self.fetcher(url)
        time.sleep(self.delay_seconds)
        return text

    def search(self, query: str, max_results: int = 5) -> list[str]:
        response = self._fetch(
            "esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmax": str(max_results),
                "sort": "pub date",
                "retmode": "json",
            },
        )
        payload = json.loads(response or "{}")
        return payload.get("esearchresult", {}).get("idlist", []) or []

    def fetch_articles(self, pmids: list[str]) -> list[dict]:
        if not pmids:
            return []
        xml_text = self._fetch(
            "efetch.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
            },
        )
        root = ET.fromstring(xml_text)
        results = []
        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID") or ""
            title = article.findtext(".//ArticleTitle") or ""
            abstract = " ".join(
                (element.text or "").strip()
                for element in article.findall(".//Abstract/AbstractText")
                if (element.text or "").strip()
            )
            journal = article.findtext(".//Journal/Title") or ""
            year = article.findtext(".//PubDate/Year") or article.findtext(".//ArticleDate/Year") or ""
            authors = []
            for author in article.findall(".//Author"):
                last = author.findtext("LastName") or ""
                fore = author.findtext("ForeName") or ""
                collective = author.findtext("CollectiveName") or ""
                name = " ".join(part for part in (fore, last) if part).strip() or collective
                if name:
                    authors.append(name)
            results.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "journal": journal,
                    "year": year,
                    "authors": authors,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                }
            )
        return results


class DoctorEvidenceProfiler:
    """Build a conservative evidence profile from official pages and PubMed."""

    def __init__(self, fetcher=None, pubmed_client: PubMedClient | None = None):
        self.fetcher = fetcher or fetch_url_text
        self.pubmed_client = pubmed_client or PubMedClient(fetcher=self.fetcher)

    def _fetch_profile_text(self, doctor: dict) -> tuple[str, list[str]]:
        source_refs = []
        if doctor.get("profile_text"):
            return str(doctor["profile_text"]), source_refs
        profile_url = doctor.get("official_profile_url") or doctor.get("profile_url")
        if not profile_url:
            return "", source_refs
        try:
            html = self.fetcher(profile_url)
            source_refs.append(profile_url)
            return html_to_text(html), source_refs
        except Exception as exc:  # pragma: no cover - network path
            return "", [f"{profile_url} (fetch failed: {exc.__class__.__name__})"]

    def _derive_pubmed_query(self, doctor: dict, patient_terms: list[str]) -> tuple[str | None, str | None]:
        explicit = doctor.get("pubmed_query")
        if explicit:
            return str(explicit), None

        aliases = _ascii_name_candidates(doctor)
        if not aliases:
            return None, "缺少可用于 PubMed 的英文姓名或显式 pubmed_query，论文画像将只作为有限信号。"

        base_name = aliases[0]
        specialty_terms = _expand_terms(
            _flatten_terms(doctor.get("specialties")) + _flatten_terms(doctor.get("department")) + patient_terms
        )
        search_terms = [term for term in specialty_terms if re.search(r"[A-Za-z]", term)]
        query = f'"{base_name}"[Author]'
        if search_terms:
            query += " AND (" + " OR ".join(f'"{term}"' for term in search_terms[:4]) + ")"
        return query, None

    def profile(
        self,
        doctor: dict,
        patient_profile: dict | None = None,
        pubmed_mode: str = "auto",
        max_papers: int = 5,
    ) -> dict:
        patient_terms = _expand_terms(
            _flatten_terms((patient_profile or {}).get("conditions"))
            + _flatten_terms((patient_profile or {}).get("abnormal_findings"))
            + _flatten_terms((patient_profile or {}).get("goals"))
        )
        profile_text, source_refs = self._fetch_profile_text(doctor)
        query, caution = self._derive_pubmed_query(doctor, patient_terms)
        notes = []
        if caution:
            notes.append(caution)

        papers: list[dict] = []
        pubmed_query = None
        if pubmed_mode != "off" and query:
            try:
                pmids = self.pubmed_client.search(query, max_results=max_papers)
                papers = self.pubmed_client.fetch_articles(pmids)
                pubmed_query = query
            except Exception as exc:  # pragma: no cover - network path
                notes.append(f"PubMed 查询失败：{exc.__class__.__name__}")
        elif pubmed_mode == "required":
            notes.append("本轮要求启用 PubMed，但当前医生资料无法形成可靠查询。")

        topic_terms = _expand_terms(
            _flatten_terms(doctor.get("specialties")) + _flatten_terms(doctor.get("department")) + patient_terms
        )
        relevant_papers = []
        recent_count = 0
        this_year = time.localtime().tm_year
        for paper in papers:
            haystack = _normalize_text((paper.get("title") or "") + " " + (paper.get("abstract") or ""))
            matched = _contains_any(haystack, topic_terms)
            if matched:
                relevant_papers.append({**paper, "matched_terms": matched})
            year = str(paper.get("year") or "")
            if year.isdigit() and int(year) >= this_year - 5:
                recent_count += 1
            if paper.get("url"):
                source_refs.append(paper["url"])

        source_refs = _uniq(source_refs)
        evidence_score = 0
        evidence_signal = "limited"
        if relevant_papers:
            evidence_score += min(6, len(relevant_papers) * 2)
        if recent_count:
            evidence_score += min(4, recent_count)
        if profile_text:
            evidence_score += 2
        evidence_score = min(10, evidence_score)

        if evidence_score >= 8:
            evidence_signal = "strong"
        elif evidence_score >= 5:
            evidence_signal = "moderate"

        highlights = []
        if profile_text:
            highlights.append(profile_text[:220] + ("..." if len(profile_text) > 220 else ""))
        if relevant_papers:
            highlights.append(f"PubMed 相关论文 {len(relevant_papers)} 篇，近 5 年 {recent_count} 篇。")
        elif papers:
            highlights.append(f"PubMed 检索到 {len(papers)} 篇公开论文，但与当前患者主题直接匹配有限。")

        return {
            "doctor_name": doctor.get("name", "Unknown"),
            "profile_summary": highlights,
            "profile_text": profile_text,
            "source_refs": source_refs,
            "pubmed_query": pubmed_query,
            "paper_count": len(papers),
            "recent_paper_count": recent_count,
            "relevant_paper_count": len(relevant_papers),
            "selected_papers": relevant_papers[:max_papers] or papers[:max_papers],
            "evidence_signal": evidence_signal,
            "evidence_score": evidence_score,
            "notes": notes,
        }


class DoctorFitFinder:
    """Rank public doctor candidates for a given patient profile."""

    def __init__(
        self, router: DepartmentFitRouter | None = None, evidence_profiler: DoctorEvidenceProfiler | None = None
    ):
        self.router = router or DepartmentFitRouter()
        self.evidence_profiler = evidence_profiler or DoctorEvidenceProfiler()

    def _score_department(self, doctor: dict, route_result: dict) -> tuple[int, list[str]]:
        department_text = _normalize_text(
            str(doctor.get("department", "")) + " " + " ".join(_flatten_terms(doctor.get("specialties")))
        )
        reasons = []
        score = 0
        for index, item in enumerate(route_result.get("recommendations", [])):
            department = item["department"]
            tokens = [department] + _flatten_terms(item.get("matched_terms"))
            if _contains_any(department_text, tokens):
                bonus = max(12, 35 - index * 8)
                score = max(score, bonus)
                reasons.append(f"与推荐科室“{department}”高度贴合")
        if not score and _contains_any(department_text, ["全科", "general", "综合内科"]):
            score = 10
            reasons.append("可作为首诊整合路径的兜底选择")
        return score, reasons

    def _score_topic_match(self, doctor: dict, patient_profile: dict, evidence_profile: dict) -> tuple[int, list[str]]:
        patient_terms = _expand_terms(
            _flatten_terms(patient_profile.get("conditions"))
            + _flatten_terms(patient_profile.get("abnormal_findings"))
            + _flatten_terms(patient_profile.get("goals"))
        )
        doctor_text = _normalize_text(
            " ".join(
                [
                    str(doctor.get("department", "")),
                    " ".join(_flatten_terms(doctor.get("specialties"))),
                    evidence_profile.get("profile_text", ""),
                ]
            )
        )
        matched = _contains_any(doctor_text, patient_terms)
        score = min(25, len(matched) * 5)
        reasons = [f"公开简介与患者主题匹配：{term}" for term in matched[:4]]
        return score, reasons

    def _score_location(self, doctor: dict, patient_profile: dict) -> tuple[int, list[str]]:
        city = str(patient_profile.get("city") or "").strip()
        district = str(patient_profile.get("district") or "").strip()
        preferred_hospitals = _flatten_terms(patient_profile.get("preferred_hospitals"))
        score = 0
        reasons = []
        if city and city == str(doctor.get("city") or "").strip():
            score += 10
            reasons.append("与用户所在城市一致")
        if district and district == str(doctor.get("district") or "").strip():
            score += 5
            reasons.append("与用户偏好区县一致")
        if preferred_hospitals and str(doctor.get("hospital") or "").strip() in preferred_hospitals:
            score += 5
            reasons.append("命中用户偏好的医院")
        return min(15, score), reasons

    def _score_continuity(self, doctor: dict, patient_profile: dict) -> tuple[int, list[str]]:
        score = 0
        reasons = []
        continuity_preference = _normalize_text(str(patient_profile.get("continuity_preference") or ""))
        if doctor.get("accepts_long_term_followup") is True:
            score += 6
            reasons.append("适合长期连续随访")
        schedule = str(doctor.get("schedule") or doctor.get("clinic_schedule") or "")
        if schedule:
            score += 4
            reasons.append("公开出诊信息明确，便于预约")
        if "长期" in continuity_preference or "long-term" in continuity_preference:
            score += 2 if doctor.get("accepts_long_term_followup") else 0
        return min(10, score), reasons

    def _score_evidence(self, evidence_profile: dict) -> tuple[int, list[str]]:
        score = int(evidence_profile.get("evidence_score") or 0)
        signal = evidence_profile.get("evidence_signal", "limited")
        reasons = [f"公开证据画像：{signal}"]
        if evidence_profile.get("relevant_paper_count"):
            reasons.append(f"与本轮患者主题直接相关论文 {evidence_profile['relevant_paper_count']} 篇")
        return min(10, score), reasons

    def rank(
        self,
        patient_profile: dict,
        doctors: list[dict],
        top_n: int = 5,
        pubmed_mode: str = "auto",
    ) -> dict:
        route_result = self.router.route(patient_profile, top_n=3)
        ranked = []
        for doctor in doctors:
            evidence_profile = self.evidence_profiler.profile(
                doctor,
                patient_profile=patient_profile,
                pubmed_mode=pubmed_mode,
            )
            department_score, department_reasons = self._score_department(doctor, route_result)
            topic_score, topic_reasons = self._score_topic_match(doctor, patient_profile, evidence_profile)
            location_score, location_reasons = self._score_location(doctor, patient_profile)
            continuity_score, continuity_reasons = self._score_continuity(doctor, patient_profile)
            evidence_score, evidence_reasons = self._score_evidence(evidence_profile)
            total_score = department_score + topic_score + location_score + continuity_score + evidence_score
            concerns = []
            if not doctor.get("official_profile_url") and not doctor.get("profile_text"):
                concerns.append("缺少完整官方简介，匹配解释会更保守。")
            if evidence_profile.get("notes"):
                concerns.extend(evidence_profile["notes"])
            if not doctor.get("schedule") and not doctor.get("clinic_schedule"):
                concerns.append("公开出诊时间不明确，预约现实性需二次核实。")

            ranked.append(
                {
                    "doctor": doctor,
                    "score": total_score,
                    "score_breakdown": {
                        "department": department_score,
                        "topic": topic_score,
                        "location": location_score,
                        "continuity": continuity_score,
                        "evidence": evidence_score,
                    },
                    "reasons": _uniq(
                        department_reasons + topic_reasons + location_reasons + continuity_reasons + evidence_reasons
                    ),
                    "concerns": _uniq(concerns),
                    "evidence_profile": evidence_profile,
                }
            )

        ranked.sort(
            key=lambda item: (
                -item["score"],
                -(item["score_breakdown"]["department"] + item["score_breakdown"]["topic"]),
                str(item["doctor"].get("hospital", "")),
            )
        )

        return {
            "route_result": route_result,
            "ranked_doctors": ranked[:top_n],
            "all_ranked_doctors": ranked,
        }


def load_json_file(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
