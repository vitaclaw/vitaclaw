"""
PubMed Abstract Reader

通过 NCBI E-utilities API 批量获取 PubMed 文献摘要、作者、期刊等详细信息。
支持按 PMID 获取和关键词检索两种模式。

API 文档: https://www.ncbi.nlm.nih.gov/books/NBK25500/
"""

import json
import logging
import os
import sys
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class PubMedAbstractReader:
    """PubMed 文献摘要读取器"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: str = None, email: str = None):
        """
        初始化 PubMed 摘要读取器

        Args:
            api_key: NCBI API Key (可选，提高请求限额至 10/秒)
            email: 联系邮箱 (NCBI 建议提供)
        """
        self.api_key = api_key or os.environ.get("NCBI_API_KEY", "")
        self.email = email or os.environ.get("NCBI_EMAIL", "user@example.com")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PubMedAbstractReader/1.0"
        })
        # 重试策略：处理瞬态 SSL/网络错误和服务端限流
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,           # 1s -> 2s -> 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        # 请求间隔 (无 API Key 限制 3/秒)
        self._last_request_time = 0
        self._min_interval = 0.34 if not self.api_key else 0.1

    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _build_params(self, params: Dict) -> Dict:
        """构建请求参数"""
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email
        return params

    def search_pubmed(self, query: str, max_results: int = 20, year_window: int = None) -> List[Dict]:
        """
        搜索 PubMed 文献

        Args:
            query: 搜索关键词 (支持布尔运算符)
            max_results: 最大结果数
            year_window: 搜索时间窗口（年数），如 10 表示最近 10 年

        Returns:
            文献列表 [{pmid, title, authors, journal, year, abstract, publication_types}]
        """
        self._rate_limit()

        # Step 1: esearch 获取 PMID 列表
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        params = self._build_params({
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance"
        })

        # 日期范围过滤
        if year_window and year_window > 0:
            import datetime
            current_year = datetime.datetime.now().year
            params["datetype"] = "pdat"
            params["mindate"] = str(current_year - year_window)
            params["maxdate"] = str(current_year)

        try:
            logger.debug(f"PubMed 搜索: {query}")
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            pmids = data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                logger.info(f"PubMed 无结果: {query}")
                return []

            logger.debug(f"找到 {len(pmids)} 篇文献")

            # Step 2: efetch 获取详细信息
            return self.fetch_abstracts(pmids)

        except Exception as e:
            logger.error(f"PubMed 搜索失败: {e}")
            return []

    def fetch_abstracts(self, pmids: List[str]) -> List[Dict]:
        """
        获取文献详细信息

        Args:
            pmids: PMID 列表

        Returns:
            文献详细信息列表
        """
        if not pmids:
            return []

        self._rate_limit()

        fetch_url = f"{self.BASE_URL}/efetch.fcgi"
        params = self._build_params({
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "xml",
            "retmode": "xml"
        })

        try:
            response = self.session.get(fetch_url, params=params, timeout=60)
            response.raise_for_status()

            return self._parse_pubmed_xml(response.text)

        except Exception as e:
            logger.error(f"获取摘要失败: {e}")
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict]:
        """解析 PubMed XML 响应"""
        results = []
        try:
            root = ET.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                citation = article.find(".//MedlineCitation")
                if citation is None:
                    continue

                pmid_elem = citation.find("PMID")
                pmid = pmid_elem.text if pmid_elem is not None else ""

                article_elem = citation.find("Article")
                if article_elem is None:
                    continue

                # 标题 -- 使用 itertext() 处理内联标签（如 <sup>, <i>）
                title_elem = article_elem.find("ArticleTitle")
                title = ''.join(title_elem.itertext()) if title_elem is not None else ""

                # 作者
                authors = []
                author_list = article_elem.find("AuthorList")
                if author_list is not None:
                    for author in author_list.findall("Author"):
                        last_name = author.find("LastName")
                        initials = author.find("Initials")
                        if last_name is not None:
                            name = last_name.text
                            if initials is not None:
                                name += f" {initials.text}"
                            authors.append(name)

                # 期刊
                journal_elem = article_elem.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else ""

                # 年份
                year_elem = article_elem.find(".//PubDate/Year")
                year = year_elem.text if year_elem is not None else ""

                # 摘要 -- 处理内联标签（如 <sup>, <i>）和结构化摘要（多个 AbstractText）
                abstract_sections = article_elem.findall(".//Abstract/AbstractText")
                abstract = ""
                if abstract_sections:
                    parts = []
                    for section in abstract_sections:
                        section_text = ''.join(section.itertext()).strip()
                        if not section_text:
                            continue
                        label = section.get("Label")
                        if label:
                            parts.append(f"{label}: {section_text}")
                        else:
                            parts.append(section_text)
                    abstract = " ".join(parts)

                # 出版类型
                publication_types = []
                pub_type_list = article_elem.find("PublicationTypeList")
                if pub_type_list is not None:
                    for pt in pub_type_list.findall("PublicationType"):
                        if pt.text:
                            publication_types.append(pt.text)

                results.append({
                    "pmid": pmid,
                    "title": title,
                    "authors": authors,
                    "journal": journal,
                    "year": year,
                    "abstract": abstract,
                    "publication_types": publication_types,
                })

        except ET.ParseError as e:
            logger.error(f"XML 解析失败: {e}")

        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")

    reader = PubMedAbstractReader()

    if len(sys.argv) > 1:
        # 按 PMID 获取（逗号分隔）
        pmids = [p.strip() for p in sys.argv[1].split(",") if p.strip()]
        print(f"正在获取 {len(pmids)} 篇文献: {', '.join(pmids)}\n")
        results = reader.fetch_abstracts(pmids)
    else:
        # 默认检索示例
        query = "EGFR L858R osimertinib"
        print(f"正在搜索: {query}\n")
        results = reader.search_pubmed(query, max_results=5)

    if not results:
        print("未找到结果。")
        sys.exit(0)

    for article in results:
        print(f"PMID:   {article['pmid']}")
        print(f"标题:   {article['title']}")
        print(f"作者:   {', '.join(article['authors'][:5])}" +
              (f" 等共{len(article['authors'])}位" if len(article['authors']) > 5 else ""))
        print(f"期刊:   {article['journal']}")
        print(f"年份:   {article['year']}")
        print(f"类型:   {', '.join(article['publication_types'])}")
        abstract_preview = article['abstract']
        if len(abstract_preview) > 300:
            abstract_preview = abstract_preview[:300] + "..."
        print(f"摘要:   {abstract_preview}")
        print("-" * 80)

    # 同时输出 JSON 到 stderr 供程序化使用
    print(f"\n共 {len(results)} 篇文献。", file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False, indent=2), file=sys.stderr)
