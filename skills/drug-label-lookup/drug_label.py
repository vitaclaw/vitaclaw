"""
Drug Label Lookup Skill

通过 openFDA API 查询药品说明书（适应症、剂量、警告、禁忌症、不良反应、药物相互作用）
API 文档: https://open.fda.gov/apis/drug/label/
"""
import logging
import os
import sys
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class FDAClient:
    """openFDA API 客户端"""

    BASE_URL = "https://api.fda.gov/drug/label.json"

    def __init__(self, api_key: str = None):
        """
        初始化 FDA 客户端

        Args:
            api_key: openFDA API Key (可选，提高请求限额)
        """
        self.api_key = api_key
        self.session = requests.Session()
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

    def search_drug_label(self, drug_name: str) -> Optional[Dict]:
        """
        搜索药物说明书

        Args:
            drug_name: 药物名称 (通用名或商品名)

        Returns:
            说明书内容字典，未找到则返回 None
        """
        search_query = f'openfda.generic_name:"{drug_name}" OR openfda.brand_name:"{drug_name}"'

        params = {
            "search": search_query,
            "limit": 1
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            logger.debug(f"[FDA] 搜索药物: {drug_name}")
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                logger.info(f"[FDA] 未找到药物: {drug_name}")
                return None

            return self._parse_label(results[0])

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.info(f"[FDA] 未找到药物: {drug_name}")
            else:
                logger.error(f"[FDA] 请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"[FDA] 搜索失败: {e}")
            return None

    def _parse_label(self, label: Dict) -> Dict:
        """解析药物说明书"""
        openfda = label.get("openfda", {})

        generic_names = openfda.get("generic_name", [])
        brand_names = openfda.get("brand_name", [])

        def get_section(key: str) -> str:
            content = label.get(key, [])
            if isinstance(content, list) and content:
                return content[0]
            return ""

        return {
            "generic_name": generic_names[0] if generic_names else "",
            "brand_name": brand_names[0] if brand_names else "",
            "manufacturer": openfda.get("manufacturer_name", [""])[0],
            "set_id": openfda.get("spl_set_id", [""])[0],
            "application_number": openfda.get("application_number", [""])[0],
            "indications": get_section("indications_and_usage"),
            "dosage": get_section("dosage_and_administration"),
            "warnings": get_section("warnings_and_cautions") or get_section("warnings"),
            "boxed_warning": get_section("boxed_warning"),
            "contraindications": get_section("contraindications"),
            "adverse_reactions": get_section("adverse_reactions"),
            "drug_interactions": get_section("drug_interactions"),
            "use_in_pregnancy": get_section("pregnancy") or get_section("use_in_specific_populations"),
            "pharmacology": get_section("clinical_pharmacology"),
        }

    def get_indications(self, drug_name: str) -> str:
        """获取适应症"""
        label = self.search_drug_label(drug_name)
        return label.get("indications", "") if label else ""

    def get_warnings(self, drug_name: str) -> str:
        """获取警告信息"""
        label = self.search_drug_label(drug_name)
        if not label:
            return ""

        warnings = []
        if label.get("boxed_warning"):
            warnings.append(f"[黑框警告] {label['boxed_warning']}")
        if label.get("warnings"):
            warnings.append(label["warnings"])

        return "\n\n".join(warnings)

    def get_dosage(self, drug_name: str) -> str:
        """获取剂量信息"""
        label = self.search_drug_label(drug_name)
        return label.get("dosage", "") if label else ""

    def get_interactions(self, drug_name: str) -> str:
        """获取药物相互作用"""
        label = self.search_drug_label(drug_name)
        return label.get("drug_interactions", "") if label else ""


class DrugLabelLookup:
    """药品说明书查询封装类"""

    def __init__(self, api_key: str = None):
        """
        初始化查询工具

        Args:
            api_key: openFDA API Key (可选)，默认从环境变量 OPENFDA_API_KEY 读取
        """
        self.api_key = api_key or os.environ.get("OPENFDA_API_KEY")
        self.client = FDAClient(api_key=self.api_key)

    def lookup(self, drug_name: str) -> Optional[Dict]:
        """
        查询药品说明书

        Args:
            drug_name: 药物名称 (通用名或商品名，英文)

        Returns:
            说明书内容字典，未找到则返回 None
        """
        return self.client.search_drug_label(drug_name)


def format_label(drug_name: str, label: Dict) -> str:
    """
    将说明书字典格式化为 Markdown 可读文本

    Args:
        drug_name: 药物名称
        label: search_drug_label 返回的字典

    Returns:
        Markdown 格式的说明书文本
    """
    generic_name = label.get("generic_name", drug_name)
    brand_name = label.get("brand_name", "")
    manufacturer = label.get("manufacturer", "")

    output = [
        "**FDA 药品说明书**\n",
        f"**药物**: {generic_name}",
    ]

    if brand_name:
        output.append(f"**商品名**: {brand_name}")
    if manufacturer:
        output.append(f"**生产商**: {manufacturer}")

    output.append("")

    # 适应症
    indications = label.get("indications", "")
    if indications:
        output.append("### 适应症")
        output.append(indications)
        output.append("")

    # 剂量
    dosage = label.get("dosage", "")
    if dosage:
        output.append("### 剂量与用法")
        output.append(dosage)
        output.append("")

    # 黑框警告
    boxed = label.get("boxed_warning", "")
    if boxed:
        output.append("### ⚠️ 黑框警告")
        output.append(boxed)
        output.append("")

    # 警告
    warnings = label.get("warnings", "")
    if warnings:
        output.append("### 警告与注意事项")
        output.append(warnings)
        output.append("")

    # 禁忌症
    contraindications = label.get("contraindications", "")
    if contraindications:
        output.append("### 禁忌症")
        output.append(contraindications)
        output.append("")

    # 药物相互作用
    interactions = label.get("drug_interactions", "")
    if interactions:
        output.append("### 药物相互作用")
        output.append(interactions)
        output.append("")

    # 不良反应
    adverse = label.get("adverse_reactions", "")
    if adverse:
        output.append("### 不良反应")
        output.append(adverse)

    set_id = label.get("set_id", "")
    if set_id:
        fda_url = f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}"
    else:
        fda_url = f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query={generic_name}"
    output.append(f"\n**参考**: [FDA: {generic_name}]({fda_url})")

    return "\n".join(output)


def no_results_response(drug_name: str) -> str:
    """
    未找到药物时的响应文本

    Args:
        drug_name: 药物名称

    Returns:
        提示文本
    """
    return f"""**FDA 药品说明书**

**药物**: {drug_name}

未找到该药物的 FDA 说明书。

可能原因:
1. 药物名称拼写错误
2. 该药物未在美国 FDA 批准
3. 尝试使用通用名或商品名搜索

建议:
- 访问 https://labels.fda.gov 直接搜索
- 使用英文药物名称
"""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    drug_name = sys.argv[1] if len(sys.argv) > 1 else "osimertinib"

    tool = DrugLabelLookup()
    label = tool.lookup(drug_name)

    if label:
        print(format_label(drug_name, label))
    else:
        print(no_results_response(drug_name))
