#!/usr/bin/env python3
"""Tests for doctor matching skills and chief-led integration."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from doctor_match_workflow import DoctorMatchWorkflow  # noqa: E402
from doctor_matching import (  # noqa: E402
    DepartmentFitRouter,
    DoctorEvidenceProfiler,
    DoctorFitFinder,
    PubMedClient,
)
from health_team_runtime import HealthTeamOrchestrator  # noqa: E402


PROFILE_HTML = """
<html>
  <head><title>Dr. Ming Li</title></head>
  <body>
    <div class="doctor-profile">
      <h1>李明 / Ming Li</h1>
      <p>Cardiology specialist focusing on hypertension, lipid management, and long-term cardiovascular risk follow-up.</p>
      <p>Chief physician. Runs weekly hypertension clinic and chronic disease continuity clinic.</p>
    </div>
  </body>
</html>
"""


ESEARCH_JSON = {
    "esearchresult": {
        "idlist": ["1001", "1002"]
    }
}


EFETCH_XML = """
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>1001</PMID>
      <Article>
        <ArticleTitle>Hypertension risk management in outpatient cardiology clinics</ArticleTitle>
        <Abstract>
          <AbstractText>This study discusses hypertension follow-up and lipid control in chronic disease clinics.</AbstractText>
        </Abstract>
        <Journal><Title>Journal of Cardiology Practice</Title></Journal>
        <AuthorList>
          <Author><ForeName>Ming</ForeName><LastName>Li</LastName></Author>
        </AuthorList>
      </Article>
      <PubDate><Year>2024</Year></PubDate>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>1002</PMID>
      <Article>
        <ArticleTitle>General internal medicine perspectives on continuity of care</ArticleTitle>
        <Abstract>
          <AbstractText>Continuity of care improves long-term outcomes for chronic disease patients.</AbstractText>
        </Abstract>
        <Journal><Title>Continuity Medicine</Title></Journal>
        <AuthorList>
          <Author><ForeName>Ming</ForeName><LastName>Li</LastName></Author>
        </AuthorList>
      </Article>
      <PubDate><Year>2022</Year></PubDate>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def fake_fetcher(url: str) -> str:
    if "esearch.fcgi" in url:
        return json.dumps(ESEARCH_JSON, ensure_ascii=False)
    if "efetch.fcgi" in url:
        return EFETCH_XML
    if "doctor-li" in url:
        return PROFILE_HTML
    raise AssertionError(f"unexpected URL: {url}")


def fake_fit_finder() -> DoctorFitFinder:
    profiler = DoctorEvidenceProfiler(
        fetcher=fake_fetcher,
        pubmed_client=PubMedClient(fetcher=fake_fetcher, delay_seconds=0),
    )
    return DoctorFitFinder(
        router=DepartmentFitRouter(),
        evidence_profiler=profiler,
    )


PATIENT_PROFILE = {
    "city": "上海",
    "district": "徐汇",
    "conditions": ["高血压", "糖前期"],
    "symptoms": ["晨起头胀"],
    "abnormal_findings": ["ALT 78 U/L", "甘油三酯 2.7 mmol/L"],
    "goals": ["找适合长期管理高血压和代谢风险的门诊"],
    "preferred_hospitals": ["瑞和国际门诊"],
    "continuity_preference": "需要长期随访和沟通清晰的医生",
}


DOCTOR_CANDIDATES = [
    {
        "name": "李明",
        "english_name": "Ming Li",
        "hospital": "瑞和国际门诊",
        "department": "心内科 / 高血压门诊",
        "city": "上海",
        "district": "徐汇",
        "specialties": ["hypertension", "lipid management", "chronic disease follow-up"],
        "official_profile_url": "https://hospital.example/doctor-li",
        "schedule": "Tue pm / Fri am",
        "accepts_long_term_followup": True,
        "pubmed_query": "\"Ming Li\"[Author] AND (hypertension OR lipid)",
    },
    {
        "name": "王琪",
        "english_name": "Qi Wang",
        "hospital": "海城医院",
        "department": "消化内科 / 肝病门诊",
        "city": "上海",
        "district": "浦东",
        "specialties": ["fatty liver", "hepatology"],
        "profile_text": "Focus on fatty liver and liver enzyme abnormalities.",
        "schedule": "Thu am",
        "accepts_long_term_followup": False,
    },
    {
        "name": "赵晨",
        "english_name": "Chen Zhao",
        "hospital": "外地三甲医院",
        "department": "内分泌科",
        "city": "杭州",
        "district": "西湖",
        "specialties": ["diabetes", "prediabetes", "obesity"],
        "profile_text": "Endocrinology physician with interest in diabetes prevention.",
        "schedule": "",
        "accepts_long_term_followup": True,
    },
]


class DoctorMatchingTest(unittest.TestCase):
    def test_department_router_prioritizes_cardiology_and_endocrinology(self):
        result = DepartmentFitRouter().route(PATIENT_PROFILE)
        departments = [item["department"] for item in result["recommendations"]]
        self.assertIn("心内科 / 高血压门诊", departments)
        self.assertIn("内分泌科", departments)

    def test_evidence_profiler_uses_public_profile_and_pubmed(self):
        profiler = DoctorEvidenceProfiler(
            fetcher=fake_fetcher,
            pubmed_client=PubMedClient(fetcher=fake_fetcher, delay_seconds=0),
        )
        result = profiler.profile(
            DOCTOR_CANDIDATES[0],
            patient_profile=PATIENT_PROFILE,
            pubmed_mode="auto",
        )
        self.assertEqual(result["paper_count"], 2)
        self.assertGreaterEqual(result["relevant_paper_count"], 1)
        self.assertIn("https://hospital.example/doctor-li", result["source_refs"])
        self.assertIn("https://pubmed.ncbi.nlm.nih.gov/1001/", result["source_refs"])

    def test_doctor_fit_finder_ranks_city_and_continuity_match_first(self):
        result = fake_fit_finder().rank(
            patient_profile=PATIENT_PROFILE,
            doctors=DOCTOR_CANDIDATES,
            top_n=3,
            pubmed_mode="auto",
        )
        top = result["ranked_doctors"][0]
        self.assertEqual(top["doctor"]["name"], "李明")
        self.assertGreater(top["score"], result["ranked_doctors"][1]["score"])

    def test_doctor_match_workflow_writes_output_and_care_team_item(self):
        with tempfile.TemporaryDirectory() as workspace_dir:
            workflow = DoctorMatchWorkflow(
                workspace_root=workspace_dir,
                memory_dir=str(Path(workspace_dir) / "memory" / "health"),
                fit_finder=fake_fit_finder(),
            )
            result = workflow.match_doctors(
                patient_profile=PATIENT_PROFILE,
                doctors=DOCTOR_CANDIDATES,
                pubmed_mode="auto",
            )
            self.assertTrue(Path(result["output_path"]).exists())
            self.assertTrue((Path(workspace_dir) / "memory" / "health" / "items" / "care-team.md").exists())
            self.assertGreaterEqual(result["follow_up_task_count"], 1)

    def test_chief_dispatches_doctor_match_to_records_research_and_metrics(self):
        with tempfile.TemporaryDirectory() as workspace_dir:
            orchestrator = HealthTeamOrchestrator(
                workspace_root=workspace_dir,
                memory_dir=str(Path(workspace_dir) / "memory" / "health"),
            )
            orchestrator.doctor_match = DoctorMatchWorkflow(
                workspace_root=workspace_dir,
                memory_dir=str(Path(workspace_dir) / "memory" / "health"),
                fit_finder=fake_fit_finder(),
            )
            result = orchestrator.dispatch_flagship_scenario(
                "doctor-fit-finder",
                payload={
                    "patient_profile": PATIENT_PROFILE,
                    "doctors": DOCTOR_CANDIDATES,
                    "top_n": 3,
                    "pubmed_mode": "auto",
                },
            )
            self.assertEqual(
                result["routed_roles"],
                ["health-records", "health-research", "health-metrics"],
            )
            self.assertTrue(Path(result["team_board_path"]).exists())
            self.assertIn("health-research", result["role_brief_paths"])


if __name__ == "__main__":
    unittest.main()
