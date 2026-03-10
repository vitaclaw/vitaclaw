import os
import sys
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class FDAAdverseEventClient:
    """openFDA FAERS (FDA Adverse Event Reporting System) 客户端"""

    BASE_URL = "https://api.fda.gov/drug/event.json"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENFDA_API_KEY", "")
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def search_adverse_events(
        self,
        drug_name: str,
        limit: int = 10,
    ) -> Optional[Dict]:
        """
        Search adverse events for a drug.

        Uses openFDA count endpoint to get top adverse reactions.

        Args:
            drug_name: Drug name (generic or brand)
            limit: Number of top adverse reactions to return

        Returns:
            Dict with drug_name, total_reports, top_reactions list
        """
        # Count top adverse reactions for this drug
        params = {
            "search": f'patient.drug.openfda.generic_name:"{drug_name}" OR patient.drug.openfda.brand_name:"{drug_name}"',
            "count": "patient.reaction.reactionmeddrapt.exact",
            "limit": limit,
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            return {
                "drug_name": drug_name,
                "top_reactions": [
                    {"reaction": r.get("term", ""), "count": r.get("count", 0)}
                    for r in results
                ],
            }
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                logger.info(f"[FAERS] 未找到药物: {drug_name}")
            else:
                logger.error(f"[FAERS] 请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"[FAERS] 搜索失败: {e}")
            return None

    def search_serious_events(
        self,
        drug_name: str,
        limit: int = 10,
    ) -> Optional[Dict]:
        """
        Search serious adverse events only (serious=1).

        Args:
            drug_name: Drug name
            limit: Number of results

        Returns:
            Dict with drug_name, top_serious_reactions list
        """
        params = {
            "search": f'(patient.drug.openfda.generic_name:"{drug_name}" OR patient.drug.openfda.brand_name:"{drug_name}") AND serious:1',
            "count": "patient.reaction.reactionmeddrapt.exact",
            "limit": limit,
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            return {
                "drug_name": drug_name,
                "top_serious_reactions": [
                    {"reaction": r.get("term", ""), "count": r.get("count", 0)}
                    for r in results
                ],
            }
        except Exception as e:
            logger.error(f"[FAERS] 严重事件搜索失败: {e}")
            return None

    def search_outcomes(
        self,
        drug_name: str,
    ) -> Optional[Dict]:
        """
        Get outcome distribution for adverse events of a drug.

        Outcomes: Death, Life Threatening, Hospitalization, Disability,
                  Congenital Anomaly, Required Intervention, Other Serious

        Args:
            drug_name: Drug name

        Returns:
            Dict with outcome distribution
        """
        params = {
            "search": f'patient.drug.openfda.generic_name:"{drug_name}" OR patient.drug.openfda.brand_name:"{drug_name}"',
            "count": "serious",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            # serious: 1=serious, 2=not serious
            outcome = {"drug_name": drug_name, "serious": 0, "non_serious": 0}
            for r in results:
                term = r.get("term", 0)
                count = r.get("count", 0)
                if term == 1:
                    outcome["serious"] = count
                elif term == 2:
                    outcome["non_serious"] = count
            outcome["total"] = outcome["serious"] + outcome["non_serious"]
            if outcome["total"] > 0:
                outcome["serious_pct"] = round(100 * outcome["serious"] / outcome["total"], 1)
            else:
                outcome["serious_pct"] = 0.0

            return outcome
        except Exception as e:
            logger.error(f"[FAERS] 结局分布查询失败: {e}")
            return None

    def get_full_report(
        self,
        drug_name: str,
        top_n: int = 15,
    ) -> Optional[Dict]:
        """
        Get a comprehensive adverse event report combining all queries.

        Args:
            drug_name: Drug name
            top_n: Number of top reactions to include

        Returns:
            Comprehensive report dict
        """
        all_events = self.search_adverse_events(drug_name, limit=top_n)
        serious_events = self.search_serious_events(drug_name, limit=top_n)
        outcomes = self.search_outcomes(drug_name)

        if not all_events and not serious_events and not outcomes:
            return None

        return {
            "drug_name": drug_name,
            "all_adverse_events": all_events,
            "serious_adverse_events": serious_events,
            "outcome_distribution": outcomes,
        }


def format_adverse_events(report: Dict) -> str:
    """Format adverse event report as markdown."""
    drug_name = report.get("drug_name", "Unknown")
    output = [
        f"**FDA 不良反应报告 (FAERS)**\n",
        f"**药物**: {drug_name}\n",
    ]

    # Outcome distribution
    outcomes = report.get("outcome_distribution")
    if outcomes:
        total = outcomes.get("total", 0)
        serious = outcomes.get("serious", 0)
        serious_pct = outcomes.get("serious_pct", 0)
        output.append(f"**总报告数**: {total:,}")
        output.append(f"**严重事件占比**: {serious:,} ({serious_pct}%)\n")

    # All adverse events
    all_events = report.get("all_adverse_events")
    if all_events:
        reactions = all_events.get("top_reactions", [])
        if reactions:
            output.append("### 最常报告的不良反应\n")
            output.append("| 排名 | 不良反应 | 报告数 |")
            output.append("|------|---------|--------|")
            for i, r in enumerate(reactions, 1):
                output.append(f"| {i} | {r['reaction']} | {r['count']:,} |")
            output.append("")

    # Serious events
    serious_events = report.get("serious_adverse_events")
    if serious_events:
        reactions = serious_events.get("top_serious_reactions", [])
        if reactions:
            output.append("### 最常报告的严重不良反应\n")
            output.append("| 排名 | 不良反应 | 报告数 |")
            output.append("|------|---------|--------|")
            for i, r in enumerate(reactions, 1):
                output.append(f"| {i} | {r['reaction']} | {r['count']:,} |")
            output.append("")

    output.append(f"\n**数据来源**: [FDA FAERS](https://www.fda.gov/drugs/questions-and-answers-fdas-adverse-event-reporting-system-faers/fda-adverse-event-reporting-system-faers-public-dashboard)")
    output.append("**注意**: FAERS 为自发报告系统，报告数不等于发生率，不能用于直接比较药物安全性。")

    return "\n".join(output)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    drug = sys.argv[1] if len(sys.argv) > 1 else "osimertinib"

    print(f"=== FDA 不良反应查询: {drug} ===\n")
    client = FDAAdverseEventClient()
    report = client.get_full_report(drug)

    if report:
        print(format_adverse_events(report))
    else:
        print(f"未找到 {drug} 的不良反应数据")
