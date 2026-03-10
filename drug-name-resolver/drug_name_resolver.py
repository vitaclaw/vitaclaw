"""
Drug Name Resolver

将药品名称（通用名/商品名/开发代号）标准化为 RxNorm RxCUI，并获取药物分类信息。
API 文档: https://lhncbc.nlm.nih.gov/RxNav/APIs/
"""
import sys
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DrugNameResolver:
    """RxNorm 药品名称解析器"""

    BASE_URL = "https://rxnav.nlm.nih.gov/REST"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json"
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

    def get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        获取药物的 RxCUI (RxNorm Concept Unique Identifier)

        Args:
            drug_name: 药物名称

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

            # 尝试近似搜索
            return self._approximate_search(drug_name)

        except Exception as e:
            logger.error(f"[RxNorm] 获取 RxCUI 失败: {e}")
            return None

    def _approximate_search(self, drug_name: str) -> Optional[str]:
        """近似搜索药物"""
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

    def get_drug_info(self, drug_name: str) -> Optional[Dict]:
        """
        获取药物基本信息

        Args:
            drug_name: 药物名称

        Returns:
            药物信息 {rxcui, name, properties, drug_class}
        """
        rxcui = self.get_rxcui(drug_name)
        if not rxcui:
            logger.info(f"[RxNorm] 未找到药物: {drug_name}")
            return None

        # 获取属性
        url = f"{self.BASE_URL}/rxcui/{rxcui}/allProperties.json"
        params = {"prop": "names"}

        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            props = data.get("propConceptGroup", {}).get("propConcept", [])

            result = {
                "rxcui": rxcui,
                "name": drug_name,
                "properties": {}
            }

            for prop in props:
                prop_name = prop.get("propName", "")
                prop_value = prop.get("propValue", "")
                result["properties"][prop_name] = prop_value

            # 获取药物分类
            result["drug_class"] = self.get_drug_class(rxcui)

            return result

        except Exception as e:
            logger.error(f"[RxNorm] 获取药物信息失败: {e}")
            return None

    def get_drug_class(self, rxcui: str) -> List[str]:
        """
        获取药物分类

        Args:
            rxcui: 药物 RxCUI

        Returns:
            药物分类列表
        """
        url = f"{self.BASE_URL}/rxcui/{rxcui}/class.json"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            classes = []
            concept_groups = data.get("rxclassDrugInfoList", {}).get("rxclassDrugInfo", [])

            for group in concept_groups:
                class_name = group.get("rxclassMinConceptItem", {}).get("className", "")
                if class_name and class_name not in classes:
                    classes.append(class_name)

            return classes[:50]

        except Exception as e:
            logger.debug(f"[RxNorm] 获取药物分类失败: {e}")
            return []

    def resolve(self, drug_name: str) -> dict:
        """
        便捷方法：将药品名称解析为标准化信息

        Args:
            drug_name: 药品名称（通用名/商品名/开发代号）

        Returns:
            包含 rxcui, name, properties, drug_class 的字典；
            若未找到，返回 {name, error} 字典
        """
        result = self.get_drug_info(drug_name)
        if result:
            return result
        return {
            "name": drug_name,
            "error": f"未找到药物: {drug_name}"
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")

    drug_name = sys.argv[1] if len(sys.argv) > 1 else "osimertinib"

    resolver = DrugNameResolver()

    print(f"=== Drug Name Resolver: {drug_name} ===")
    result = resolver.resolve(drug_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))
