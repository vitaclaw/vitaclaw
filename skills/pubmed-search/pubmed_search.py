"""
Smart PubMed Search - 3-Layer LLM Progressive Architecture

Standalone skill extracted from MTB project. No MTB dependencies.

Architecture:
    User Query
        -> [Layer 1 LLM] High-precision tiab-only query -> API search
        -> [Layer 2 LLM] Expanded MeSH+tiab+synonyms (receives Layer 1 failure) -> API search
        -> [Layer 3 LLM] Minimal disease+gene only (receives Layer 1+2 failures) -> API search
        -> [Regex Fallback] Best single concept -> API search
        -> [XML Bucketing] PubMed PublicationType -> 6 evidence buckets
        -> [LLM Batch Scoring] Parallel 20/batch relevance+quality scoring
        -> [LLM Secondary Bucketing] Unclassified articles study_type completion
        -> [Stratified Sampling] By evidence bucket quota + empty bucket reallocation -> Final results
"""
import json
import os
import re
import sys
import time
import logging
import xml.etree.ElementTree as ET
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# ==================== Configuration (from environment) ====================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
)
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemini-3-flash-preview")
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "65536"))
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "")

# Search defaults
DEFAULT_YEAR_WINDOW = 10
PUBMED_BROAD_SEARCH_COUNT = 200
PUBMED_BUCKET_QUOTAS = {
    "guideline": 3,
    "rct": 6,
    "systematic_review": 4,
    "observational": 4,
    "case_report": 2,
    "preclinical": 1,
}

# Bucket labels (Chinese)
BUCKET_LABELS = {
    "guideline": "指南",
    "rct": "RCT",
    "systematic_review": "系统综述",
    "observational": "观察性",
    "case_report": "病例报告",
    "preclinical": "临床前",
}


# ==================== NCBI PubMed Client ====================


class NCBIPubMedClient:
    """NCBI E-utilities PubMed client (standalone, no ClinVar)."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: str = None, email: str = None):
        self.api_key = api_key or NCBI_API_KEY
        self.email = email or NCBI_EMAIL
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "SmartPubMedSearch/1.0"}
        )
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
        self._last_request_time = 0
        self._min_interval = 0.34 if not self.api_key else 0.1

    def _rate_limit(self):
        """NCBI rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _build_params(self, params: Dict) -> Dict:
        """Add API key and email to params."""
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email
        return params

    def search_pubmed(
        self, query: str, max_results: int = 20, year_window: int = None
    ) -> List[Dict]:
        """
        Search PubMed and return article details.

        Args:
            query: Search query (supports Boolean operators)
            max_results: Maximum results
            year_window: Search time window in years

        Returns:
            List of article dicts
        """
        self._rate_limit()

        search_url = f"{self.BASE_URL}/esearch.fcgi"
        params = self._build_params(
            {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            }
        )

        if year_window and year_window > 0:
            import datetime

            current_year = datetime.datetime.now().year
            params["datetype"] = "pdat"
            params["mindate"] = str(current_year - year_window)
            params["maxdate"] = str(current_year)

        try:
            logger.debug(f"[PubMed] Search: {query}")
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            pmids = data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                logger.info(f"[PubMed] No results: {query}")
                return []

            logger.debug(f"[PubMed] Found {len(pmids)} articles")
            return self.fetch_abstracts(pmids)

        except Exception as e:
            logger.error(f"[PubMed] Search failed: {e}")
            return []

    def fetch_abstracts(self, pmids: List[str]) -> List[Dict]:
        """Fetch article details by PMIDs."""
        if not pmids:
            return []

        self._rate_limit()

        fetch_url = f"{self.BASE_URL}/efetch.fcgi"
        params = self._build_params(
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "rettype": "xml",
                "retmode": "xml",
            }
        )

        try:
            response = self.session.get(fetch_url, params=params, timeout=60)
            response.raise_for_status()
            return self._parse_pubmed_xml(response.text)
        except Exception as e:
            logger.error(f"[PubMed] Fetch abstracts failed: {e}")
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict]:
        """Parse PubMed XML response."""
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

                # Title — handle inline tags
                title_elem = article_elem.find("ArticleTitle")
                title = (
                    "".join(title_elem.itertext())
                    if title_elem is not None
                    else ""
                )

                # Authors
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

                # Journal
                journal_elem = article_elem.find(".//Journal/Title")
                journal = (
                    journal_elem.text if journal_elem is not None else ""
                )

                # Year
                year_elem = article_elem.find(".//PubDate/Year")
                year = year_elem.text if year_elem is not None else ""

                # Abstract — handle structured abstracts
                abstract_sections = article_elem.findall(
                    ".//Abstract/AbstractText"
                )
                abstract = ""
                if abstract_sections:
                    parts = []
                    for section in abstract_sections:
                        section_text = "".join(section.itertext()).strip()
                        if not section_text:
                            continue
                        label = section.get("Label")
                        if label:
                            parts.append(f"{label}: {section_text}")
                        else:
                            parts.append(section_text)
                    abstract = " ".join(parts)

                # Publication types
                publication_types = []
                pub_type_list = article_elem.find("PublicationTypeList")
                if pub_type_list is not None:
                    for pt in pub_type_list.findall("PublicationType"):
                        if pt.text:
                            publication_types.append(pt.text)

                results.append(
                    {
                        "pmid": pmid,
                        "title": title,
                        "authors": authors,
                        "journal": journal,
                        "year": year,
                        "abstract": abstract,
                        "publication_types": publication_types,
                    }
                )

        except ET.ParseError as e:
            logger.error(f"[PubMed] XML parse error: {e}")

        return results


# ==================== Smart PubMed Search ====================


class SmartPubMedSearch:
    """
    Smart PubMed Search with 3-Layer LLM Progressive Architecture.

    Layer 1: High-precision [tiab]-only query
    Layer 2: Expanded recall with MeSH+TIAB dual insurance + synonym expansion
    Layer 3: Minimal fallback with only disease + gene/variant
    Fallback: Regex-based best single concept (no LLM)
    Post-filter: LLM batch relevance scoring + study type classification
    Sampling: Stratified sampling by evidence bucket quotas
    """

    # Evidence buckets (priority order, lower index = higher priority)
    MTB_EVIDENCE_BUCKETS = [
        "guideline",
        "rct",
        "systematic_review",
        "observational",
        "case_report",
        "preclinical",
    ]

    # PubMed PublicationType -> bucket mapping
    PUBTYPE_TO_BUCKET = {
        # Guidelines
        "Practice Guideline": "guideline",
        "Guideline": "guideline",
        "Consensus Development Conference": "guideline",
        "Consensus Development Conference, NIH": "guideline",
        # RCT / Clinical trials
        "Randomized Controlled Trial": "rct",
        "Clinical Trial": "rct",
        "Clinical Trial, Phase I": "rct",
        "Clinical Trial, Phase II": "rct",
        "Clinical Trial, Phase III": "rct",
        "Clinical Trial, Phase IV": "rct",
        "Controlled Clinical Trial": "rct",
        "Pragmatic Clinical Trial": "rct",
        # Systematic reviews / Meta-analyses / Reviews
        "Systematic Review": "systematic_review",
        "Meta-Analysis": "systematic_review",
        "Review": "systematic_review",
        # Observational
        "Observational Study": "observational",
        "Multicenter Study": "observational",
        "Comparative Study": "observational",
        # Case reports
        "Case Reports": "case_report",
    }

    # Preclinical heuristic keywords
    PRECLINICAL_MARKERS = [
        "in vitro",
        "cell line",
        "xenograft",
        "mouse model",
        "animal model",
        "preclinical",
        "cell culture",
    ]

    LAYER1_PROMPT = """You are a PubMed Search Specialist.

Task: Convert the clinical query into a HIGH-PRECISION PubMed Boolean search string.

Strategy:
1. Extract key concepts: Disease, Gene/Variant, Drug, Mechanism/Outcome
2. Use ONLY [tiab] field tag (title/abstract search) — do NOT use [MeSH]
3. Within each concept, use OR to connect synonyms (wrap each synonym in quotes)
4. Between different concepts, use AND
5. Remove: numeric values (2+, CPS 3, ECOG 1, 79 mut/Mb), staging info, non-English characters
6. Expand common acronyms: CRC → "colorectal cancer", NSCLC → "non-small cell lung cancer", mCRC → "metastatic colorectal cancer"
7. Keep gene names (KRAS, EGFR), variant names (G12C, L858R), and drug names (cetuximab, osimertinib)
8. Combine gene+variant as a single phrase when possible: "KRAS G12C"[tiab]
9. IMPORTANT: Use AT MOST 4 AND groups. Prioritize concepts in this order:
   (1) Disease/cancer type — ALWAYS include
   (2) Gene/variant — ALWAYS include if present
   (3) Drug name — include if it is the primary focus of the query
   (4) Mechanism/outcome (resistance, efficacy, prognosis) — include only if ≤3 AND groups so far
   DROP these from AND groups: geographic terms (China, Japan, etc.), staging info, secondary modifiers,
   general terms like "inhibitor" when specific drug names already exist, biomarker subtypes (MSS, TMB-H)
10. When multiple related concepts exist (e.g., SHP2 + SOS1 + inhibitor), merge them into ONE OR group rather than separate AND groups

Example:
  Input: KRAS G12C colorectal cancer resistance SHP2 SOS1 inhibitor China
  Output: ("colorectal cancer"[tiab] OR "colorectal neoplasm"[tiab]) AND ("KRAS G12C"[tiab]) AND ("SHP2"[tiab] OR "SOS1"[tiab] OR "resistance"[tiab])

Output ONLY the raw PubMed query string. No explanation, no markdown.

User Query: {query}

PubMed Query:"""

    LAYER2_PROMPT = """You are a PubMed Search Specialist.

Task: The previous search query returned ZERO results on PubMed. Build a BROADER query with higher recall.

Previous failed query (returned 0 results):
{failed_queries}

Strategy — use MeSH + TIAB dual insurance, AND reduce AND groups:
1. For each concept, use BOTH MeSH and free text: ("MeSH Term"[MeSH] OR "free text"[tiab])
2. Expand drug synonyms: generic name + brand name + development code
   e.g., (osimertinib[tiab] OR Tagrisso[tiab] OR AZD9291[tiab])
3. Expand variant notations: L858R OR "exon 21" OR "p.L858R"
4. Expand disease terms with MeSH: ("Colorectal Neoplasms"[MeSH] OR "colorectal cancer"[tiab])
5. Be more inclusive within each concept group (more OR synonyms)
6. CRITICAL: You MUST use FEWER AND groups than the failed query. Maximum 3 AND groups total.
   - Analyze the failed query: identify which AND group likely caused zero results
   - DROP geographic terms (China, Japan, etc.), mechanism modifiers, biomarker subtypes (MSS, TMB-H), general terms
   - Keep only: Disease + Gene/Drug (primary) + one optional modifier
   - Merge related concepts into OR groups instead of separate AND groups
7. If the query involves a rare/new drug name, drop the combination partner drug and keep only the rare drug + disease

Example:
  Input: KRAS G12C colorectal cancer inhibitor resistance China
  Failed: ... AND ("China"[tiab]) — too restrictive
  Output: ("Colorectal Neoplasms"[MeSH] OR "colorectal cancer"[tiab] OR "CRC"[tiab]) AND ("KRAS"[tiab] OR "KRAS G12C"[tiab]) AND ("drug resistance"[MeSH] OR "resistance"[tiab] OR "inhibitor"[tiab])

Output ONLY the raw PubMed query string. No explanation, no markdown.

Original User Query: {query}

Broader PubMed Query:"""

    LAYER3_PROMPT = """You are a PubMed Search Specialist.

Task: ALL previous queries returned ZERO results. Build a MINIMAL fallback query using only the 2 most essential concepts.

Previous failed queries (all returned 0 results):
{failed_queries}

Strategy:
1. Identify the 2 MOST IMPORTANT concepts from the original query (usually: disease + gene/variant)
2. DROP all drug names, interventions, mechanisms, and modifiers
3. Use simple [tiab] search only — do NOT use [MeSH]
4. Each concept can have 2-3 synonyms connected by OR
5. Connect the 2 concepts with a single AND

Example:
  Input: KRAS G12C colorectal cancer cetuximab resistance SHP2 inhibitor
  Output: ("colorectal cancer"[tiab] OR "CRC"[tiab]) AND ("KRAS G12C"[tiab] OR "KRAS"[tiab])

Output ONLY the raw PubMed query string. No explanation, no markdown.

Original User Query: {query}

Minimal PubMed Query:"""

    BATCH_RELEVANCE_FILTER_PROMPT = """You are a Clinical Literature Reviewer for a Molecular Tumor Board.

Task: Evaluate EACH abstract for relevance, evidence quality, and study type.

User's Original Query: {original_query}

Articles to evaluate (JSON array with title, abstract, and PubMed publication types):
{articles_json}

For EACH article, evaluate:
1. Relevance: Does it discuss the specific disease, gene/biomarker, treatment, or clinical outcomes?
2. Evidence quality: Consider study design strength (Phase III RCT > Phase II > Phase I > prospective cohort > retrospective > case series > preclinical), sample size, and whether it reports primary endpoints.
3. Study type classification: Classify into ONE of the following categories based on the study methodology described in the abstract.

IMPORTANT: Use the "publication_types" field as a strong signal for study_type classification.
If publication_types contains "Review", classify as "systematic_review" (not "preclinical").
If publication_types contains "Randomized Controlled Trial", classify as "rct".

study_type categories:
- "guideline": Clinical practice guidelines, consensus statements, expert panel recommendations
- "rct": Randomized controlled trials, clinical trials (any phase), interventional studies
- "systematic_review": Systematic reviews, meta-analyses, pooled analyses, narrative reviews, literature reviews
- "observational": Cohort studies, cross-sectional studies, retrospective analyses, real-world data, registry studies
- "case_report": Case reports, case series (typically < 10 patients)
- "preclinical": In vitro studies, cell line experiments, animal models, xenograft studies.
  A review article that DISCUSSES preclinical data is NOT preclinical — classify it as "systematic_review".
  Only classify as "preclinical" if the article reports ORIGINAL preclinical experimental results.

Return ONLY a valid JSON array (no markdown, no explanation):
[{{"pmid": "...", "is_relevant": true/false, "relevance_score": 0-10, "study_type": "rct|systematic_review|observational|case_report|preclinical|guideline", "matched_criteria": ["..."], "key_findings": "..."}}]

Scoring guideline for relevance_score:
- 9-10: Directly relevant + high-quality evidence (large RCT, guideline, pivotal study)
- 7-8: Directly relevant + moderate evidence (Phase I/II, prospective cohort)
- 5-6: Partially relevant or lower evidence quality (retrospective, case series)
- 1-4: Tangentially relevant or preclinical only
- 0: Not relevant

IMPORTANT: Return evaluation for ALL articles in the input, maintaining the same order."""

    def __init__(self, ncbi_client: NCBIPubMedClient = None):
        self.ncbi_client = ncbi_client or NCBIPubMedClient()
        self.model = LLM_MODEL

    def _call_llm(self, prompt: str, max_tokens: int = None) -> str:
        """Call LLM via OpenRouter API."""
        if max_tokens is None:
            max_tokens = LLM_MAX_TOKENS

        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required for LLM calls"
            )

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": max_tokens,
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    OPENROUTER_BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                response.raise_for_status()
                result = response.json()

                if "choices" not in result:
                    raise ValueError(
                        f"API error: {result.get('error', result)}"
                    )

                finish_reason = result["choices"][0].get(
                    "finish_reason", "unknown"
                )
                if finish_reason == "length":
                    logger.warning(
                        f"[SmartPubMed] LLM response truncated (finish_reason=length, max_tokens={max_tokens})"
                    )
                content = result["choices"][0]["message"]["content"].strip()
                # Clean potential markdown code blocks
                if content.startswith("```"):
                    content = re.sub(r"^```\w*\n?", "", content)
                    content = re.sub(r"\n?```$", "", content)
                return content

            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
            ) as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"[SmartPubMed] LLM request failed ({type(e).__name__}), retrying ({attempt + 1}/{max_retries - 1})..."
                    )
                else:
                    logger.error(
                        f"[SmartPubMed] LLM request failed, retries exhausted: {e}"
                    )
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"[SmartPubMed] LLM call failed, retrying ({attempt + 1}/{max_retries - 1}): {e}"
                    )
                else:
                    logger.error(
                        f"[SmartPubMed] LLM call failed, retries exhausted: {e}"
                    )
                    raise

    def _build_layer_query(
        self, layer: int, query: str, failed_queries: List[str]
    ) -> str:
        """Use LLM to build a PubMed query at a specific layer."""
        prompts = {
            1: self.LAYER1_PROMPT,
            2: self.LAYER2_PROMPT,
            3: self.LAYER3_PROMPT,
        }

        prompt_template = prompts.get(layer, self.LAYER1_PROMPT)
        failed_str = (
            "\n".join(f"  - {q}" for q in failed_queries)
            if failed_queries
            else "(none)"
        )

        prompt = prompt_template.format(query=query, failed_queries=failed_str)
        result = self._call_llm(prompt)

        if not result:
            result = self._fallback_query_cleanup(query)

        logger.info(
            f"[SmartPubMed] Layer {layer} query: '{query[:40]}...' -> '{result[:80]}...'"
        )
        return result

    def _fallback_query_cleanup(self, query: str) -> str:
        """Fallback simple query cleanup."""
        cleaned = re.sub(r"[\u4e00-\u9fff]+", "", query)
        cleaned = re.sub(
            r"\b\d+\.?\d*\s*(\+|%|mut/Mb|ng/ml|U/ml)\b",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\b(ECOG|CPS|PS|TPS)\s*\d+\b", "", cleaned, flags=re.IGNORECASE
        )
        cleaned = re.sub(r"\bp\.([A-Z]\d+[A-Z])\b", r"\1", cleaned)
        cleaned = " ".join(cleaned.split())
        return cleaned

    def _extract_best_single_concept(self, query: str) -> str:
        """
        Last-resort regex fallback (no LLM). Extract best single concept.

        Priority: gene+variant > drug name > gene name > disease name
        """
        cleaned = self._fallback_query_cleanup(query)
        tokens = cleaned.split()

        generic_words = {
            "high",
            "low",
            "resistance",
            "resistant",
            "mechanisms",
            "mechanism",
            "response",
            "treatment",
            "therapy",
            "clinical",
            "monitoring",
            "efficacy",
            "safety",
            "analysis",
            "study",
            "review",
            "outcomes",
            "prognosis",
            "diagnosis",
            "sensitivity",
            "inhibitor",
            "inhibitors",
            "mutation",
            "mutations",
            "expression",
            "pathway",
            "signaling",
            "China",
            "patients",
            "cancer",
            "tumor",
            "tumour",
        }

        # 1. Gene+variant
        gene_variant_pattern = re.compile(
            r"\b([A-Z][A-Z0-9]{1,6})\s+([A-Z]\d+[A-Z])\b"
        )
        match = gene_variant_pattern.search(cleaned)
        if match:
            concept = f'"{match.group(1)} {match.group(2)}"'
            logger.info(
                f"[SmartPubMed] Best single concept (gene+variant): {concept}"
            )
            return concept

        # 2. Drug name (-ib, -mab, etc. suffix)
        drug_pattern = re.compile(
            r"\b(\w*(?:inib|tinib|ertinib|umab|izumab|ximab|rasib|clib|lisib|parib))\b",
            re.IGNORECASE,
        )
        drug_match = drug_pattern.search(cleaned)
        if drug_match:
            drug = drug_match.group(1)
            logger.info(
                f"[SmartPubMed] Best single concept (drug): {drug}"
            )
            return drug

        # 3. Gene name (2-6 uppercase letters+digits)
        gene_pattern = re.compile(r"\b([A-Z][A-Z0-9]{1,5})\b")
        for match in gene_pattern.finditer(cleaned):
            candidate = match.group(1)
            if candidate.lower() not in generic_words and len(candidate) >= 2:
                non_gene = {
                    "AND",
                    "OR",
                    "NOT",
                    "MeSH",
                    "TIAB",
                    "CRC",
                    "MSS",
                    "MSI",
                    "TMB",
                    "IHC",
                    "CPS",
                    "TPS",
                    "ECOG",
                }
                if candidate not in non_gene:
                    logger.info(
                        f"[SmartPubMed] Best single concept (gene): {candidate}"
                    )
                    return candidate

        # 4. Disease name (multi-word phrase)
        disease_patterns = [
            r'"?(colorectal cancer|colorectal neoplasm|colon cancer|rectal cancer)"?',
            r'"?(non-small cell lung cancer|NSCLC|lung adenocarcinoma|lung cancer)"?',
            r'"?(breast cancer|pancreatic cancer|gastric cancer|ovarian cancer)"?',
            r'"?(hepatocellular carcinoma|prostate cancer|melanoma|glioblastoma)"?',
        ]
        for dp in disease_patterns:
            dm = re.search(dp, cleaned, re.IGNORECASE)
            if dm:
                disease = dm.group(0).strip('"')
                logger.info(
                    f"[SmartPubMed] Best single concept (disease): {disease}"
                )
                return f'"{disease}"'

        # 5. Fallback: first non-generic token
        for token in tokens:
            if token.lower() not in generic_words and len(token) >= 3:
                logger.info(
                    f"[SmartPubMed] Best single concept (first non-generic): {token}"
                )
                return token

        # Final fallback
        fallback = (
            tokens[0]
            if tokens
            else query.split()[0]
            if query
            else ""
        )
        logger.info(
            f"[SmartPubMed] Best single concept (fallback): {fallback}"
        )
        return fallback

    def _classify_publication_bucket(self, article: Dict) -> Optional[str]:
        """
        Classify article into evidence bucket based on PubMed PublicationType XML metadata.

        Returns:
            Bucket name or None (needs LLM secondary classification)
        """
        pub_types = article.get("publication_types", [])

        best_bucket = None
        best_priority = len(self.MTB_EVIDENCE_BUCKETS)

        for pt in pub_types:
            bucket = self.PUBTYPE_TO_BUCKET.get(pt)
            if bucket:
                priority = self.MTB_EVIDENCE_BUCKETS.index(bucket)
                if priority < best_priority:
                    best_priority = priority
                    best_bucket = bucket

        # Preclinical heuristic
        if best_bucket is None:
            text = (
                (article.get("title") or "")
                + " "
                + (article.get("abstract") or "")
            ).lower()
            if any(marker in text for marker in self.PRECLINICAL_MARKERS):
                best_bucket = "preclinical"

        return best_bucket

    def _filter_batch(
        self, original_query: str, batch: List[Dict], batch_idx: int
    ) -> List[Dict]:
        """
        Evaluate a batch of articles for relevance (single LLM call per batch).

        Args:
            original_query: User's original query
            batch: Article list (max 20)
            batch_idx: Batch index (for logging)

        Returns:
            Relevant articles with scores
        """
        articles_for_eval = []
        pmid_to_article = {}
        for article in batch:
            pmid = article.get("pmid", "")
            abstract = article.get("abstract", "")
            if not abstract:
                continue
            pmid_to_article[pmid] = article
            articles_for_eval.append(
                {
                    "pmid": pmid,
                    "title": article.get("title") or "",
                    "abstract": abstract,
                    "publication_types": article.get("publication_types", []),
                }
            )

        if not articles_for_eval:
            return []

        prompt = self.BATCH_RELEVANCE_FILTER_PROMPT.format(
            original_query=original_query,
            articles_json=json.dumps(articles_for_eval, ensure_ascii=False),
        )

        response = self._call_llm(prompt)

        filtered = []
        try:
            evaluations = json.loads(response)
            if not isinstance(evaluations, list):
                evaluations = [evaluations]

            for eval_result in evaluations:
                pmid = str(eval_result.get("pmid", ""))
                is_relevant = eval_result.get("is_relevant", False)
                score = eval_result.get("relevance_score", 0)

                if pmid in pmid_to_article and is_relevant and score >= 5:
                    article = pmid_to_article[pmid]
                    article["relevance_score"] = score
                    article["matched_criteria"] = eval_result.get(
                        "matched_criteria", []
                    )
                    article["key_findings"] = eval_result.get(
                        "key_findings", ""
                    )
                    llm_study_type = eval_result.get("study_type", "")
                    if llm_study_type in self.MTB_EVIDENCE_BUCKETS:
                        article["llm_study_type"] = llm_study_type
                    filtered.append(article)

            logger.debug(
                f"[SmartPubMed] Batch {batch_idx}: {len(articles_for_eval)} -> {len(filtered)} relevant"
            )

        except json.JSONDecodeError as e:
            logger.warning(
                f"[SmartPubMed] Batch {batch_idx} JSON parse failed, trying partial parse: {e}"
            )
            last_complete = response.rfind("}")
            if last_complete > 0:
                truncated = (
                    response[:last_complete + 1].rstrip(",\n\r\t ") + "]"
                )
                try:
                    evaluations = json.loads(truncated)
                    if not isinstance(evaluations, list):
                        evaluations = [evaluations]
                    for eval_result in evaluations:
                        pmid = str(eval_result.get("pmid", ""))
                        is_relevant = eval_result.get("is_relevant", False)
                        score = eval_result.get("relevance_score", 0)
                        if (
                            pmid in pmid_to_article
                            and is_relevant
                            and score >= 5
                        ):
                            article = pmid_to_article[pmid]
                            article["relevance_score"] = score
                            article["matched_criteria"] = eval_result.get(
                                "matched_criteria", []
                            )
                            article["key_findings"] = eval_result.get(
                                "key_findings", ""
                            )
                            llm_study_type = eval_result.get("study_type", "")
                            if llm_study_type in self.MTB_EVIDENCE_BUCKETS:
                                article["llm_study_type"] = llm_study_type
                            filtered.append(article)
                    logger.info(
                        f"[SmartPubMed] Batch {batch_idx} partial parse succeeded: rescued {len(filtered)} articles"
                    )
                except json.JSONDecodeError:
                    logger.error(
                        f"[SmartPubMed] Batch {batch_idx} partial parse also failed"
                    )
            else:
                logger.error(
                    f"[SmartPubMed] Batch {batch_idx} cannot be partially parsed"
                )

        return filtered

    def _filter_results(
        self, original_query: str, results: List[Dict]
    ) -> List[Dict]:
        """
        LLM-based filtering (parallel + batch strategy).

        Strategy:
        - Split articles into batches of 20
        - Use ThreadPoolExecutor for parallel batch processing
        - Merge results and sort by relevance
        """
        if not results:
            return []

        BATCH_SIZE = 20
        MAX_WORKERS = 2

        batches = [
            results[i : i + BATCH_SIZE]
            for i in range(0, len(results), BATCH_SIZE)
        ]
        logger.info(
            f"[SmartPubMed] Starting filtering: {len(results)} articles in {len(batches)} batches (workers={MAX_WORKERS})"
        )

        filtered = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(
                    self._filter_batch, original_query, batch, idx
                ): idx
                for idx, batch in enumerate(batches)
            }
            for future in as_completed(futures):
                batch_idx = futures[future]
                try:
                    batch_results = future.result()
                    filtered.extend(batch_results)
                except Exception as e:
                    logger.error(
                        f"[SmartPubMed] Batch {batch_idx} execution failed: {e}"
                    )
                    raise

        filtered.sort(
            key=lambda x: x.get("relevance_score", 0), reverse=True
        )
        logger.info(
            f"[SmartPubMed] Filtering complete: {len(results)} -> {len(filtered)} articles"
        )
        return filtered

    def _stratified_sample(
        self, articles: List[Dict], max_results: int
    ) -> List[Dict]:
        """
        Stratified sampling by evidence bucket quotas.

        Strategy:
        1. Sort within each bucket by relevance_score descending
        2. Take articles per PUBMED_BUCKET_QUOTAS
        3. Redistribute empty bucket quotas by priority order
        4. Sort final results by (bucket_priority, -relevance_score)
        """
        # Step 1: Bucket articles
        buckets: Dict[str, List[Dict]] = {
            b: [] for b in self.MTB_EVIDENCE_BUCKETS
        }

        for article in articles:
            bucket = article.get("mtb_bucket")
            if bucket and bucket in buckets:
                buckets[bucket].append(article)
            else:
                article["mtb_bucket"] = "observational"
                buckets["observational"].append(article)

        # Step 2: Sort within each bucket
        for bucket_name in buckets:
            buckets[bucket_name].sort(
                key=lambda x: x.get("relevance_score", 0), reverse=True
            )

        dist = {b: len(arts) for b, arts in buckets.items() if arts}
        logger.info(f"[SmartPubMed] Evidence bucket distribution: {dist}")

        # Step 3: Select by quota
        selected = []
        remaining_by_bucket: Dict[str, List[Dict]] = {}

        for bucket_name in self.MTB_EVIDENCE_BUCKETS:
            quota = PUBMED_BUCKET_QUOTAS.get(bucket_name, 0)
            available = buckets[bucket_name]
            take = min(quota, len(available))
            selected.extend(available[:take])
            remaining_by_bucket[bucket_name] = available[take:]

        # Step 4: Redistribute shortfall
        shortfall = max_results - len(selected)
        if shortfall > 0:
            for bucket_name in self.MTB_EVIDENCE_BUCKETS:
                if shortfall <= 0:
                    break
                surplus = remaining_by_bucket.get(bucket_name, [])
                take = min(shortfall, len(surplus))
                if take > 0:
                    selected.extend(surplus[:take])
                    shortfall -= take

        # Step 5: Sort by (bucket_priority, -relevance_score)
        def sort_key(article):
            bucket = article.get("mtb_bucket", "observational")
            try:
                bucket_priority = self.MTB_EVIDENCE_BUCKETS.index(bucket)
            except ValueError:
                bucket_priority = len(self.MTB_EVIDENCE_BUCKETS)
            relevance = article.get("relevance_score", 0)
            return (bucket_priority, -relevance)

        selected.sort(key=sort_key)

        logger.info(
            f"[SmartPubMed] Stratified sampling: {len(articles)} -> {len(selected[:max_results])} articles"
        )
        return selected[:max_results]

    def search(
        self,
        query: str,
        max_results: int = 20,
        broad_search_count: int = None,
        skip_filtering: bool = False,
        year_window: int = None,
    ) -> Tuple[List[Dict], str]:
        """
        Main smart search pipeline: 3-layer LLM progressive retrieval + regex fallback + stratified sampling.

        Args:
            query: User's original query (natural language)
            max_results: Final result count
            broad_search_count: API broad search count (for post-filtering pool)
            skip_filtering: Skip LLM filtering (for simple queries or no API key)
            year_window: Search time window in years

        Returns:
            (filtered high-relevance articles, actual query string used)
        """
        if broad_search_count is None:
            broad_search_count = PUBMED_BROAD_SEARCH_COUNT
        if year_window is None:
            year_window = DEFAULT_YEAR_WINDOW

        # Auto-skip LLM filtering if no API key
        if not OPENROUTER_API_KEY:
            skip_filtering = True
            logger.warning(
                "[SmartPubMed] No OPENROUTER_API_KEY set, using basic search without LLM"
            )

        logger.info(
            f"[SmartPubMed] Starting search: {query[:80]}... (year_window={year_window})"
        )

        if not OPENROUTER_API_KEY:
            # No LLM: direct search with cleaned query
            cleaned = self._fallback_query_cleanup(query)
            results = self.ncbi_client.search_pubmed(
                cleaned, max_results=broad_search_count, year_window=year_window
            )
            if results:
                return self._finalize_results(
                    query, results, cleaned, max_results, skip_filtering=True
                )
            return [], cleaned

        failed_queries = []

        # Layer 1: High-precision [tiab]-only query
        q1 = self._build_layer_query(1, query, failed_queries)
        results = self.ncbi_client.search_pubmed(
            q1, max_results=broad_search_count, year_window=year_window
        )
        if results:
            logger.info(f"[SmartPubMed] Layer 1 hit {len(results)} articles")
            return self._finalize_results(
                query, results, q1, max_results, skip_filtering
            )
        failed_queries.append(q1)

        # Layer 2: Expanded recall MeSH+TIAB+synonyms
        q2 = self._build_layer_query(2, query, failed_queries)
        results = self.ncbi_client.search_pubmed(
            q2, max_results=broad_search_count, year_window=year_window
        )
        if results:
            logger.info(f"[SmartPubMed] Layer 2 hit {len(results)} articles")
            return self._finalize_results(
                query, results, q2, max_results, skip_filtering
            )
        failed_queries.append(q2)

        # Layer 3: Minimal disease+gene only
        q3 = self._build_layer_query(3, query, failed_queries)
        results = self.ncbi_client.search_pubmed(
            q3, max_results=broad_search_count, year_window=year_window
        )
        if results:
            logger.info(f"[SmartPubMed] Layer 3 hit {len(results)} articles")
            return self._finalize_results(
                query, results, q3, max_results, skip_filtering
            )

        # Fallback: Best single concept (regex only, no LLM)
        best_concept = self._extract_best_single_concept(query)
        logger.warning(
            f"[SmartPubMed] All 3 LLM layers returned no results, regex fallback: {best_concept}"
        )
        results = self.ncbi_client.search_pubmed(
            best_concept,
            max_results=broad_search_count,
            year_window=year_window,
        )
        if results:
            logger.info(
                f"[SmartPubMed] Fallback hit {len(results)} articles"
            )
            return self._finalize_results(
                query, results, best_concept, max_results, skip_filtering
            )

        logger.warning("[SmartPubMed] All query strategies returned no results")
        return [], best_concept

    def _finalize_results(
        self,
        original_query: str,
        results: List[Dict],
        used_query: str,
        max_results: int,
        skip_filtering: bool,
    ) -> Tuple[List[Dict], str]:
        """XML bucketing + LLM filtering + LLM secondary bucketing + stratified sampling."""
        logger.info(
            f"[SmartPubMed] API returned {len(results)} articles"
        )

        # Phase 1: XML metadata bucketing
        for article in results:
            article["mtb_bucket"] = self._classify_publication_bucket(article)
            article["bucket_source"] = (
                "xml" if article["mtb_bucket"] else None
            )

        xml_classified = sum(
            1 for a in results if a["mtb_bucket"] is not None
        )
        logger.info(
            f"[SmartPubMed] XML bucketing: {xml_classified}/{len(results)} classified"
        )

        if skip_filtering:
            for article in results:
                if article["mtb_bucket"] is None:
                    article["mtb_bucket"] = "observational"
                    article["bucket_source"] = "fallback"
            return self._stratified_sample(results, max_results), used_query

        # Phase 2: LLM relevance+quality scoring + study_type classification
        filtered = self._filter_results(original_query, results)

        # Merge bucketing: XML priority, None uses LLM study_type
        for article in filtered:
            if article.get("mtb_bucket") is None:
                llm_type = article.get("llm_study_type")
                if llm_type and llm_type in self.MTB_EVIDENCE_BUCKETS:
                    article["mtb_bucket"] = llm_type
                    article["bucket_source"] = "llm"
                else:
                    article["mtb_bucket"] = "observational"
                    article["bucket_source"] = "fallback"

        llm_classified = sum(
            1 for a in filtered if a.get("bucket_source") == "llm"
        )
        logger.info(
            f"[SmartPubMed] LLM secondary bucketing: {llm_classified} articles completed"
        )

        # Phase 3: Stratified sampling
        return self._stratified_sample(filtered, max_results), used_query


# ==================== Formatting ====================


def format_results(
    query: str, results: List[Dict], optimized_query: str = ""
) -> str:
    """Format search results as markdown (with relevance scores + evidence buckets)."""
    output = [
        "**PubMed 搜索结果**\n",
        f"**搜索关键词**: {query}",
    ]
    if optimized_query and optimized_query != query:
        output.append(f"**优化查询**: {optimized_query}")
    output.append(f"**找到文献**: {len(results)} 篇")

    # Evidence distribution summary
    bucket_counts: Dict[str, int] = {}
    for article in results:
        bucket = article.get("mtb_bucket", "")
        if bucket:
            bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    if bucket_counts:
        dist_str = ", ".join(
            f"{BUCKET_LABELS.get(b, b)}:{c}" for b, c in bucket_counts.items()
        )
        output.append(f"**证据分布**: {dist_str}")

    output.extend(["\n", "---\n"])

    for i, article in enumerate(results, 1):
        pmid = article.get("pmid", "N/A")
        title = article.get("title", "无标题")
        authors = article.get("authors", [])
        journal = article.get("journal", "")
        year = article.get("year", "")
        abstract = article.get("abstract", "")
        relevance_score = article.get("relevance_score")
        matched_criteria = article.get("matched_criteria", [])
        key_findings = article.get("key_findings", "")

        author_str = ", ".join(authors)

        output.append(f"### {i}. {title}\n")
        output.append(f"- **PMID**: {pmid}")
        output.append(f"- **作者**: {author_str}")
        output.append(f"- **期刊**: {journal} ({year})")

        if relevance_score is not None:
            output.append(f"- **相关性评分**: {relevance_score}/10")
        if matched_criteria:
            output.append(f"- **匹配条件**: {', '.join(matched_criteria)}")
        if key_findings:
            output.append(f"- **关键发现**: {key_findings}")

        pub_types = article.get("publication_types", [])
        mtb_bucket = article.get("mtb_bucket", "")
        bucket_source = article.get("bucket_source", "")
        if pub_types:
            output.append(f"- **出版类型**: {', '.join(pub_types)}")
        if mtb_bucket:
            label = BUCKET_LABELS.get(mtb_bucket, mtb_bucket)
            source_tag = f" ({bucket_source})" if bucket_source else ""
            output.append(f"- **证据分类**: {label}{source_tag}")

        if abstract:
            output.append(f"- **摘要**: {abstract}")

        output.append(
            f"- **链接**: https://pubmed.ncbi.nlm.nih.gov/{pmid}/\n"
        )
        output.append("---\n")

    return "\n".join(output)


# ==================== CLI ====================


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    query = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "EGFR L858R osimertinib"
    )

    print(f"=== Smart PubMed Search ===\n")
    print(f"Query: {query}\n")

    searcher = SmartPubMedSearch()
    results, used_query = searcher.search(query, max_results=5)

    if results:
        print(format_results(query, results, optimized_query=used_query))
    else:
        print(f"No results found for: {query}")
        print(f"Query used: {used_query}")
