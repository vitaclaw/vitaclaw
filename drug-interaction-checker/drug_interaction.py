"""
Drug Interaction Checker

检查药物间相互作用（基于 RxNorm API + FDA 说明书补充）

RxNorm API: https://lhncbc.nlm.nih.gov/RxNav/APIs/
openFDA API: https://open.fda.gov/apis/drug/label/
"""
import logging
import os
import sys
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class DrugInteractionChecker:
    """药物相互作用检查器（RxNorm + FDA 说明书回退）"""

    BASE_URL = "https://rxnav.nlm.nih.gov/REST"
    INTERACTION_URL = "https://rxnav.nlm.nih.gov/REST/interaction"
    FDA_URL = "https://api.fda.gov/drug/label.json"

    def __init__(self, fda_api_key: str = None):
        """
        初始化检查器

        Args:
            fda_api_key: openFDA API Key（可选，提高请求限额）
        """
        self.fda_api_key = fda_api_key or os.environ.get("OPENFDA_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

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

    # ------------------------------------------------------------------ #
    #  RxNorm: RxCUI 解析
    # ------------------------------------------------------------------ #

    def _get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        获取药物的 RxCUI（RxNorm Concept Unique Identifier）

        先尝试精确匹配，失败后回退到近似搜索。

        Args:
            drug_name: 药物名称（英文通用名）

        Returns:
            RxCUI 字符串，未找到返回 None
        """
        url = f"{self.BASE_URL}/rxcui.json"
        params = {"name": drug_name}

        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            id_group = data.get("idGroup", {})
            rxnorm_id = id_group.get("rxnormId", [])

            if rxnorm_id:
                return rxnorm_id[0]

            # 精确匹配失败，尝试近似搜索
            return self._approximate_search(drug_name)

        except Exception as e:
            logger.error(f"[RxNorm] 获取 RxCUI 失败: {e}")
            return None

    def _approximate_search(self, drug_name: str) -> Optional[str]:
        """
        近似搜索药物名称

        Args:
            drug_name: 药物名称

        Returns:
            最佳匹配的 RxCUI，未找到返回 None
        """
        url = f"{self.BASE_URL}/approximateTerm.json"
        params = {"term": drug_name, "maxEntries": 1}

        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            candidates = data.get("approximateGroup", {}).get("candidate", [])
            if candidates:
                return candidates[0].get("rxcui")
            return None

        except Exception as e:
            logger.debug(f"[RxNorm] 近似搜索失败: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  RxNorm: 单药相互作用
    # ------------------------------------------------------------------ #

    def get_single_drug_interactions(self, drug_name: str) -> List[Dict]:
        """
        获取单个药物的已知相互作用

        Args:
            drug_name: 药物名称

        Returns:
            相互作用列表 [{"drugs": [...], "description": str, "severity": str}]
        """
        rxcui = self._get_rxcui(drug_name)
        if not rxcui:
            return []

        url = f"{self.INTERACTION_URL}/interaction.json"
        params = {"rxcui": rxcui}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            interactions = []
            groups = data.get("interactionTypeGroup", [])

            for group in groups:
                for itype in group.get("interactionType", []):
                    for pair in itype.get("interactionPair", []):
                        description = pair.get("description", "")
                        severity = pair.get("severity", "N/A")

                        concepts = pair.get("interactionConcept", [])
                        drugs_involved = []
                        for concept in concepts:
                            drug = concept.get("minConceptItem", {}).get("name", "")
                            if drug:
                                drugs_involved.append(drug)

                        interactions.append({
                            "drugs": drugs_involved,
                            "description": description,
                            "severity": severity,
                        })

            return interactions

        except Exception as e:
            logger.error(f"[RxNorm] 查询相互作用失败: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  RxNorm: 多药相互作用
    # ------------------------------------------------------------------ #

    def check_multi_drug_interactions(self, drug_names: List[str]) -> List[Dict]:
        """
        检查多个药物之间的相互作用

        Args:
            drug_names: 药物名称列表（至少 2 个）

        Returns:
            相互作用列表 [{"drugs": [...], "description": str, "severity": str}]
        """
        rxcuis = []
        for name in drug_names:
            rxcui = self._get_rxcui(name)
            if rxcui:
                rxcuis.append(rxcui)

        if len(rxcuis) < 2:
            return []

        url = f"{self.INTERACTION_URL}/list.json"
        params = {"rxcuis": "+".join(rxcuis)}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            interactions = []
            full_results = data.get("fullInteractionTypeGroup", [])

            for group in full_results:
                for itype in group.get("fullInteractionType", []):
                    for pair in itype.get("interactionPair", []):
                        description = pair.get("description", "")
                        severity = pair.get("severity", "N/A")

                        concepts = pair.get("interactionConcept", [])
                        drugs_involved = []
                        for concept in concepts:
                            drug = concept.get("minConceptItem", {}).get("name", "")
                            if drug:
                                drugs_involved.append(drug)

                        interactions.append({
                            "drugs": drugs_involved,
                            "description": description,
                            "severity": severity,
                        })

            return interactions

        except Exception as e:
            logger.error(f"[RxNorm] 检查相互作用失败: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  FDA 说明书回退
    # ------------------------------------------------------------------ #

    def _get_fda_interactions(self, drug_name: str) -> Optional[str]:
        """
        从 openFDA 药品说明书获取 Drug Interactions 章节

        当 RxNorm 中无相互作用数据时作为回退。

        Args:
            drug_name: 药物名称

        Returns:
            Drug Interactions 文本，未找到返回 None
        """
        search_query = (
            f'openfda.generic_name:"{drug_name}" '
            f'OR openfda.brand_name:"{drug_name}"'
        )
        params = {"search": search_query, "limit": 1}

        if self.fda_api_key:
            params["api_key"] = self.fda_api_key

        try:
            response = self.session.get(self.FDA_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            label = results[0]
            interactions = label.get("drug_interactions", [])
            if isinstance(interactions, list) and interactions:
                return interactions[0]
            return None

        except Exception as e:
            logger.debug(f"[FDA] 查询说明书相互作用失败: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  便捷方法: check()
    # ------------------------------------------------------------------ #

    def check(
        self,
        drug_name: str,
        other_drugs: Optional[List[str]] = None,
    ) -> str:
        """
        综合检查药物相互作用（单药 + 多药 + FDA 回退）

        Args:
            drug_name: 主药物名称
            other_drugs: 其他药物名称列表（可选）

        Returns:
            格式化的 Markdown 结果文本
        """
        rxcui = self._get_rxcui(drug_name) or ""

        # 1) 单药相互作用
        interactions = self.get_single_drug_interactions(drug_name)

        # 2) FDA 回退
        fda_interactions = None
        if not interactions:
            fda_interactions = self._get_fda_interactions(drug_name)

        # 3) 多药相互作用
        multi_interactions = []
        if other_drugs:
            all_drugs = [drug_name] + list(other_drugs)
            multi_interactions = self.check_multi_drug_interactions(all_drugs)

        return format_results(
            drug_name=drug_name,
            interactions=interactions,
            multi_interactions=multi_interactions,
            fda_interactions=fda_interactions,
            rxcui=rxcui,
        )


# ---------------------------------------------------------------------- #
#  格式化输出
# ---------------------------------------------------------------------- #


def format_results(
    drug_name: str,
    interactions: List[Dict],
    multi_interactions: List[Dict],
    fda_interactions: Optional[str] = None,
    rxcui: str = "",
) -> str:
    """
    将查询结果格式化为 Markdown 文本

    Args:
        drug_name: 药物名称
        interactions: 单药相互作用列表
        multi_interactions: 多药相互作用列表
        fda_interactions: FDA 说明书相互作用文本（回退）
        rxcui: 药物 RxCUI

    Returns:
        Markdown 格式的结果文本
    """
    output = [
        "**RxNorm 药物查询结果**\n",
        f"**药物**: {drug_name}",
    ]

    if rxcui:
        output.append(f"**RxCUI**: {rxcui}")

    output.append("")

    # 单药相互作用（RxNorm）
    if interactions:
        output.append("### 主要药物相互作用 (RxNorm)\n")
        for i, intr in enumerate(interactions[:50], 1):
            drugs = ", ".join(intr.get("drugs", []))
            description = intr.get("description", "")
            severity = intr.get("severity", "N/A")
            output.append(f"**{i}. {drugs}**")
            output.append(f"- 严重程度: {severity}")
            output.append(f"- 说明: {description}")
            output.append("")
    elif fda_interactions:
        output.append("### 药物相互作用 (FDA 说明书)\n")
        output.append("*注: RxNorm 无数据，以下信息来自 FDA 药品说明书*\n")
        output.append(fda_interactions)
        output.append("")
    else:
        output.append("未找到药物相互作用记录。\n")

    # 多药相互作用
    if multi_interactions:
        output.append("### 多药相互作用检查\n")
        for intr in multi_interactions[:50]:
            drugs = ", ".join(intr.get("drugs", []))
            severity = intr.get("severity", "N/A")
            output.append(f"- **{drugs}**: {severity}")
        output.append("")

    # 参考链接
    if rxcui:
        rxnorm_url = (
            f"https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI"
            f"&searchTerm={rxcui}"
        )
    else:
        rxnorm_url = (
            f"https://mor.nlm.nih.gov/RxNav/search?searchBy=STRING"
            f"&searchTerm={drug_name}"
        )

    output.append(f"**参考**: [RxNorm: {drug_name}]({rxnorm_url})")
    return "\n".join(output)


# ---------------------------------------------------------------------- #
#  CLI 入口
# ---------------------------------------------------------------------- #

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if len(sys.argv) > 1:
        drug_names = sys.argv[1:]
    else:
        drug_names = ["osimertinib", "rifampin", "ketoconazole"]

    checker = DrugInteractionChecker()

    primary = drug_names[0]
    others = drug_names[1:] if len(drug_names) > 1 else None

    print(f"=== 药物相互作用检查: {primary} ===")
    if others:
        print(f"    其他药物: {', '.join(others)}")
    print()

    result = checker.check(primary, other_drugs=others)
    print(result)
