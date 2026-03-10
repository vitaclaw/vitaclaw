"""
ClinicalTrials.gov API v2 临床试验搜索

搜索 ClinicalTrials.gov 临床试验，支持按疾病、干预措施、地区、试验状态等多维度筛选。

API 文档: https://clinicaltrials.gov/data-api/api
"""
import sys
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ClinicalTrialSearch:
    """ClinicalTrials.gov API v2 客户端"""

    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ClinicalTrialSearch/1.0"
        })
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def search(
        self,
        condition: str,
        intervention: Optional[str] = None,
        location: str = "China",
        status: str = "RECRUITING",
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索临床试验

        Args:
            condition: 疾病/条件 (如 "NSCLC", "EGFR mutation lung cancer")
            intervention: 干预措施/药物 (可选)
            location: 地点 (默认中国)，设为 None 或空字符串表示全球搜索
            status: 试验状态 (RECRUITING, NOT_YET_RECRUITING, COMPLETED 等，支持逗号分隔多个)
            max_results: 最大结果数

        Returns:
            试验列表 [{nct_id, brief_title, phase, status, conditions, interventions, locations, ...}]
        """
        params = {
            "format": "json",
            "pageSize": max_results,
            "query.cond": condition,
            "filter.overallStatus": status,
        }

        if intervention:
            params["query.intr"] = intervention

        if location:
            params["query.locn"] = location

        params["fields"] = ",".join([
            "NCTId",
            "BriefTitle",
            "OfficialTitle",
            "Phase",
            "OverallStatus",
            "Condition",
            "InterventionName",
            "InterventionType",
            "LocationFacility",
            "LocationCity",
            "LocationCountry",
            "LeadSponsorName",
            "EnrollmentCount",
            "StartDate",
            "PrimaryCompletionDate",
            "EligibilityCriteria"
        ])

        try:
            logger.debug(
                "[CT.gov] 搜索: %s, 干预: %s, 地点: %s, 状态: %s",
                condition, intervention, location or "全球", status
            )
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            studies = data.get("studies", [])
            if not studies:
                logger.info("[CT.gov] 无匹配试验: %s", condition)
                return []

            logger.debug("[CT.gov] 找到 %d 项试验", len(studies))
            return self._parse_studies(studies, location_filter=location)

        except Exception as e:
            logger.error("[CT.gov] 搜索失败: %s", e)
            return []

    def get_details(self, nct_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个试验的详细信息

        Args:
            nct_id: 试验 NCT 编号 (如 NCT04532463)

        Returns:
            试验详细信息字典，失败时返回 None
        """
        url = f"{self.BASE_URL}/{nct_id}"
        params = {"format": "json"}

        try:
            logger.debug("[CT.gov] 获取试验详情: %s", nct_id)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            studies = self._parse_studies([data], location_filter=None)
            return studies[0] if studies else None

        except Exception as e:
            logger.error("[CT.gov] 获取 %s 失败: %s", nct_id, e)
            return None

    def _parse_studies(
        self, studies: List[Dict], location_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """解析试验数据"""
        results = []

        for study in studies:
            protocol = study.get("protocolSection", {})

            # 基本信息
            id_module = protocol.get("identificationModule", {})
            nct_id = id_module.get("nctId", "")
            brief_title = id_module.get("briefTitle", "")
            official_title = id_module.get("officialTitle", "")

            # 状态
            status_module = protocol.get("statusModule", {})
            overall_status = status_module.get("overallStatus", "")
            start_date = status_module.get("startDateStruct", {}).get("date", "")
            completion_date = status_module.get(
                "primaryCompletionDateStruct", {}
            ).get("date", "")

            # 设计
            design_module = protocol.get("designModule", {})
            phases = design_module.get("phases", [])
            phase = ", ".join(phases) if phases else "N/A"
            enrollment = design_module.get("enrollmentInfo", {}).get("count", 0)

            # 条件
            conditions_module = protocol.get("conditionsModule", {})
            conditions = conditions_module.get("conditions", [])

            # 干预
            interventions = []
            arms_module = protocol.get("armsInterventionsModule", {})
            for intr in arms_module.get("interventions", []):
                interventions.append({
                    "name": intr.get("name", ""),
                    "type": intr.get("type", "")
                })

            # 地点 (按 location_filter 过滤，为空时返回所有)
            locations = []
            locations_module = protocol.get("contactsLocationsModule", {})
            for loc in locations_module.get("locations", []):
                country = loc.get("country", "")
                if location_filter and country.lower() != location_filter.lower():
                    continue
                locations.append({
                    "facility": loc.get("facility", ""),
                    "city": loc.get("city", ""),
                    "country": country
                })

            # 资助方
            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
            lead_sponsor = sponsor_module.get("leadSponsor", {}).get("name", "")

            # 入选标准
            eligibility_module = protocol.get("eligibilityModule", {})
            eligibility_criteria = eligibility_module.get(
                "eligibilityCriteria", ""
            )

            results.append({
                "nct_id": nct_id,
                "brief_title": brief_title,
                "official_title": official_title,
                "phase": phase,
                "status": overall_status,
                "enrollment": enrollment,
                "start_date": start_date,
                "completion_date": completion_date,
                "conditions": conditions,
                "interventions": interventions,
                "locations": locations,
                "sponsor": lead_sponsor,
                "eligibility_criteria": eligibility_criteria,
                "url": f"https://clinicaltrials.gov/study/{nct_id}"
            })

        return results


def format_results(
    results: List[Dict[str, Any]],
    cancer_type: str = "",
    biomarker: str = "",
    intervention: str = "",
    status: str = "RECRUITING",
    location: str = "China"
) -> str:
    """
    将搜索结果格式化为 Markdown 报告

    Args:
        results: search() 返回的试验列表
        cancer_type: 肿瘤类型（用于显示搜索条件）
        biomarker: 生物标志物（用于显示搜索条件）
        intervention: 干预措施（用于显示搜索条件）
        status: 试验状态
        location: 地区

    Returns:
        格式化的 Markdown 字符串
    """
    if not results:
        return _no_results_response(
            cancer_type, biomarker, intervention, status, location
        )

    output = [
        "**ClinicalTrials.gov 搜索结果**\n",
        "**搜索条件**:",
        f"- 肿瘤类型: {cancer_type or 'N/A'}",
        f"- 生物标志物: {biomarker or 'N/A'}",
        f"- 干预措施: {intervention or 'N/A'}",
        f"- 地区: {location if location else '全球'}",
        f"- 状态: {status}\n",
        f"**匹配试验（共{len(results)}项）**:\n",
        "---\n"
    ]

    for i, trial in enumerate(results, 1):
        nct_id = trial.get("nct_id", "N/A")
        title = trial.get("brief_title", "无标题")
        phase = trial.get("phase", "N/A")
        trial_status = trial.get("status", "N/A")
        enrollment = trial.get("enrollment", 0)
        sponsor = trial.get("sponsor", "")
        interventions = trial.get("interventions", [])
        locations = trial.get("locations", [])
        eligibility = trial.get("eligibility_criteria", "")

        output.append(f"### {i}. {nct_id} - {title}\n")
        output.append(f"**Phase**: {phase}")
        output.append(f"**状态**: {trial_status}")
        output.append(f"**入组人数**: {enrollment} patients")
        output.append(f"**资助方**: {sponsor}")

        # 干预措施
        if interventions:
            drug_list = [
                f"{intr.get('name', '')} ({intr.get('type', '')})"
                for intr in interventions
            ]
            output.append(f"**药物**: {', '.join(drug_list)}")

        # 入选标准
        if eligibility:
            output.append(f"\n**关键入组标准**:\n{eligibility}")

        # 试验中心
        if locations:
            if location and location.lower() == "china":
                site_label = "中国中心"
                site_list = [
                    f"{loc.get('facility', '')} ({loc.get('city', '')})"
                    for loc in locations
                ]
            else:
                site_label = "试验中心"
                site_list = [
                    f"{loc.get('facility', '')} ({loc.get('city', '')}, {loc.get('country', '')})"
                    for loc in locations
                ]
            output.append(f"\n**{site_label}**:")
            for site in site_list:
                output.append(f"- {site}")

        output.append(f"\n**参考**: {trial.get('url', '')}")
        output.append("\n---\n")

    output.append(
        "\n**备注**: 以上为实时数据，实际试验入组需联系各中心PI确认资格。"
    )

    return "\n".join(output)


def _no_results_response(
    cancer_type: str = "",
    biomarker: str = "",
    intervention: str = "",
    status: str = "RECRUITING",
    location: str = "China"
) -> str:
    """无结果时的建议响应"""
    suggestions = [
        "1. 尝试放宽搜索条件",
        '2. 使用英文搜索 (如 "NSCLC" 而非 "非小细胞肺癌")'
    ]
    if "COMPLETED" not in status.upper():
        suggestions.append(
            "3. 检查其他试验状态 (如 COMPLETED, NOT_YET_RECRUITING)"
        )
    if location:
        suggestions.append(
            f"{len(suggestions) + 1}. 尝试全球搜索 (设置 location 为 None)"
        )

    return (
        "**ClinicalTrials.gov 搜索结果**\n"
        "\n"
        "**搜索条件**:\n"
        f"- 肿瘤类型: {cancer_type or 'N/A'}\n"
        f"- 生物标志物: {biomarker or 'N/A'}\n"
        f"- 干预措施: {intervention or 'N/A'}\n"
        f"- 地区: {location if location else '全球'}\n"
        f"- 状态: {status}\n"
        "\n"
        "**未找到匹配的临床试验。**\n"
        "\n"
        "建议:\n"
        + "\n".join(suggestions)
        + "\n"
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    condition = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "NSCLC EGFR"

    print(f"=== ClinicalTrials.gov 搜索: {condition} ===\n")

    client = ClinicalTrialSearch()
    results = client.search(
        condition=condition,
        location="China",
        status="RECRUITING",
        max_results=5
    )

    if results:
        print(format_results(
            results,
            cancer_type=condition,
            location="China"
        ))
    else:
        print("未找到匹配的临床试验。")
        print(_no_results_response(cancer_type=condition))
